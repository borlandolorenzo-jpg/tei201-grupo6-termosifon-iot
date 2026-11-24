/*
 * TEI201 · Grupo 6 — Colector solar termosifón con válvula anti-flujo-inverso (IoT)
 * Plataforma: ESP32 DevKit (38 pines) · Arduino core for ESP32
 *
 * Qué hace:
 *   1. Lee 2 sondas DS18B20 en un bus 1-Wire (GPIO33): colector (T_col) y tanque (T_tank).
 *      La sonda de ambiente (T_amb) es opcional: HAS_AMBIENT = 1 en config.h.
 *   2. Decide si la válvula (servo SG90) debe estar abierta o cerrada con un controlador
 *      diferencial con histéresis (control.h).
 *   3. Guarda cada muestra en Firebase Realtime Database (histórico + estado actual) vía REST.
 *      Si no hay WiFi, acumula hasta 180 muestras en RAM (30 min) y las envía al reconectar.
 *   4. Mueve el servo en GPIO13. Señaliza con 2 LED: verde = válvula abierta, rojo = falla de sensor o sin WiFi.
 *
 * Flujo: sensor -> procesamiento (control.h) -> actuador (servo) -> conectividad (Firebase) -> dashboard.
 * Ver FUENTES.md para librerías y ayuda de IA declaradas.
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ESP32Servo.h>
#include <time.h>

#include "config.h"   // copiar desde config.h.example

// 1 = hay sonda de ambiente (3 sondas); 0 = solo colector y tanque (2 sondas).
// Si config.h no lo define, se asume 0 (prototipo con 2 sondas).
#ifndef HAS_AMBIENT
#define HAS_AMBIENT 0
#endif
#include "control.h"

// ===================== Objetos globales =====================
OneWire oneWire(PIN_ONEWIRE);
DallasTemperature sensors(&oneWire);
Servo valveServo;
ControlParams ctrlParams;               // valores por defecto en control.h
DiffController controller(ctrlParams);

DeviceAddress addrCol = ADDR_COL;
DeviceAddress addrTank = ADDR_TANK;
#if HAS_AMBIENT
DeviceAddress addrAmb = ADDR_AMB;
#else
DeviceAddress addrAmb = {0,0,0,0,0,0,0,0};   // sin sonda de ambiente
#endif

// ===================== Cola de muestras (RAM) =====================
struct Sample {
  uint32_t ts;      // epoch [s] (0 = sin hora válida)
  float tc, tt, ta; // temperaturas [°C]; NAN si la lectura es inválida
  uint8_t valve;    // 1 = abierta, 0 = cerrada
  uint8_t fault;    // bits: 1 = colector, 2 = tanque, 4 = ambiente
  int8_t rssi;      // intensidad WiFi [dBm]
  uint16_t closures;
};
const int QUEUE_SIZE = 180;
Sample queueBuf[QUEUE_SIZE];
int qHead = 0, qCount = 0;

void queuePush(const Sample& s) {
  if (qCount == QUEUE_SIZE) {         // cola llena: descartar la más antigua
    qHead = (qHead + 1) % QUEUE_SIZE;
    qCount--;
  }
  queueBuf[(qHead + qCount) % QUEUE_SIZE] = s;
  qCount++;
}
void queuePop() {
  if (qCount > 0) { qHead = (qHead + 1) % QUEUE_SIZE; qCount--; }
}

// ===================== Estado del ciclo de medición =====================
enum Phase { IDLE, CONVERTING };
Phase phase = IDLE;
unsigned long tPhase = 0;       // inicio de la fase actual
unsigned long tLastCycle = 0;
float prevValid[3] = {NAN, NAN, NAN};
bool useAddresses = false;
bool timeSynced = false;
unsigned long lastWifiTry = 0;
unsigned long lastUploadTry = 0;
unsigned long lastBlink = 0;

// ===================== Utilidades =====================
bool addrIsSet(const DeviceAddress a) { return a[0] != 0; }

// Valida una lectura del DS18B20.
//  -127 = sensor desconectado; 85.0 = valor de arranque (sin conversión); fuera de rango físico.
bool validReading(float t, int idx) {
  if (t == DEVICE_DISCONNECTED_C) return false;
  if (t < -55.0f || t > 125.0f) return false;
  if (t == 85.0f && (isnan(prevValid[idx]) || prevValid[idx] < 80.0f)) return false;
  return true;
}

float readSensor(int idx, const DeviceAddress addr) {
  float t = useAddresses ? sensors.getTempC(addr) : sensors.getTempCByIndex(idx);
  if (validReading(t, idx)) { prevValid[idx] = t; return t; }
  return NAN;
}

void moveValve(bool open) {
  valveServo.write(open ? SERVO_OPEN_DEG : SERVO_CLOSED_DEG);
}

void connectWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  if (millis() - lastWifiTry < 10000UL && lastWifiTry != 0) return;
  lastWifiTry = millis();
  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.println("[wifi] intentando conectar...");
}

void syncTime() {
  if (timeSynced || WiFi.status() != WL_CONNECTED) return;
  configTime(0, 0, "pool.ntp.org", "time.google.com");   // UTC; el dashboard convierte a hora local
  if (time(nullptr) > 1700000000) {
    timeSynced = true;
    Serial.println("[ntp] hora sincronizada");
  }
}

// ===================== Firebase (REST) =====================
String fbUrl(const char* path) {
  String u = String(FIREBASE_URL) + path + ".json";
  if (strlen(FIREBASE_AUTH) > 0) u += "?auth=" + String(FIREBASE_AUTH);
  return u;
}

String jsonNum(float v) { return isnan(v) ? String("null") : String(v, 2); }

String sampleToJson(const Sample& s) {
  String j = "{";
  j += "\"ts\":" + String(s.ts);
  j += ",\"tc\":" + jsonNum(s.tc);
  j += ",\"tt\":" + jsonNum(s.tt);
  j += ",\"ta\":" + jsonNum(s.ta);
  j += ",\"v\":" + String(s.valve);
  j += ",\"f\":" + String(s.fault);
  j += ",\"rssi\":" + String(s.rssi);
  j += ",\"cl\":" + String(s.closures);
  j += "}";
  return j;
}

// Envía una petición HTTPS. method: "POST" (agrega al histórico) o "PUT" (reemplaza el estado).
bool firebaseSend(const char* path, const char* method, const String& body) {
  WiFiClientSecure client;
  client.setInsecure();   // prototipo: no se valida el certificado (ver limitaciones en README)
  HTTPClient http;
  http.setTimeout(6000);
  if (!http.begin(client, fbUrl(path))) return false;
  http.addHeader("Content-Type", "application/json");
  int code = (strcmp(method, "PUT") == 0) ? http.PUT(body) : http.POST(body);
  http.end();
  if (code != 200) Serial.printf("[fb] %s %s -> HTTP %d\n", method, path, code);
  return code == 200;
}

// Intenta enviar la muestra más antigua de la cola.
void uploadOne() {
  if (qCount == 0 || WiFi.status() != WL_CONNECTED) return;
  if (millis() - lastUploadTry < 300UL) return;
  lastUploadTry = millis();

  const Sample& s = queueBuf[qHead];
  if (s.ts == 0) { queuePop(); return; }        // muestra sin hora válida: no se sube
  String body = sampleToJson(s);
  if (firebaseSend("/lecturas", "POST", body)) {
    if (qCount == 1) firebaseSend("/estado", "PUT", body);   // estado actual = última muestra subida
    queuePop();
  }
}

// ===================== Ciclo de medición y control =====================
void finishCycle() {
  float tc = readSensor(0, addrCol);
  float tt = readSensor(1, addrTank);
  float ta = HAS_AMBIENT ? readSensor(2, addrAmb) : NAN;   // NAN = no hay sonda
  bool okC = !isnan(tc), okT = !isnan(tt);

  bool open = controller.update(okC ? tc : 0, okC, okT ? tt : 0, okT, millis());
  if (!CONTROL_ENABLED) open = true;   // ensayo B (sin válvula): fuerza abierta, el controlador igual registra
  moveValve(open);

  Sample s;
  s.ts = timeSynced ? (uint32_t)time(nullptr) : 0;
  s.tc = tc; s.tt = tt; s.ta = ta;
  s.valve = open ? 1 : 0;
  s.fault = (okC ? 0 : 1) | (okT ? 0 : 2) | ((HAS_AMBIENT && isnan(ta)) ? 4 : 0);
  s.rssi = (WiFi.status() == WL_CONNECTED) ? WiFi.RSSI() : 0;
  s.closures = (uint16_t)controller.closures();
  queuePush(s);

  Serial.printf("T_col=%.2f  T_tank=%.2f  T_amb=%.2f  dT=%.2f  valvula=%s%s%s  cola=%d\n",
                tc, tt, ta, (okC && okT) ? tc - tt : NAN,
                open ? "ABIERTA" : "CERRADA",
                controller.inFault() ? " [FALLA]" : "",
                controller.overTemp() ? " [SOBRETEMP]" : "", qCount);
}

void updateLeds() {
  digitalWrite(PIN_LED_OK, controller.isOpen() ? HIGH : LOW);
  bool problem = controller.inFault() || WiFi.status() != WL_CONNECTED;
  if (problem) {                                   // rojo parpadea cada 500 ms
    if (millis() - lastBlink > 500) {
      lastBlink = millis();
      digitalWrite(PIN_LED_FAIL, !digitalRead(PIN_LED_FAIL));
    }
  } else {
    digitalWrite(PIN_LED_FAIL, LOW);
  }
}

// ===================== setup / loop =====================
void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("\n== TEI201 Grupo 6 · termosifon IoT ==");

  pinMode(PIN_LED_OK, OUTPUT);
  pinMode(PIN_LED_FAIL, OUTPUT);

  valveServo.setPeriodHertz(50);
  valveServo.attach(PIN_SERVO, SERVO_MIN_US, SERVO_MAX_US);
  moveValve(true);                                 // arranque: válvula abierta

  sensors.begin();
  sensors.setResolution(12);                       // 0.0625 °C, conversión ~750 ms
  sensors.setWaitForConversion(false);             // no bloquear mientras convierte
  useAddresses = addrIsSet(addrCol) && addrIsSet(addrTank) && (!HAS_AMBIENT || addrIsSet(addrAmb));
  Serial.printf("[ds18b20] sondas en el bus: %d · direcciones fijas: %s\n",
                sensors.getDeviceCount(), useAddresses ? "si" : "NO (usando orden del bus)");

  WiFi.mode(WIFI_STA);
  connectWifi();
}

void loop() {
  connectWifi();
  syncTime();
  updateLeds();

  unsigned long now = millis();
  if (phase == IDLE && (now - tLastCycle >= SAMPLE_MS || tLastCycle == 0)) {
    sensors.requestTemperatures();                 // inicia conversión (no bloquea)
    tPhase = now;
    tLastCycle = now;
    phase = CONVERTING;
  } else if (phase == CONVERTING && now - tPhase >= 800) {   // 12 bits tarda <= 750 ms
    finishCycle();
    phase = IDLE;
  }

  uploadOne();
}
