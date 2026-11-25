# Colector solar termosifón con válvula anti-flujo-inverso (IoT)

**TEI 201 · Taller de Diseño en Ingeniería · Universidad Adolfo Ibáñez · Grupo 6**
**Integrantes:** Lorenzo Borlando · Cristóbal Fuentes · Micaela Miserda
**Profesor:** Camilo Wilson · **ODS 7:** Energía asequible y no contaminante

**Dashboard en línea:** https://borlandolorenzo-jpg.github.io/tei201-grupo6-termosifon-iot/dashboard/?sim=1 (simulación)

Sistema IoT que mide las temperaturas de un colector solar termosifón, decide cuándo cerrar una válvula para evitar el flujo inverso nocturno, guarda los datos en la nube y los muestra en un dashboard con indicadores y alertas.

## Problema que resuelve (referencia al Avance 1)

En Chile, calentar agua es un gasto importante para los hogares en situación de pobreza energética. Un colector solar de placa plana con circulación pasiva (termosifón) la calienta sin electricidad, pero **de noche el flujo se invierte**: el agua caliente del tanque baja por el colector frío y pierde calor. Se documentan pérdidas de hasta ≈ 40 % de la energía captada en algunos sistemas.

**Solución:** una válvula que se cierra cuando el colector está más frío que el tanque y se abre cuando hay sol, gobernada por un controlador electrónico diferencial. El dispositivo mide, decide, actúa y registra los datos para demostrar con evidencia cuánto calor se conserva.

> **Nota de alcance:** por costo, la válvula solenoide de 12 V se reemplazó por un **servo SG90 que simula la válvula**. Con él se demuestran la medición, la lógica de control, la conectividad y el registro de datos.

## Arquitectura

```
 DS18B20 ×2 ──► ESP32 ──► decisión (control.h) ──► servo SG90 (válvula)
 (colector y     │
  tanque; ambi-   ├──► LED (estado) 
  ente opcional)  └──► WiFi ──► Firebase Realtime DB ──► Dashboard web
```

Más detalle en [`docs/arquitectura.md`](docs/arquitectura.md).

| Subsistema | Componente | Función |
|---|---|---|
| Sensores | 2× DS18B20 sumergibles (+1 opcional de ambiente) | T colector y T tanque; T ambiente si se instala la tercera sonda (`HAS_AMBIENT` en `config.h`) |
| Procesamiento | ESP32 DevKit (38 pines), en perfboard 50 × 70 mm con zócalos | Lectura, control diferencial con histéresis, envío de datos |
| Actuador | Servo SG90 | Abre / cierra (simula la válvula) |
| Conectividad | WiFi + Firebase Realtime Database (REST) | Repositorio persistente |
| Visualización | Dashboard HTML + Chart.js | Gráficos, indicadores y alertas |
| Señalización | 2 LED | Verde: válvula abierta · Rojo: falla o sin WiFi |
| Energía | Fuente 5 V / 2 A | ESP32 y servo (sondas desde 3V3) |

La lista completa de componentes con cantidades y costos está en [`hardware/BOM.xlsx`](hardware/BOM.xlsx).

## Estructura del repositorio

```
├── README.md · FUENTES.md
├── firmware/            README.md (pines y librerías)
│   ├── main/            main.ino · control.h · config.h.example
│   └── utils/           escanear_ds18b20 (direcciones de las sondas)
├── dashboard/           index.html · app.js · analytics.js · config.js · sim_data.js
├── hardware/            esquematico.pdf/.png/.svg · BOM.xlsx/.csv · montaje_perfboard.md · fotos/
├── diseño-3d/           modelo de referencia (STEP/STL) · planos · renders
├── testing/             protocolo_pruebas.pdf/.md · resultados_simulacion.md · simulacion/ · analisis.py · unit/ · datos/ · resultados/
└── docs/                presentacion_final.pdf · Presentacion_Avance3.pptx · arquitectura · guion · checklist · notas de iteración
```

## Instalación y uso

### 1. Firebase (repositorio de datos)
1. Crear un proyecto en <https://console.firebase.google.com> y activar **Realtime Database** (ubicación a elección).
2. En la pestaña **Reglas**, pegar (reglas abiertas para el periodo de ensayos; cerrarlas al terminar):
   ```json
   {
     "rules": {
       "estado":   { ".read": true, ".write": true },
       "lecturas": { ".read": true, ".write": true }
     }
   }
   ```
