# testing/datos — datos experimentales

Aquí van los archivos CSV de cada prueba del [protocolo](../protocolo_pruebas.md). **Solo datos reales**: no se suben datos simulados.

| Archivo | Prueba | Cómo se obtiene |
|---|---|---|
| `P1_calibracion_AAAAMMDD.csv` | P1 – sondas vs. referencia | Llenar `plantilla_P1_calibracion.csv`: una fila por muestra (30 por sonda y punto) |
| `P2_registro_AAAAMMDD.csv` | P2 – lógica de control | Dashboard → Exportar CSV (periodo "Última hora") |
| `P3_registro_AAAAMMDD.csv` | P3 – conectividad | Dashboard → Exportar CSV |
| `P5_A_noche1.csv` … `P5_B_noche3.csv` | P5 – ensayo nocturno A/B | Dashboard → Exportar CSV, 12 h por noche |
| `P6_registro_AAAAMMDD.csv` | P6 – desempeño diurno | Dashboard → Exportar CSV (24 h) |

Formato de los registros del dashboard: `ts_epoch,ts_iso_utc,t_col_c,t_tank_c,t_amb_c,valvula_abierta,falla,rssi_dbm,cierres`.

Las fotos, capturas del dashboard y videos de cada ensayo van en `../evidencia/` con el mismo prefijo (`P2_...`).
