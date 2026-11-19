// config.js — editar con los datos del proyecto Firebase del grupo.
// Estos valores se pueden cambiar también desde el botón "Configuración" del dashboard.
window.DASH_CONFIG = {
  FIREBASE_URL: 'https://TU-PROYECTO-default-rtdb.firebaseio.com', // sin "/" final
  FIREBASE_AUTH: '',        // opcional (solo si las reglas lo exigen)
  TANK_LITERS: 20,          // volumen del tanque [L] — AJUSTAR al valor real
  HOT_TARGET_C: 45,         // temperatura objetivo de agua caliente [°C] (definida en el Avance 1)
  TANK_MAX_C: 65,           // límite de sobretemperatura (igual que control.h)
  DT_ON: 5,                 // umbral de apertura [K] (igual que control.h)
  DT_OFF: 2,                // umbral de cierre [K]
  REFRESH_S: 10             // frecuencia de actualización
};
