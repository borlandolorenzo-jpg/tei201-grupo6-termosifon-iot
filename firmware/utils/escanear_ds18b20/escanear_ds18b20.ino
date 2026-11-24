/*
 * escanear_ds18b20.ino — utilidad para obtener la dirección ROM de cada DS18B20.
 *
 * Uso:
 *   1. Conectar UNA sonda a la vez (o las tres y mirar el orden) al pin 4 con pull-up de 4.7 kΩ.
 *   2. Abrir el Monitor Serie a 115200 baudios.
 *   3. Copiar cada dirección a ADDR_COL / ADDR_TANK / ADDR_AMB en firmware/main/config.h
 *      y etiquetar físicamente cada sonda (cinta con "COL", "TANQUE", "AMB").
 */
#include <OneWire.h>
#include <DallasTemperature.h>

#define PIN_ONEWIRE 33   // mismo pin que la perfboard final
OneWire oneWire(PIN_ONEWIRE);
DallasTemperature sensors(&oneWire);

void setup() {
  Serial.begin(115200);
  delay(500);
  sensors.begin();
  int n = sensors.getDeviceCount();
  Serial.printf("Sondas encontradas: %d\n", n);
  for (int i = 0; i < n; i++) {
    DeviceAddress a;
    if (sensors.getAddress(a, i)) {
      Serial.printf("Sonda %d: {", i);
      for (int k = 0; k < 8; k++) Serial.printf("0x%02X%s", a[k], k < 7 ? "," : "");
      Serial.println("}");
    }
  }
}

void loop() {
  sensors.requestTemperatures();
  for (int i = 0; i < sensors.getDeviceCount(); i++) {
    Serial.printf("Sonda %d: %.2f °C   ", i, sensors.getTempCByIndex(i));
  }
  Serial.println();
  delay(2000);
}
