# Informe de implementación — 6 de noviembre de 2026

## 1. Auditoría

Se inspeccionó el historial completo disponible (repositorio no shallow, dos commits
originales), todos los módulos Python, todos los templates, CSS, JavaScript, pruebas
y documentos de operación antes de modificar código. Las 19 pruebas originales
pasaron como línea base. [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md) distingue
capacidades verificadas, problemas, riesgos y trabajo diferido.

Hallazgos principales: carga implícita de credenciales, secretos/bases/bytecode
versionados, borrado de series al cambiar proveedor, identidad basada solo en ticker,
precios REAL y ausencia de migraciones, backups, workers de streaming o CI.

## 2. Arquitectura implementada

Monolito modular incremental. `market_explained/application.py` contiene la aplicación
Flask existente; `app.py` conserva las importaciones y entrada ejecutable/WSGI.
Los nuevos módulos separan APIs v1, contratos/instrumentos, proveedores, worker y
almacenamiento. La recogida diaria existente mantiene su compatibilidad y sus
funciones públicas, ahora con adaptadores independientes Yahoo/Nasdaq. No se
reemplazaron framework, frontend, autenticación ni motor de gráficas.

## 3. Archivos nuevos y modificados

- Nuevos: `market_explained/{api,markets,providers,ingestion,storage}/`, migración SQL,
  templates `markets.html`, `market.html`, `sources.html`, fixtures de documentación
  y capturas reales REST/WebSocket, pruebas de configuración/migración/ingesta.
