<div align="center">
  <img src="static/mark.svg" width="56" height="56" alt="Explainable Market">
  <h1>Explainable Market</h1>
  <p>Datos de mercado con fuente. Contexto comprensible. Predicciones con incertidumbre.</p>
  <p><strong>Español · English · 简体中文</strong></p>
  <p><a href="#ejecución-local">Inicio rápido</a> · <a href="#funcionalidad-y-estado">Funcionalidad</a> · <a href="docs/ARCHITECTURE_AUDIT.md">Arquitectura</a> · <a href="CONTRIBUTING.md">Contribuir</a> · <a href="SECURITY.md">Seguridad</a></p>
</div>

Plataforma de código abierto para explorar precios, noticias y conceptos financieros.
Conserva Flask, Jinja, JavaScript nativo y gráficas SVG generadas en el servidor:
sin servicios de IA obligatorios ni un frontend que dependa de un CDN.

**Solo información y educación.** No conecta cuentas de brokerage, no ejecuta
órdenes y no promete rentabilidad. Las estimaciones pueden fallar; una coincidencia
temporal o una contribución del modelo no demuestra causalidad.

## Funcionalidad y estado

| Área | Implementado | Límites actuales |
| --- | --- | --- |
| Acciones estadounidenses | Cierres diarios Yahoo/Nasdaq, noticias RSS y CSV | No son cotizaciones en vivo; 12 instrumentos iniciales |
| Criptomonedas | Binance público: trades, ticker, velas y backfill | BTCUSDT y ETHUSDT; cotizan en USDT, no USD |
| Forex y oro | Twelve Data REST opcional: EUR/USD, USD/JPY y XAU/USD | Cuotas y licencia; visualización externa deshabilitada por defecto |
| Predicciones | Persistencia, ridge y XGBoost CPU opcional; evaluación cronológica | Al menos 120 cierres; sin validación independiente ni precisión garantizada |
| Asistente y sentimiento | BigModel o DeepSeek opcional, contexto acotado y JSON validado | Requieren credencial válida; guía educativa local cuando falta la clave |
| Experiencia de usuario | Registro, sesiones, watchlists persistentes, biblioteca y tres idiomas | Sin recuperación de contraseña ni verificación de correo |

Índices SPX/FTSE permanecen no disponibles con el acceso probado. Alpaca, FRED,
streaming forex y WebSocket hacia el navegador están pendientes. La web consulta
el estado persistido cada cinco segundos; el streaming Binance ocurre en un worker.
No se generan precios sintéticos para completar mercados sin datos.

### Cómo leer las gráficas

- **Verde / rojo / gris:** cada precio observado sube, baja o no cambia respecto al anterior.
- **Amarillo discontinuo:** siguiente cierre estimado, tanto si sube como si baja.
- **Sombreado amarillo:** intervalo empírico nominal del 80%; no garantiza cobertura futura.

En `/intelligence?symbol=BTCUSDT` se muestran hasta 30 cierres hasta el corte del
modelo y su predicción. Se comprueban fuente, corte y precio de referencia antes
de unirlos. El ancho del horizonte futuro es ilustrativo, sin inventar una sesión.
La fuente, las fechas UTC y las limitaciones permanecen visibles.

## Ejecución local

Requiere Python 3.11 o superior. Validación local actual: Python 3.12.

```bash
git clone https://github.com/deepdevjose/explainable-market.git
cd explainable-market
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
./run.sh
```

Abre **http://127.0.0.1:5050**. Waitress ejecuta la aplicación sin depurador.
El lanzador admite `.venv/` y el entorno histórico `venv/`. Una instalación nueva
arranca sin credenciales; los mercados externos pueden tardar o no estar disponibles.

Para conservar sesiones entre arranques, configura una `SECRET_KEY` privada y
estable. Sin ella, desarrollo utiliza una clave efímera. Producción la exige.

### Configuración privada

[.env.example](.env.example) documenta variables **sin credenciales**. La aplicación
lee el entorno del proceso; no carga automáticamente `.env` ni archivos heredados.
Usa tu gestor de secretos o la configuración privada de un servicio. Nunca pegues
valores reales en el ejemplo, commits, incidencias, capturas o comandos compartidos.

| Variable | Uso |
| --- | --- |
| `SECRET_KEY` | Secreto de sesión estable; al menos 32 caracteres en producción |
| `APP_ENV`, `COOKIE_SECURE`, `TRUSTED_PROXY` | Producción, HTTPS y proxy de confianza exacto |
| `DATABASE_PATH` | SQLite; predeterminado `data/market-live.db` |
| `AI_PROVIDER` | `deepseek` (compatibilidad predeterminada) o `bigmodel` |
| `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL` | Asistente DeepSeek opcional |
| `BIGMODEL_API_KEY`, `BIGMODEL_MODEL` | Asistente BigModel; modelo predeterminado `glm-5.3-flash` |
| `TWELVE_DATA_API_KEY` | Proveedor de mercado opcional, independiente de la IA |
| `TWELVE_DATA_PUBLIC_DISPLAY` | `0` por defecto; cambiar solo tras confirmar derechos externos |

Las claves permanecen en el servidor. El usuario ve qué proveedor de IA recibe su
consulta y contexto. Sin clave seleccionada se ofrece una guía local identificada
como no generativa; un fallo de un proveedor configurado produce un error, sin
cambiar silenciosamente a otro proveedor. [Configuración y validación de IA](docs/AI_PROVIDERS.md).

### Colectores y modelos

Ejecuta cada proceso en una terminal independiente, compartiendo `DATABASE_PATH`:

