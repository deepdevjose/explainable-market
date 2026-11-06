# Explainable Market

Una plataforma en español para comprender movimientos del mercado a partir de cierres diarios, noticias con fuente y un asistente educativo. Landing pública y aplicación responsive con temas claro y oscuro, inspiradas en la sobriedad de Apple y en los fundamentos de IBM Carbon: tipografía IBM Plex Sans, azul de interacción, escala de espaciado y estados accesibles.

## Ejecutar

```bash
./run.sh
```

Abre **http://127.0.0.1:5050**. El script usa `venv/`, lo crea si hace falta e instala dependencias cuando Flask o Waitress no están disponibles. También puedes preparar el entorno manualmente:

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python app.py
```

Python 3.11 o superior. El servidor HTTP es Waitress, con ocho hilos y depuración desactivada.

## Qué puedes hacer

- Explorar el panorama y detalles de activos sin cuenta.
- Crear una cuenta propia y guardar o quitar activos de una lista persistente.
- Consultar series de cierres de uno, tres y seis meses; descargar CSV con fuente.
- Abrir titulares originales y filtrar por activo o sentimiento.
- Comparar variaciones a una, tres y siete sesiones con ventanas completas.
- Solicitar a DeepSeek la clasificación del tono de hasta ocho titulares desde el detalle de un activo, con sesión iniciada.
- Abrir el asistente flotante desde cualquier pantalla. Tiene contexto del activo, datos y noticias del servidor, y un historial separado por usuario o visitante.
- Borrar el historial local del asistente y consultar la metodología y biblioteca educativa.

## Configurar DeepSeek

La configuración se toma únicamente de variables del proceso. `.env.example` es
una referencia: no se cargan `.env` ni `env (1).txt`. No se admite el alias
DEEPSEEK_KEY. Exporta DEEPSEEK_API_KEY desde tu gestor de secretos o servicio.
Sin clave, los mercados siguen funcionando y el asistente muestra su error de
configuración; no se simulan respuestas del modelo.

```bash
# Mantén este valor estable y privado entre arranques. En producción usa tu gestor de secretos.
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
./run.sh
```

Sin SECRET_KEY, el entorno de desarrollo usa una clave efímera y cierra las sesiones
al reiniciar. APP_ENV=production exige una clave explícita de al menos 32 caracteres
y activa cookies seguras para HTTPS. Las credenciales que entraron en el historial
deben rotarse: consulta [SECURITY.md](SECURITY.md). No reutilices la clave antigua.

Si el servidor ya está abierto, reinícialo después de cambiar la clave. El modelo predeterminado es `deepseek-flash`, configurable mediante `DEEPSEEK_MODEL`. Las llamadas salen únicamente del backend hacia `https://api.deepseek.com/chat/completions`; la clave nunca se incorpora al HTML, JavaScript ni respuestas de la API.

El asistente se limita mediante instrucciones de sistema y una respuesta estructurada validada a explicaciones de la plataforma y educación financiera; no cuenta con herramientas ni ejecuta operaciones. Los límites del modelo no constituyen una garantía contra respuestas incorrectas o intentos de eludir instrucciones. El contexto procede del servidor, no del contenido arbitrario del navegador.

**Estado de la validación inicial, 6 de noviembre de 2026:** el proveedor rechazó la credencial suministrada con HTTP 401. La conexión está implementada; la conversación y el sentimiento en vivo requieren una clave válida. Por decisión del usuario esa configuración queda pendiente. No hay respuestas sustitutivas que aparenten proceder del modelo.

## Datos y actualización

Los datos financieros se guardan en **`data/market-live.db`**. La antigua `data/market.db` se conserva sin importar sus cuentas, titulares ni cotizaciones. No se generan precios ni titulares para la aplicación. El generador anterior fue retirado.

- Precios: series públicas diarias de Yahoo Finance; ante fallos, Nasdaq. La validación en este entorno obtuvo los cierres mediante Nasdaq.
- Noticias: RSS por activo de Yahoo Finance, con enlace y fecha UTC. Los artículos originales pueden estar en inglés.
- Catálogo inicial: AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, AMD, JPM, V, XOM y SPY.
- El panorama consulta su lista en segundo plano al entrar si pasaron 15 minutos desde el último intento. La actualización manual tiene un mínimo de 90 segundos entre intentos por activo.
- La serie de Yahoo excluye el día actual de Nueva York para evitar mostrar una vela intradía como cierre. Las noticias desde las 16:00 de Nueva York se asocian a la siguiente sesión disponible; los cierres anticipados requieren un calendario bursátil específico.
- Cada observación diaria se archiva por fuente. Al cambiar de proveedor solo se reconstruye la proyección visible para evitar mezclar ajustes; el historial por fuente se conserva.
- Si la fuente falla, se conservan datos anteriores, se muestra su fecha y un aviso. Sin datos previos se muestra un estado pendiente.