- Nuevos: `.env.example`, `.gitignore`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`,
  `CODE_OF_CONDUCT.md`, plantillas de issues/PR, workflow CI, configuración Ruff/mypy,
  dependencias de desarrollo, verificador de higiene, Docker/Compose y documentación
  de arquitectura, datos y despliegue.
- Modificados: `app.py`, `config.py`, `db.py`, `collector.py`, `ai.py`, `charts.py`,
  requirements/run.sh, README, navegación/base, panorama, metodología, CSS y JS.
- Retirados exclusivamente del índice Git: archivo de credenciales, secreto local,
  ambas bases y bytecode. Las copias locales se conservan. El historial no se reescribió.

## 4. Funciones existentes preservadas

Landing, panorama, registro/login/logout, cuentas con hash, listas privadas,
noticias/RSS/filtros/sentimiento, ventanas de reacción, biblioteca, asistente
DeepSeek opcional, historial separado, borrado de chat y CSV. Se conservan rutas y
formatos anteriores, Jinja, SVG, IBM Plex local, tokens de color/espaciado,
temas claro/oscuro, breakpoints y controles de teclado. Las 19 pruebas originales
no fueron modificadas. La revisión visual final sigue pendiente; conservación de
CSS y renderizado HTTP no equivalen a aceptación visual.

## 5. Nueva funcionalidad implementada

Registro explícito de BTCUSDT y ETHUSDT de Binance Spot, sin confundir USDT con USD.
Eventos canónicos validados con Decimal, UTC, origen, secuencia, precios, bid/ask,
volumen, OHLCV y estado de cierre. Historial inmutable, deduplicación, control de
orden, estado por fuente/tipo, checkpoints atómicos y registros de calidad.

Worker asyncio independiente: stream público de trades/ticker/velas de un minuto,
backfill de hasta 365 velas diarias cerradas, ping/pong, timeout, rotación antes de
24 horas, reconexión con jitter/backoff, resuscripción, colas acotadas, aislamiento
entre tareas REST/stream/proveedores y apagado con drenaje.

Páginas integradas `/markets`, `/market/<symbol>`, `/sources`; filtros/búsqueda,
procedencia y fechas. La página consulta la API cada cinco segundos, sin abrir
conexiones del navegador al proveedor. Estados actuales se derivan de frescura y
conexión, sin promover datos históricos a LIVE. Nuevas APIs v1 paginadas y limitadas
con contrato de error. Registry de capacidades y enlaces de condiciones por fuente.

## 6. Pruebas ejecutadas y resultados

- `venv/bin/python -m unittest discover -s tests -q`: **46/46 pasan** en Python 3.14.
  Incluye las 19 originales, migración/restauración de backup, conservación de
  cuentas/listas/mensajes/noticias/precios, procedencia tras cambiar proveedor,
  contratos/precisión/validación, deduplicación/orden/checkpoints, datos históricos
  e incompletos, estados, APIs, cuotas, reconexión/resuscripción sobre WebSocket
  local, aislamiento de fallos REST/proveedor, drenaje y fallo de almacenamiento.
- Pruebas automatizadas sin API externa: fixtures fijas y capturas reales con fecha
  y fuente; servidor WebSocket exclusivamente localhost. Ningún fixture se importa
  a la base activa ni aparenta ser un feed en vivo.
- `venv/bin/ruff check .`: pasa.
- `venv/bin/mypy`: pasa en los **14 archivos** del subsistema nuevo seleccionado;
  no se afirma tipado completo del código Flask original.
- `venv/bin/bandit -q -r market_explained ai.py charts.py collector.py config.py db.py -ll`:
  sin hallazgos de severidad media/alta. Las aperturas HTTPS fijas tienen supresiones
  específicas justificadas; XML externo se procesa con defusedxml.
- `venv/bin/pip-audit -r requirements.txt`: sin vulnerabilidades conocidas al ejecutar.
- `node --check static/app.js` y `compileall` de módulos: pasan.
- Higiene del índice Git: sin bases, credenciales locales, bytecode ni literales
  de clave detectados por el verificador limitado. Esto no certifica el historial.
- Inicio real **`PORT=5058 ./run.sh`**, Waitress, con la base activa: HTTP 200 en
  landing, app, news, learn, login, register, symbol/AAPL, markets, market/BTCUSDT,
  sources, health, CSV y APIs comprobadas (16 comprobaciones HTTP).
- AAPL: 127 cierres, fuente Nasdaq, último cierre 2026-11-05 y sin price_error al
  consultar el runtime tras la actualización. Se conservó el contrato diario existente.
- Navegador: `The browser access host is unavailable`; no se produjeron capturas ni
  se verificó visualmente contraste, móvil o interacción real de teclado.
- Docker no está instalado en este entorno: Compose/build/ARM64 no se ejecutaron.
  El workflow se preparó, pero no se afirma que GitHub Actions haya corrido.

## 7. Migración de datos

`001_market_foundation.sql` es aditiva y transaccional, con backup online SQLite
0600 antes de aplicar cambios y versión registrada. Mantiene tablas originales.
Archiva cierres anteriores por proveedor y nuevas revisiones antes de actualizar la
proyección de compatibilidad. Al cambiar proveedor no se borra el archivo histórico.
No recupera datos ya borrados por versiones antiguas ni precisión perdida por REAL.
Los timestamps de cierre diario bursátil desconocidos no se inventan.

Las pruebas ejercitan una base con cuenta, lista, conversación, noticia y precios
antes de migrar, ejecutan init dos veces, comparan filas y verifican integridad de
la copia restaurable. El archivo antiguo market.db permanece intacto y no se importa.
Procedimiento y límites en [DATA_OPERATIONS.md](DATA_OPERATIONS.md).

## 8. Estado de proveedores y evidencia externa

**Binance implementado y conexión real verificada.** Los primeros intentos contra
stream.binance.com y data-stream.binance.vision expiraron durante handshake;
api.binance.com devolvió `Network is unreachable`. El endpoint oficial de datos
REST data-api.binance.vision respondió. Una prueba posterior contra
`wss://data-stream.binance.vision:443` conectó correctamente.

En una base temporal, una ejecución de 25 segundos persistió **1.734 eventos de
stream y 730 velas históricas** para los dos pares. En la base activa, una ejecución
posterior de 50 segundos persistió **2.432 eventos de stream** (2.294 trades,
92 ticker y 46 actualizaciones de vela) y **730 velas diarias cerradas**. Hubo
apagado ordenado, cero reconexiones en esa ejecución e integridad SQLite `ok`.
Los contadores son evidencia puntual, no cifras permanentes ni garantía de caudal.