```bash
# Acciones y noticias; una sola ejecución si omites --loop.
.venv/bin/python collector.py --loop --interval 900
# Streaming cripto y backfill de velas cerradas.
.venv/bin/python -m market_explained.ingestion.workers
# Opcional: consulta Twelve Data con cuotas persistentes.
.venv/bin/python -m market_explained.ingestion.twelve_worker
# Opcional: entrenamiento fuera del servidor web.
.venv/bin/python -m pip install -r requirements-ml.txt
.venv/bin/python -m market_explained.intelligence.worker
```

Los dos últimos workers admiten `--once`. La ingesta Binance no necesita clave.
Los modelos usan divisiones cronológicas y evaluación walk-forward; no entrenan
con velas abiertas ni mezclan feeds. [Protocolo, resultados y límites](docs/PREDICTIVE_INTELLIGENCE.md).

## Datos, persistencia y API

SQLite utiliza WAL, claves foráneas y transacciones. Las migraciones son aditivas,
versionadas y precedidas de una copia privada. Conservan cuentas, watchlists,
mensajes e historial por proveedor. [Backup y recuperación](docs/DATA_OPERATIONS.md).

Los eventos normalizados conservan procedencia, precios decimales y timestamps UTC.
Los estados distinguen **LIVE, DELAYED, HISTORICAL, STALE, DEMO y UNAVAILABLE**.
LIVE requiere evento y recepción recientes y colector conectado. Detener el worker
conserva el último dato y lo vuelve desactualizado; no lo convierte en un dato nuevo.

| Página | Contenido |
| --- | --- |
| `/app`, `/watchlist`, `/symbol/AAPL` | Panorama, lista personal y detalle de acciones |
| `/markets`, `/market/BTCUSDT` | Explorador e instrumentos con proveedor y frescura |
| `/intelligence` | Predicción, gráfica, evaluación y contribuciones |
| `/news`, `/learn`, `/sources` | Noticias, educación y estado de fuentes |

Las rutas existentes se conservan. La API de lectura v1 incluye `/markets`,
`/instruments`, `/market/<symbol>`, `/market/<symbol>/history`, `/analysis/<symbol>`,
`/predictions/<symbol>`, `/providers/status` y `/system/health` bajo `/api/v1`.
Las listas paginan con `limit` (1–200) y `offset`. Los errores usan
`{"error":{"code":"…","message":"…"}}`; hay límites persistentes por IP.
Los pronósticos devuelven 503 si faltan datos/entrenamiento y 403 si la visualización
está restringida. `/health` verifica la base; `ai_configured` solo indica configuración,
no valida saldo ni disponibilidad externa.

## Desarrollo y comprobaciones

```bash
.venv/bin/python -m pip install -r requirements-dev.txt -r requirements-ml.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/bandit -q -r market_explained ai.py charts.py collector.py config.py db.py -ll
.venv/bin/pip-audit -r requirements.txt -r requirements-ml.txt
node --check static/app.js
.venv/bin/python scripts/check_repository_hygiene.py
# Después de seleccionar archivos con git add, revisar el contenido exacto del commit:
.venv/bin/python scripts/check_repository_hygiene.py --staged
```

Las pruebas usan bases temporales, fixtures y WebSockets locales sin solicitudes
externas. GitHub Actions configura pruebas, lint, tipos, auditoría de dependencias
y build amd64/ARM64. La evidencia externa y visual se documenta por separado;
una configuración de CI o despliegue no demuestra que haya sido ejecutada.

## Arquitectura y operación

```text
app.py                  Entrada Flask/WSGI compatible
market_explained/       API, mercados, proveedores, ingesta, inteligencia y almacenamiento
collector.py / ai.py    Adquisición histórica e integración educativa compatibles
config.py / db.py       Configuración explícita y operaciones SQLite
charts.py               Gráficas SVG sin CDN
templates/ / static/    Jinja, diseño existente, JavaScript y fuentes locales
tests/                  Pruebas aisladas y fixtures con procedencia
docs/                   Auditoría, protocolos y evidencia de validación
infrastructure/         Docker Compose y preparación de despliegue
```

- [Auditoría de arquitectura](docs/ARCHITECTURE_AUDIT.md) y [primera entrega](docs/IMPLEMENTATION_REPORT.md).
- [Demo supervisada desde Linux](docs/LAPTOP_DEMO.md): servicios al arrancar y túnel temporal. Requiere equipo encendido y conectado; no es alojamiento independiente.
- [Despliegue y Docker](infrastructure/deployment/README.md): preparación opcional, no un despliegue cloud certificado. GitHub Pages no ejecuta el backend Flask ni sus workers.
- [Revisión antes de publicar](docs/RELEASE_CHECKLIST.md): alcance de las comprobaciones y exposición histórica.

## Seguridad y licencias

**Hubo una exposición histórica de material sensible.** Se limpiaron las ramas
publicadas y se conservó la aplicación actual. Esto no revoca claves ni elimina
copias anteriores, forks o cachés de GitHub. Consulta [SECURITY.md](SECURITY.md) y
[el informe de limpieza](docs/HISTORY_CLEANUP.md) antes de reutilizar credenciales
o cambios de clones antiguos.

El código propio usa [MIT](LICENSE); IBM Plex conserva su [OFL](static/fonts/OFL.txt).
Noticias y datos externos mantienen sus derechos originales: acceso gratuito o
público no equivale a autorización de redistribución. `/sources` identifica las
condiciones de los proveedores. Twelve Data se oculta externamente por defecto.

Lee la [guía de contribución](CONTRIBUTING.md), el [código de conducta](CODE_OF_CONDUCT.md)
y la [política de seguridad](SECURITY.md). Conservamos el diseño existente y las
funciones educativas mediante cambios incrementales.
