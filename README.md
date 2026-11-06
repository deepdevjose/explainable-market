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

Copia `.env.example` a `.env` y escribe tu clave en `DEEPSEEK_API_KEY`. Las variables del proceso tienen prioridad. Por compatibilidad se admite `DEEPSEEK_KEY` del archivo local `env (1).txt`; no se usan los campos de Softr de ese archivo.

```bash
cp .env.example .env
# Edita .env con tu editor. No pegues la clave en el terminal ni en el chat.
./run.sh
```

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
- Al cambiar de proveedor se sustituye la serie del activo para evitar mezclar ajustes de precios diferentes.
- Si la fuente falla, se conservan datos anteriores, se muestra su fecha y un aviso. Sin datos previos se muestra un estado pendiente.

Para recoger todo el catálogo una vez o mantenerlo actualizado en un proceso independiente:

```bash
venv/bin/python collector.py
venv/bin/python collector.py --loop --interval 900
```

No hay suscripción a un feed en tiempo real. Los endpoints públicos pueden cambiar, estar retrasados o no estar disponibles. Antes de una distribución comercial debe contratarse un proveedor con licencia y garantías apropiadas. La app muestra coincidencias temporales, nunca causalidad probada ni predicciones de rentabilidad.

## Persistencia y seguridad

SQLite usa claves foráneas, WAL y transacciones. Las contraseñas usan scrypt con sal. No hay cuenta predefinida. La cookie de sesión es HttpOnly y SameSite=Lax; los formularios y APIs de escritura requieren CSRF. Las redirecciones de login se restringen a rutas locales. Se incluyen CSP, protección contra iframes y límites persistentes por IP para login, registro, actualizaciones y consultas de IA.

El límite de IA es 30 consultas de chat por hora por IP, seis solicitudes de análisis de titulares por hora por IP y 200 solicitudes combinadas por día para esta instancia. Estos límites son para un MVP de una instancia; en un despliegue con proxy o varios procesos deben adaptarse al tráfico e infraestructura. Las respuestas del modelo se muestran como texto y no se ejecuta HTML del proveedor.

`data/.session-secret` se genera con permisos 0600 y se reutiliza entre arranques. Conserva `data/` para mantener cuentas, listas, historial y sesiones. El historial conserva las últimas 30 entradas por usuario o visitante; se envían como máximo ocho entradas anteriores, la pregunta y un contexto limitado a DeepSeek. El borrado del chat elimina el historial local, no lo ya procesado por el proveedor.

Para un servidor público usa HTTPS mediante un proxy, `COOKIE_SECURE=1`, gestión de secretos, copias de seguridad y supervisión. `HOST=0.0.0.0` habilita acceso de red únicamente cuando lo configuras explícitamente. Registro y login están implementados; verificación de correo y recuperación de contraseña no forman parte de esta entrega.

## Comprobaciones

```bash
venv/bin/python -m unittest discover -s tests -v
node --check static/app.js
curl http://127.0.0.1:5050/health
```

Las 19 pruebas de integración usan una base temporal y proveedores sustituidos, sin gastar crédito de DeepSeek ni tocar datos del usuario. `/health` comprueba la base y si existe configuración de IA; `ai_configured: true` **no valida** credencial, saldo ni disponibilidad del proveedor.

Consulta [la definición del producto](docs/PRODUCTO.md) y [la evidencia de validación](docs/VALIDACION.md). Se probaron rutas HTTP y fuentes externas. La inspección visual en navegador queda pendiente porque el host de automatización no está disponible en esta sesión.

## Estructura

```text
app.py                  Páginas, cuentas, sesiones, APIs, exportación
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