Para recoger todo el catálogo una vez o mantenerlo actualizado en un proceso independiente:

```bash
venv/bin/python collector.py
venv/bin/python collector.py --loop --interval 900
```

El worker de Binance recibe trades, ticker y velas por WebSocket. Los proveedores de acciones conservan sus cierres históricos diarios. Los endpoints públicos pueden cambiar, estar retrasados o no estar disponibles. Antes de una distribución comercial debe contratarse un proveedor con licencia y garantías apropiadas. La app muestra coincidencias temporales, nunca causalidad probada ni predicciones de rentabilidad.

## Persistencia y seguridad

SQLite usa claves foráneas, WAL y transacciones. Las contraseñas usan scrypt con sal. No hay cuenta predefinida. La cookie de sesión es HttpOnly y SameSite=Lax; los formularios y APIs de escritura requieren CSRF. Las redirecciones de login se restringen a rutas locales. Se incluyen CSP, protección contra iframes y límites persistentes por IP para login, registro, actualizaciones y consultas de IA.

El límite de IA es 30 consultas de chat por hora por IP, seis solicitudes de análisis de titulares por hora por IP y 200 solicitudes combinadas por día para esta instancia. Estos límites son para un MVP de una instancia; en un despliegue con proxy o varios procesos deben adaptarse al tráfico e infraestructura. Las respuestas del modelo se muestran como texto y no se ejecuta HTML del proveedor.

SECRET_KEY debe proporcionarse por entorno para conservar sesiones entre arranques. No se lee `data/.session-secret`. Conserva `data/` para mantener cuentas, listas e historial; las bases y backups están ignorados en Git. El historial conserva las últimas 30 entradas por usuario o visitante; se envían como máximo ocho entradas anteriores, la pregunta y un contexto limitado a DeepSeek. El borrado del chat elimina el historial local, no lo ya procesado por el proveedor.

Para un servidor público usa HTTPS mediante un proxy, `COOKIE_SECURE=1`, gestión de secretos, copias de seguridad y supervisión. `HOST=0.0.0.0` habilita acceso de red únicamente cuando lo configuras explícitamente. Registro y login están implementados; verificación de correo y recuperación de contraseña no forman parte de esta entrega.

## Comprobaciones

```bash
venv/bin/python -m unittest discover -s tests -v
node --check static/app.js
curl http://127.0.0.1:5050/health
```

Las 48 pruebas usan bases temporales, fixtures con procedencia y un WebSocket local, sin gastar crédito de DeepSeek ni tocar datos del usuario. `/health` comprueba la base y si existe configuración de IA; `ai_configured: true` **no valida** credencial, saldo ni disponibilidad del proveedor.

Consulta [la auditoría](docs/ARCHITECTURE_AUDIT.md), [el informe de esta entrega](docs/IMPLEMENTATION_REPORT.md) y [las operaciones de datos](docs/DATA_OPERATIONS.md). La inspección visual en navegador queda pendiente porque el host de automatización no está disponible. El documento VALIDACION.md conserva la evidencia anterior y sus correcciones.

## Estructura

```text
app.py                  Entrada WSGI/CLI e importaciones compatibles
market_explained/       Aplicación Flask, APIs v1, mercados, proveedores, worker y almacenamiento
collector.py            Fuentes externas, caché y recogida en segundo plano
ai.py                   DeepSeek, contexto acotado y validación JSON
config.py               Variables de entorno y secreto de sesión
db.py                   Esquema SQLite, transacciones y límites
charts.py               Gráficas SVG accesibles sin CDN
templates/              Landing, aplicación, formularios y asistente
static/                 CSS, JavaScript, marca y tipografía local
tests/test_app.py       Pruebas de integración aisladas
```

No se ha publicado una instancia externa. La implementación mantiene el backend Python existente; el hosting de Sites requiere un runtime de Workers y no ejecuta este proceso Flask/Waitress sin una migración adicional.

