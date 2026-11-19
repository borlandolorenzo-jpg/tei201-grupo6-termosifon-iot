// Pruebas unitarias del controlador (se ejecutan en el PC, sin hardware).
// Compilar y correr:   g++ -std=c++17 -Wall -o test_control test_control.cpp && ./test_control
#include <cstdio>
#include "../../firmware/main/control.h"

static int fails = 0;
#define CHECK(cond, msg)                                         \
  do {                                                           \
    if (!(cond)) { std::printf("  FALLA: %s\n", msg); fails++; } \
    else { std::printf("  ok:    %s\n", msg); }                  \
  } while (0)

int main() {
  ControlParams p;  // valores por defecto: dtOn=5, dtOff=2, dwell=60 s
  std::printf("[T1] Arranque y apertura con sol\n");
  {
    DiffController c(p);
    CHECK(c.isOpen(), "arranca abierta (comportamiento sin válvula)");
    c.update(30, true, 28, true, 1000);  // dT = 2 -> cierra (primer cambio sin espera)
    CHECK(!c.isOpen(), "dT=2 K al arrancar -> cierra");
    c.update(40, true, 30, true, 100000);  // dT = 10 >= 5, pasaron >60 s
    CHECK(c.isOpen(), "dT=10 K -> abre");
  }
  std::printf("[T2] Histéresis: sin conmutación dentro de la banda muerta\n");
  {
    DiffController c(p);
    c.update(45, true, 30, true, 0);  // abierta
    int changes = 0;
    bool prev = c.isOpen();
    // dT oscila entre 2.5 y 4.5 K (dentro de la banda 2..5) con ruido
    for (int i = 0; i < 200; i++) {
      float dt = 3.5f + ((i % 2) ? 1.0f : -1.0f);
      c.update(30 + dt, true, 30, true, 100000 + i * 10000);
      if (c.isOpen() != prev) { changes++; prev = c.isOpen(); }
    }
    CHECK(changes == 0, "200 muestras con dT en [2.5, 4.5] K -> 0 conmutaciones");
  }
  std::printf("[T3] Umbrales exactos\n");
  {
    DiffController c(p);
    c.update(30, true, 28, true, 0);  // dT=2 -> cierra
    CHECK(!c.isOpen(), "dT=2.0 -> cerrada");
    c.update(34.9f, true, 30, true, 200000);  // dT=4.9
    CHECK(!c.isOpen(), "dT=4.9 sigue cerrada");
    c.update(35.0f, true, 30, true, 400000);  // dT=5.0
    CHECK(c.isOpen(), "dT=5.0 abre");
    c.update(32.1f, true, 30, true, 600000);  // dT=2.1
    CHECK(c.isOpen(), "dT=2.1 sigue abierta");
    c.update(32.0f, true, 30, true, 800000);  // dT=2.0
    CHECK(!c.isOpen(), "dT=2.0 cierra");
    CHECK(c.closures() == 2, "contador de cierres = 2");
  }
  std::printf("[T4] Tiempo mínimo entre movimientos\n");
  {
    DiffController c(p);
    c.update(30, true, 28, true, 0);          // cierra (primer cambio)
    c.update(50, true, 30, true, 10000);      // dT=20 pero solo pasaron 10 s
    CHECK(!c.isOpen(), "a los 10 s no se mueve (dwell 60 s)");
    c.update(50, true, 30, true, 61000);
    CHECK(c.isOpen(), "a los 61 s sí abre");
  }
  std::printf("[T5] Falla de sensor -> fail-open\n");
  {
    DiffController c(p);
    c.update(30, true, 28, true, 0);  // cierra
    CHECK(!c.isOpen(), "cerrada antes de la falla");
    c.update(0, false, 28, true, 10000);
    CHECK(!c.isOpen() && !c.inFault(), "1 lectura inválida: mantiene estado, sin falla");
    c.update(0, false, 28, true, 20000);
    c.update(0, false, 28, true, 30000);
    CHECK(c.inFault(), "3 lecturas inválidas seguidas -> FALLA");
    CHECK(c.isOpen(), "en falla la válvula queda abierta (ignora dwell)");
    c.update(31, true, 28, true, 40000);  // sensor vuelve
    CHECK(!c.inFault(), "sensor recuperado -> sale de FALLA");
  }
  std::printf("[T6] Sobretemperatura del tanque\n");
  {
    DiffController c(p);
    c.update(80, true, 64.9f, true, 0);
    CHECK(c.isOpen(), "tanque 64.9 °C: opera normal");
    c.update(80, true, 65.0f, true, 1000);
    CHECK(!c.isOpen() && c.overTemp(), "tanque 65 °C: cierra por sobretemperatura");
    c.update(80, true, 62.0f, true, 200000);
    CHECK(!c.isOpen(), "tanque 62 °C: aún en banda de reanudación, sigue cerrada");
    c.update(80, true, 60.0f, true, 400000);
    CHECK(c.isOpen() && !c.overTemp(), "tanque 60 °C: reanuda operación normal");
  }
  std::printf("[T7] Desborde de millis() (32 bits)\n");
  {
    DiffController c(p);
    c.update(30, true, 28, true, 4294960000u);  // cierra cerca del desborde
    c.update(50, true, 30, true, 70000u);        // ~77 s después (tras el desborde)
    CHECK(c.isOpen(), "el tiempo mínimo se calcula bien tras el desborde");
  }
  std::printf("\n%s (%d fallas)\n", fails ? "RESULTADO: FALLÓ" : "RESULTADO: TODAS LAS PRUEBAS PASARON", fails);
  return fails ? 1 : 0;
}
