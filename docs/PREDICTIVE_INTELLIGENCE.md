# Mercados y pronósticos — implementación y evidencia

Actualización verificada el 12 de noviembre de 2026. Se amplió la aplicación
existente; no se sustituyeron Flask, Jinja, SQLite, CSS, SVG ni autenticación.

## Implementado

- Adaptador independiente Twelve Data por REST: históricos diarios y quotes con
  timestamps del proveedor, precios Decimal y procedencia explícita. Se consultan
  EUR/USD, USD/JPY, XAU/USD y dos índices registrados por separado. No se mezclan
  fuentes ni se identifica USDT como USD.
- Worker de polling independiente, cuotas persistentes de 6/min y 600/24 h,
  checkpoints, deduplicación, cierre conservador UTC, estados por instrumento y
  recuperación. Los rechazos permanentes se reintentan después de 24 horas;
  red/cuota después de 60 s. Las cuotas locales no conocen uso externo de la clave.
- Quotes consultados cada 900 s, etiquetados DELAYED con retraso contractual no
  verificado. Se vuelven STALE si el evento o la recepción tienen más de 1800 s.
  No se anuncia streaming de Twelve Data ni un estado LIVE para ese adaptador.
- Persistencia, autorregresión ridge y XGBoost CPU para retorno del próximo cierre
  observado. Entrenamiento separado de Flask, mínimo 120 cierres, revisión cada
  30 minutos y hash del conjunto para evitar entrenamientos repetidos.
- SMA20, EMA20, RSI14 con medias simples, MACD sin señal, bandas de Bollinger20,
  último log-retorno y volatilidad diaria de log-retornos20. No se anualiza con
  un calendario uniforme entre mercados.
- Página `/intelligence`, APIs `/api/v1/predictions/<symbol>` y
  `/api/v1/analysis/<symbol>`, comparación de modelos, incertidumbre, fechas,
  calidad, indicadores y explicación de contribuciones en es/en/zh-Hans.
- Seis servicios systemd supervisados, habilitados, con `Linger=yes`: web, Binance,
  diario, Twelve Data, modelos y túnel. La aplicación arranca al encender la laptop
  y no depende de mantener VS Code abierto. La suspensión/apagado corta el servicio.

## Archivos principales

| Área | Nuevos y modificados |
| --- | --- |
| Fuentes y polling | [Adaptador](../market_explained/providers/twelve_data.py), [worker](../market_explained/ingestion/twelve_worker.py), registro de capacidades y [persistencia](../market_explained/storage/repository.py) |
| Modelos | [Forecasting](../market_explained/intelligence/forecasting.py), [series/registro](../market_explained/intelligence/data.py), [worker](../market_explained/intelligence/worker.py), [dependencias opcionales](../requirements-ml.txt) |
| API y acceso | [Rutas](../market_explained/api/routes.py), [autorización de visualización](../market_explained/security/display.py) |
| UI | [Página predictiva](../templates/intelligence.html), navegación/detalle/explorador existentes, catálogos de idiomas y CSS existente |
| SQLite | [Migración 002](../market_explained/storage/migrations/002_twelve_data.sql), [003](../market_explained/storage/migrations/003_verified_index.sql) |
| Operación y validación | [Servicios](../scripts/demo_services.py), [CI](../.github/workflows/ci.yml), [nuevos tests](../tests/test_twelve_forecasting.py), [fixtures](../tests/fixtures/README.md), actualizaciones de tests de contratos/migración |

No se modificó `tests/test_app.py`. El cambio previo del usuario en `.env.example`
se dejó intacto y fuera de estos commits.

## Metodología y límites

Se usan únicamente cierres completos de una fuente específica por instrumento.
Los stocks conservan la atribución histórica de su proveedor actual y una fecha de
sesión con cutoff UTC conservador, que no es la hora exacta de cierre de bolsa.
Los candles conservan su ventana y recepción. Revisiones del proveedor se guardan
como observaciones diferentes; la serie de entrenamiento usa la revisión más reciente.
El conjunto no es un archivo histórico point-in-time de lo conocido en cada fecha.
No se han resuelto los ajustes corporativos, sesgo de supervivencia ni regímenes.