Referencias: [DeepSeek Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/), [fundamentos de Carbon](https://www.carbondesignsystem.com/building-blocks/foundations/themes/overview). IBM Plex Sans se distribuye localmente con su licencia en `static/fonts/OFL.txt`.

## Fundación multimercado — fases A y primer flujo B

En una segunda terminal, con el mismo DATABASE_PATH (por defecto
`data/market-live.db`):

```bash
venv/bin/python -m market_explained.ingestion.workers
# Prueba acotada con datos externos reales:
venv/bin/python -m market_explained.ingestion.workers --duration 60 --backfill-days 7
```

Abre `/markets`, busca un instrumento y entra en `/market/BTCUSDT` o
`/market/ETHUSDT`. `/sources` muestra disponibilidad y condiciones. La interfaz
consulta observaciones persistidas cada cinco segundos; no conecta el navegador
al proveedor. El worker solicita hasta 365 velas diarias cerradas. BTCUSDT cotiza
en USDT (Tether), no USD. No se asignan equivalencias implícitas entre tickers.

Los estados son LIVE (evento y recepción de menos de 30 segundos con colector
conectado), HISTORICAL, STALE, DELAYED, DEMO y UNAVAILABLE. Los dos últimos tipos
de feed simulados/retrasados no están habilitados por ningún adaptador actual.
Los datos históricos no se presentan como en vivo; detener el worker conserva
observaciones y las vuelve desactualizadas. No se siembran fixtures en producción.

Prueba externa del 6 de noviembre de 2026: conexión pública Binance verificada,
operaciones/ticker/velas normalizadas y persistidas, API con LIVE mientras el
colector estaba conectado y STALE después. Es una prueba breve, no aceptación
operativa de 24 horas. REST usa el endpoint oficial dedicado a datos públicos;
la conectividad puede variar por región o momento. Ver el informe para cifras.

APIs nuevas (solo lectura):

- `/api/v1/markets`
- `/api/v1/instruments?asset_class=crypto&q=Bitcoin&limit=100&offset=0`
- `/api/v1/market/BTCUSDT`
- `/api/v1/market/BTCUSDT/history?limit=100&offset=0&provider=binance`
- `/api/v1/providers/status`
- `/api/v1/system/health`

Los precios nuevos son strings decimales y las fechas son UTC. La paginación
admite 1–200 registros y offset no negativo. Los errores v1 tienen
`{"error":{"code":"...","message":"..."}}`; el límite es 120 lecturas/minuto/IP
por instancia con Retry-After. Las APIs existentes conservan sus formatos.
`/analysis/<symbol>` y `/predictions/<symbol>` bajo `/api/v1` responden 501:
los modelos no están implementados. WS `/api/v1/stream` está pendiente; la web
usa polling. Forex, Alpaca (IEX/SIP), índices, materias primas y FRED figuran
como planificados, sin precios inventados ni peticiones por falta de credenciales.

SQLite aplica la migración aditiva versionada y crea automáticamente un backup
privado antes del primer cambio. Mantiene cuentas, listas, conversaciones y datos
anteriores. El archivo antiguo `data/market.db` permanece en disco sin importarlo.
Consulta recuperación y límites en [DATA_OPERATIONS.md](docs/DATA_OPERATIONS.md).

## Licencias, contribuciones y despliegue

El código propio se publica bajo [MIT](LICENSE). IBM Plex conserva su OFL. Los
materiales de referencia, noticias y datos de terceros no reciben una nueva licencia
por estar aquí. Consulta las condiciones enlazadas en `/sources`; una API pública
no concede automáticamente permiso de redistribución. [Contribuciones](CONTRIBUTING.md),
[seguridad](SECURITY.md) y [conducta](CODE_OF_CONDUCT.md).

Docker Compose, preparación amd64/ARM64 y un plan opcional OCI Always Free están
en [infrastructure/deployment](infrastructure/deployment/README.md). No se ha
verificado una compilación Docker local ni un despliegue cloud. La aplicación no
requiere cuenta cloud. No se crean recursos pagos ni se publica el backend en
GitHub Pages. GitHub Actions prepara pruebas, lint, tipos, seguridad y build.

**Aviso financiero:** información y educación únicamente. No hay conexión a
brokers, ejecución de órdenes, promesas de rentabilidad ni predicciones de esta
entrega. Correlación no implica causalidad. Revisa fecha, fuente y límites de datos.

Documentación primaria del adaptador: [Binance WebSocket](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams),
[REST de mercado](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints)
y [endpoints públicos de datos](https://developers.binance.com/docs/binance-spot-api-docs/faqs/market_data_only).

Para publicar la aplicación completa sin depender de la laptop, sigue
[Publicar gratis](infrastructure/deployment/PUBLICAR_GRATIS.md): máquina externa
Always Free sujeta a disponibilidad, procesos independientes, volumen SQLite y
proxy HTTPS. GitHub Pages por sí solo no ejecuta el backend. La guía y configuración
no significan que exista ya una instancia pública.
