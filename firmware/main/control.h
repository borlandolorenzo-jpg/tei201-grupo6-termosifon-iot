/*
 * control.h — Controlador diferencial con histéresis para la válvula anti-flujo-inverso.
 *
 * Lógica pura en C++ (sin dependencias de Arduino) para poder probarla en un PC
 * con testing/unit/test_control.cpp antes de cargarla al ESP32.
 *
 * Idea física:
 *   - De día el colector está más caliente que el tanque (T_col > T_tanque):
 *     la válvula se ABRE y el termosifón circula con normalidad.
 *   - De noche el colector se enfría y el tanque queda más caliente:
 *     sin válvula aparece flujo inverso (el tanque pierde calor por el colector).
 *     La válvula se CIERRA para cortar esa circulación.
 *
 * Reglas (histéresis sobre ΔT = T_col - T_tanque):
 *   - Cerrada -> abre si ΔT >= dtOn
 *   - Abierta -> cierra si ΔT <= dtOff
 *   - Entre dtOff y dtOn se mantiene el estado (banda muerta).
 *
 * Seguridad:
 *   - Falla de sensor (col o tanque) durante >= maxFailures ciclos seguidos:
 *     modo FALLA -> válvula ABIERTA ("fail-open"). El sistema vuelve a comportarse
 *     como un termosifón sin válvula (pierde eficiencia de noche, pero no se bloquea
 *     la circulación ni se sobrecalienta el colector).
 *   - Sobretemperatura del tanque (plástico rígido): cierra la válvula al llegar a
 *     tankMax y la reabre al bajar de tankResume.
 *   - Tiempo mínimo entre movimientos (minDwellMs) para proteger el servo.
 *     Los cambios de seguridad (falla, sobretemperatura) ignoran ese tiempo.
 */
#pragma once
#include <stdint.h>

struct ControlParams {
  float dtOn = 5.0f;           // [K]  abrir cuando T_col - T_tanque >= dtOn
  float dtOff = 2.0f;          // [K]  cerrar cuando T_col - T_tanque <= dtOff
  float tankMax = 65.0f;       // [°C] cerrar por sobretemperatura (definir según el material del tanque)
  float tankResume = 60.0f;    // [°C] volver a operación normal
  uint32_t minDwellMs = 60000; // [ms] tiempo mínimo entre movimientos de la válvula
  uint8_t maxFailures = 3;     // ciclos consecutivos con sensor inválido para declarar FALLA
};

class DiffController {
 public:
  explicit DiffController(const ControlParams& p) : p_(p) {}

  // Actualiza el estado. Retorna true si la válvula debe quedar ABIERTA.
  // nowMs: tiempo monotónico en milisegundos (millis()).
  bool update(float tCol, bool okCol, float tTank, bool okTank, uint32_t nowMs) {
    if (!okCol || !okTank) {
      if (failCount_ < 255) failCount_++;
    } else {
      failCount_ = 0;
    }
    fault_ = (failCount_ >= p_.maxFailures);

    bool desired = open_;
    bool safety = false;  // el cambio es de seguridad (ignora el tiempo mínimo)

    if (fault_) {
      desired = true;  // fail-open
      safety = true;
    } else if (failCount_ > 0) {
      desired = open_;  // lectura inválida transitoria: mantener estado
    } else {
      if (!overTemp_ && tTank >= p_.tankMax) overTemp_ = true;
      else if (overTemp_ && tTank <= p_.tankResume) overTemp_ = false;

      if (overTemp_) {
        desired = false;
        safety = true;
      } else {
        const float dt = tCol - tTank;
        if (!open_ && dt >= p_.dtOn) desired = true;
        else if (open_ && dt <= p_.dtOff) desired = false;
      }
    }

    if (desired != open_) {
      const bool dwellOk = !everChanged_ || (uint32_t)(nowMs - lastChangeMs_) >= p_.minDwellMs;
      if (safety || dwellOk) {
        if (open_ && !desired) closures_++;
        open_ = desired;
        lastChangeMs_ = nowMs;
        everChanged_ = true;
      }
    }
    return open_;
  }

  bool isOpen() const { return open_; }
  bool inFault() const { return fault_; }
  bool overTemp() const { return overTemp_; }
  uint32_t closures() const { return closures_; }
  const ControlParams& params() const { return p_; }

 private:
  ControlParams p_;
  bool open_ = true;  // al arrancar: abierta (comportamiento de termosifón sin válvula)
  bool fault_ = false;
  bool overTemp_ = false;
  bool everChanged_ = false;
  uint8_t failCount_ = 0;
  uint32_t lastChangeMs_ = 0;
  uint32_t closures_ = 0;
};