3. Copiar la URL de la base (`https://<proyecto>-default-rtdb.firebaseio.com`).

### 2. Firmware
1. Instalar **Arduino IDE** con el paquete de placas *esp32* (Espressif) y, en el Gestor de librerías: `OneWire`, `DallasTemperature` y `ESP32Servo`.
2. Copiar `firmware/main/config.h.example` como `firmware/main/config.h` y completar WiFi y URL de Firebase (`config.h` no se sube a GitHub).
3. Conectar las sondas, abrir `firmware/utils/escanear_ds18b20/escanear_ds18b20.ino`, anotar la dirección de cada sonda y pegarlas en `ADDR_COL` y `ADDR_TANK` de `config.h` (`ADDR_AMB` solo si se instala la tercera sonda y `HAS_AMBIENT` = 1).
4. Revisar en `config.h` los pines de la perfboard: `PIN_ONEWIRE 33` (sondas) y `PIN_SERVO 13` (servo).
5. Placa **ESP32 Dev Module**, abrir `firmware/main/main.ino` y cargar. El Monitor Serie (115200) muestra cada ciclo.

### 3. Dashboard
- Editar `dashboard/config.js` con la URL de Firebase, el volumen del tanque y la temperatura objetivo.
- Abrir `dashboard/index.html` en el navegador (doble clic) o publicarlo con GitHub Pages.
- Botones: periodo (1 h a 3 días), **Exportar CSV** y **Configuración**.
- `index.html?sim=1` muestra la **simulación** de los ensayos (`testing/simulacion/simular.py`), rotulada "SIMULACIÓN". Versión en línea: enlace al inicio de este README.
- `index.html?demo=1` muestra datos de demostración solo para ver el diseño.
- Para que el ESP32 envíe datos sin la red de la universidad, conectarlo al **hotspot de un celular** (red de 2.4 GHz; en iPhone activar "Maximizar compatibilidad").

### 4. Conexión del hardware
Ver [`hardware/esquematico.pdf`](hardware/esquematico.pdf) y [`hardware/montaje_perfboard.md`](hardware/montaje_perfboard.md).

## Presentación
- Diapositivas: [`docs/presentacion_final.pdf`](docs/presentacion_final.pdf) (y la versión editable `docs/Presentacion_Avance3.pptx`).
- Guion y reparto: [`docs/guion_presentacion.md`](docs/guion_presentacion.md).

## Pruebas
- **Unitarias (PC, sin hardware):** `g++ -std=c++17 -o test_control testing/unit/test_control.cpp && ./test_control` y `node testing/unit/test_analytics.js`.
- **Protocolo experimental completo:** [`testing/protocolo_pruebas.pdf`](testing/protocolo_pruebas.pdf).
- **Análisis de datos:** `python testing/analisis.py --help`.

## Estado del proyecto

| Elemento | Estado |
|---|---|
| Firmware, dashboard, protocolo, esquemático, BOM | Entregados |
| Gemelo 3D, planos y renders (Fusion 360) | Ver `diseño-3d/` |
| Ensayos P2, P5 y P6 | **Por simulación** (acordado con el profesor): [`testing/resultados_simulacion.md`](testing/resultados_simulacion.md) |
| Dashboard con la simulación | [https://borlandolorenzo-jpg.github.io/tei201-grupo6-termosifon-iot/dashboard/?sim=1](https://borlandolorenzo-jpg.github.io/tei201-grupo6-termosifon-iot/dashboard/?sim=1) (rotulado "SIMULACIÓN") |
| Ensayos con el hardware y registro en Firebase | Procedimiento en el protocolo; el ESP32 se conecta al hotspot de un celular porque la red de la universidad no es compatible |

## Limitaciones conocidas
- Los resultados de los ensayos son **simulados** (modelo térmico en `testing/simulacion/simular.py`, misma lógica que `control.h`), según lo acordado con el profesor, porque el ESP32 no se puede conectar a la red WiFi pública de la universidad.
- El servo simula la válvula: el efecto hidráulico real se verificará en una etapa posterior.
- El firmware no valida el certificado HTTPS de Firebase (`setInsecure()`), aceptable en prototipo.
- Las reglas de Firebase son abiertas durante los ensayos; no usar así en producción.

## Declaración de fuentes e IA
Ver [`FUENTES.md`](FUENTES.md).