La API respondió LIVE para ambos pares durante la conexión con timestamps UTC y
provider=binance; después de detener el worker respondió STALE conservando el dato.
Se capturaron frames reales de los tres tipos y una respuesta REST como fixtures.
Los valores históricos siguen siendo HISTORICAL. Las verificaciones locales HTTP
y conteos completos quedan en artifacts/ ignorado; nunca se publica una base.

**Yahoo/Nasdaq:** adquisición diaria preservada, con Nasdaq comprobado en runtime.
**Twelve Data/Alpaca/FRED:** metadatos de capacidad/licencia y estado planificado;
no adaptadores operativos ni solicitud de credenciales. Forex, índices y materias
primas muestran ausencia de datos. SPY sigue siendo un ETF, no un feed de índices.

## 9. Límites conocidos

No se hizo una prueba continua de 24 horas: la rotación se verificó con simulación
local. No hay reparación completa de trades/minutos perdidos, persistencia de colas
tras kill abrupto, retención automática, benchmark de carga sostenida o varios
workers coordinados. Los checkpoints y gaps son persistentes; el backfill diario
se reconsulta idempotentemente. Ejecutar un worker por DB y vigilar crecimiento.

No hay WS público `/api/v1/stream`; la interfaz usa polling. `/api/v1/analysis` y
`predictions` con símbolo responden 501, sin datos de modelo fabricados. No hay
ML/SHAP ni indicadores de fase D. La reorganización de auth/usuarios/assistant
continúa incrementalmente: sus funciones permanecen en el módulo Flask preservado.
DeepSeek requiere credencial nueva y no se probó conversación real en esta entrega.
Falta revisión visual, instalación de contenedores y aceptación cloud/ARM64.

## 10. Seguridad y licencias

Se confirmó exposición histórica de credencial DeepSeek, secreto de sesión y bases
con registros antiguos. **Deben revocarse/rotarse los secretos y revisarse los datos
expuestos. No se rotaron credenciales del proveedor desde este trabajo.** Eliminar
archivos del índice no elimina el historial. No se reprodujeron valores ni se hizo
force push/rewrite. Se corrigió la documentación anterior que afirmaba un ignore
inexistente. Se eliminó la carga de archivos locales y se exige entorno explícito.

Se mantienen CSRF, hash de contraseña, redirecciones locales, CSP y cookies seguras;
se añaden validación de proxy explícito, claves requeridas en producción, permisos
privados de SQLite y parsing XML protegido. CI/higiene son controles limitados, no
una certificación de seguridad. MIT cubre código propio; OFL y derechos de datos,
noticias/materiales ajenos conservan sus condiciones. No se ejecutan operaciones.

## 11. Comandos locales

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
export SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
./run.sh
# Otra terminal, mismo DATABASE_PATH o mismo directorio por defecto:
venv/bin/python -m market_explained.ingestion.workers
```

Abrir http://127.0.0.1:5050/markets. No hay cuenta cloud obligatoria. Para sesiones
persistentes conservar SECRET_KEY en un gestor/servicio privado. No repetir su
rotación en cada arranque. `DEEPSEEK_API_KEY` es opcional, exportada solo al backend.

```bash
venv/bin/python -m pip install -r requirements-dev.txt
venv/bin/python -m unittest discover -s tests -v
venv/bin/ruff check .
venv/bin/mypy
node --check static/app.js
```

## 12. Próxima fase y control de cambios

Completar aceptación visual y una campaña prolongada de streaming/rotación,
medir SQLite/disk y añadir reparación de gaps antes de ampliar pares. Luego fase C:
Twelve Data opcional con cuotas/licencias, Alpaca con IEX/SIP separados e integración
macroeconómica FRED. Solo después abordar indicadores y evaluación cronológica de
fase D, comenzando por baseline de persistencia y sin publicidad de precisión.

Cambios en `feat/multi-market-data-foundation`, commits lógicos de refactor,
ingesta/UI y preparación de operación/gobernanza. No se fusionó main, no se hizo
push ni se crearon recursos cloud. Docker, workflow y guía OCI son preparación,
no despliegue verificado.