Para cada fila solo se calculan características con precios conocidos hasta su
corte: dos retornos rezagados, medias de retornos de 5/20 sesiones, volatilidad20 y
distancia a SMA20. El objetivo es el retorno simple del próximo cierre observado,
no un precio garantizado ni necesariamente un plazo exacto de 24 horas. El precio
estimado se deriva del precio de referencia con aritmética Decimal; los modelos
usan arrays float para entrenamiento numérico.

Se distribuyen cronológicamente aproximadamente 60% entrenamiento, 20% calibración
y 20% prueba. Calibración y prueba usan reentrenamiento con ventanas crecientes,
utilizando solo objetivos disponibles antes de cada origen. La selección usa MAE
de calibración, nunca el segmento de prueba. Después de evaluar, se ajusta el modelo
seleccionado a todos los objetivos conocidos y se predice desde el último cierre.
No hay optimización usando el resultado de la prueba.

El intervalo empírico nominal 80% usa un cuantil finito de residuos absolutos de
calibración del modelo seleccionado. **No garantiza cobertura futura**: las series
son dependientes y cambian de régimen. La cobertura real de la prueba se muestra
junto al nivel nominal. Los modelos no tienen validación independiente.

XGBoost usa 40 árboles, profundidad 2, eta 0.05, regularización y semilla fija,
sin GPU. Sus contribuciones se obtienen con TreeSHAP integrado (`pred_contribs`);
ridge informa contribuciones de características estandarizadas. Describen el
cálculo del modelo y no prueban causas económicas. Persistencia estima retorno cero.
La documentación de librerías y artefacto JSON del modelo seleccionado se guardan
en el registro privado de modelos; la API no entrega el artefacto del booster.

No hay órdenes, brokers ni promesas de retorno. DeepSeek sigue siendo opcional y
no interviene en ingesta, entrenamiento, selección, intervalos o explicación numérica.

## Evidencia real de esta instalación

- Twelve Data: **1095 velas cerradas y 3 quotes**, distribuidas entre EUR/USD,
  USD/JPY y XAU/USD, normalizadas y persistidas. No se sembraron fixtures de pruebas.
- SPX devolvió HTTP 404. Se consultó el catálogo oficial `/indices`, que confirmó
  FTSE con moneda GBP y venue LSE; su consulta también devolvió HTTP 404. Ambos
  permanecen UNAVAILABLE, sin sustituirlos por un ETF ni por precios sintéticos.
  El código HTTP no demuestra por sí solo si la causa es plan, cobertura o símbolo.
- **17 pronósticos persistidos**: 12 acciones, 2 pares cripto, 2 pares forex y oro.
  Selección por calibración: 13 persistencia y 4 XGBoost. Ridge se entrenó y evaluó
  como candidato; no fue elegido. Persistencia es una referencia legítima y visible.
- Ejemplo MSFT: MAE posterior de persistencia 0.01684, ridge 0.01852 y XGBoost
  0.01795; cobertura observada del intervalo seleccionado **50%** en 22 observaciones.
  NVDA: cobertura **36.36%** en 22 observaciones. Esto **no acredita precisión
  predictiva**: los modelos seleccionados pueden empeorar frente al baseline fuera
  de calibración. La interfaz muestra los resultados sin cambiar el modelo usando
  esa prueba ni esconder la cobertura baja.
- Filas existentes antes/después de migrar y generar modelos: 1 cuenta, 2 entradas
  de watchlist, 2 mensajes y 1544 precios diarios, conservados. Se ejecutó la prueba
  de migración con cuentas, listas, mensajes, noticias y precios de un esquema antiguo.
- Seis servicios activos y habilitados; `Linger=yes`. Terminación controlada del
  proceso web: systemd creó un PID nuevo y `/health` volvió a HTTP 200. No se hizo
  un reinicio físico del equipo ni una aceptación continua de 24 h.
- HTTPS público: `/api/v1/predictions/MSFT` devolvió 200 con XGBoost real;
  `/api/v1/market/EURUSD` devolvió UNAVAILABLE y `observation=null` por la restricción
  de visualización externa. Los endpoints de historia/análisis/predicción de ese
  proveedor responden 403 para visitantes externos.

Las cantidades son la captura de validación, no métricas continuas. Binance sigue
recibiendo eventos y la base puede crecer después de este informe.

## Validación ejecutada

- Lanzador documentado `./run.sh` ejecutado en un puerto y SQLite temporales: `/health` HTTP 200.
- **63 pruebas unittest, OK**, incluyendo los 19 tests originales sin cambios,
  migración/preservación, contratos anteriores y diez nuevas pruebas offline.
- Los nuevos tests comprueban el fixture real de Twelve Data, rechazo de velas del
  día abierto, timestamps/Decimal, deduplicación, revisiones, cuotas, reintentos,
  credenciales ausentes, errores sin secretos, límites de visualización pública,
  features causales, walk-forward y persistencia/lectura de pronósticos.
- XGBoost CPU instalado y ejecutado en esta laptop Linux amd64/Python 3.12. Los tests
  ML se omiten explícitamente cuando no están instaladas sus dependencias; un job CI
  separado las instala. CI remoto y la ejecución ML en ARM64 no se han verificado.
- Ruff y mypy (22 archivos seleccionados) sin errores. Bandit sin hallazgos medios
  o altos; `pip-audit` del runtime y dependencias ML sin vulnerabilidades conocidas.
- Chromium por HTTPS: página predictiva en español e inglés de escritorio y chino
  móvil (390 px), tablas desplazables, precios redondeados para presentación,
  sin desbordamiento horizontal de página y sin mensajes de consola.

Los fixtures reales se guardan solo para pruebas offline. Las series generadas por
el test de modelos se crean en memoria para comprobar causalidad y persistencia;
no se cargan en los workers o la base de producción.

## Migraciones y seguridad

`002_twelve_data.sql` añade instrumentos/provider_symbols, estados por instrumento
con reintentos e índice de predicciones. `003_verified_index.sql` añade FTSE conforme
al catálogo oficial. Se conserva SPX y no se borra ningún histórico. Cada ejecución
con migraciones pendientes crea backup SQLite privado 0600 antes de la transacción.
Restauración y almacenamiento: [DATA_OPERATIONS.md](DATA_OPERATIONS.md).

No se escribieron credenciales en Git. La nueva clave está únicamente en el entorno
privado del servicio, modo 0600; errores y logs usan códigos controlados. Puesto que
fue compartida en conversación, se recomienda rotarla y sustituirla privadamente.
Las exposiciones anteriores continúan documentadas en [SECURITY.md](../SECURITY.md).

`TWELVE_DATA_PUBLIC_DISPLAY=0` por defecto. La clave no demuestra un derecho de
redistribución: el acceso público a precios, históricos y derivados de Twelve Data
se bloquea hasta confirmar autorización. El acceso interno directo por loopback,
sin cabeceras de proxy, permite inspección. Los datos no se envían en el contexto
público del asistente. Otros proveedores conservan sus propias condiciones.

## Ejecución y siguiente paso

[README](../README.md) contiene los comandos locales y
[LAPTOP_DEMO.md](LAPTOP_DEMO.md) los servicios y la configuración privada.
El servidor completo conserva SQLite y workers; Cloudflare Workers requeriría
migrar persistencia y ejecución. Cloudflare Tunnel publica el servidor de la laptop,
no lo convierte en alojamiento cloud. El enlace Quick Tunnel puede cambiar.

Siguiente fase: confirmar derechos de visualización y cobertura/plan de índices,
validar cuotas durante 24 h, establecer URL estable si se dispone de dominio,
mejorar archivos point-in-time/calendarios/ajustes y evaluar fuera de muestra con
más datos. ATR, señal MACD, volumen/correlaciones entre mercados, modelos neuronales,
Alpaca/FRED, WebSocket al navegador y despliegue externo permanente siguen pendientes.
No se ha demostrado una ventaja predictiva; ampliar modelos debe depender de esa
validación, no de añadir complejidad.

## Referencias primarias

- [SDK oficial Twelve Data](https://github.com/twelvedata/twelvedata-python).
  El adaptador implementa directamente el contrato REST sin requerir el SDK.
- [Time series](https://twelvedata.com/docs/market-data/time-series),
  [cuotas](https://support.twelvedata.com/en/articles/5615854-credits),
  [planes](https://twelvedata.com/pricing),
  [uso y redistribución](https://support.twelvedata.com/en/articles/5332349-commercial-and-personal-usage),
  [atribución](https://support.twelvedata.com/en/articles/12647398-attribution-guidelines-for-using-twelve-data).
- [Python en Cloudflare Workers](https://developers.cloudflare.com/workers/languages/python/).
- [XGBoost CPU](https://xgboost.readthedocs.io/en/stable/install.html).
