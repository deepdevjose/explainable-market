# Demo pública desde la laptop

La laptop ejecuta la aplicación Flask existente, SQLite y los colectores reales.
Cloudflare Quick Tunnel publica una URL HTTPS temporal; no utiliza la pantalla
intermedia de Microsoft Dev Tunnels. No es alojamiento permanente ni garantiza
acceso desde China. Mantener la laptop despierta y con Internet durante la demo.

## Servicios supervisados

En esta instalación Linux se usa Python 3.12 en `.venv/` y el binario oficial de
Cloudflare 2026.10.7, extraído sin privilegios de administrador. Se verificó su
SHA-256 contra el índice oficial de paquetes de `pkg.cloudflare.com`.
No se descarga ni ejecuta software al abrir la web.

```bash
.venv/bin/python scripts/demo_services.py install
.venv/bin/python scripts/demo_services.py status
.venv/bin/python scripts/demo_services.py url
```

El instalador crea seis servicios de **usuario**: `market-explained-demo-web`,
`-worker`, `-daily`, `-twelve`, `-forecast` y `-tunnel`. Habilita `loginctl enable-linger`
para arrancarlos al encender el equipo y mantenerlos después del cierre de sesión. Se reinician
si fallan y no dependen del proceso del asistente ni de una terminal abierta.
No se modifica la política de suspensión del equipo. El servidor no funciona
mientras la laptop duerme o está apagada. Se configuró el inicio al arrancar, pero
no se reinició físicamente la laptop durante la validación. El colector diario consulta cada 900 segundos; Binance
recibe eventos por WebSocket, y la interfaz lee el estado persistido cada 5 segundos.

La configuración privada queda en `~/.config/market-explained-demo/server.env`,
con permisos 0600 y una clave de sesión estable generada una sola vez. Se mantiene
fuera de Git. No reutilizar credenciales históricamente expuestas. El servidor usa
cookies seguras y escucha solo en loopback; el túnel proporciona HTTPS. El acceso
HTTP local no sustituye la prueba de registro/login mediante la URL HTTPS pública.
Para activar DeepSeek, añadir una **nueva clave válida** a ese archivo local como
`DEEPSEEK_API_KEY=...` y reiniciar únicamente el servicio web. Nunca compartirlo.

```bash
systemctl --user restart market-explained-demo-web
journalctl --user -u market-explained-demo-worker -n 30 --no-pager
.venv/bin/python scripts/demo_services.py stop
.venv/bin/python scripts/demo_services.py start
```

No detener o reiniciar el túnel durante la grabación: su URL cambiará cuando se
cree una nueva conexión Quick Tunnel. Consultar de nuevo `url` tras reiniciarlo.
No compartir bases de datos, secretos ni archivos de configuración privada.

## Idiomas y comportamiento visible

El selector permite español, inglés y chino mandarín simplificado (`zh-Hans`).
Se conserva por sesión y funciona entre páginas. Los catálogos son locales:
no se llama a un traductor externo ni se envían titulares o datos personales para
traducir. Noticias originales, nombres de compañías, textos ya guardados del chat,
atribución y códigos de calidad se mantienen en su idioma original.

Los precios cripto se leen cada cinco segundos y destellan en verde o rojo solo
cuando cambia una observación recibida. Se respeta `prefers-reduced-motion`.
La gráfica breve de cripto muestra hasta 60 observaciones **recibidas durante la
visita**, no todos los trades ni una serie inventada; el gráfico histórico SVG se
conserva. Las acciones siguen usando cierres diarios, nunca simulación de tiempo real.

Sin DeepSeek se ofrece una guía local determinista, identificada expresamente como
no generativa, para conceptos básicos. No clasifica titulares ni promete conversación
libre. El análisis de sentimiento sigue requiriendo una clave y saldo válidos.
Los modelos de persistencia, ridge y XGBoost CPU se entrenan fuera del servidor
web y aparecen en `/intelligence`. Twelve Data se consulta cada 15 minutos y
sus observaciones se etiquetan DELAYED o STALE, según la frescura. Los demás
proveedores pendientes se mantienen identificados como tales. La ilustración de la portada es conceptual y está etiquetada.

## Comprobación realizada el 12 de noviembre de 2026

- 53 pruebas automatizadas: las 48 anteriores y cinco de idiomas/aislamiento/guía local.
- Doce acciones actualizadas hasta el cierre del 11 de noviembre; noticias consultadas.
- Binance con eventos reales recientes y estado LIVE; almacenamiento conservado.
- Cuatro servicios de usuario activos. `/health` y portada accesibles por HTTPS.
- Navegador Chromium: selector, chino e inglés, escritorio y móvil; revisión de capturas.
- La red local no resolvió inicialmente el dominio Quick Tunnel. La comprobación HTTPS
  usó `curl --resolve` con la IP obtenida de un resolvedor público, manteniendo TLS.
  Una comprobación posterior respondió también con el DNS habitual. Esto no certifica
  la accesibilidad desde el dispositivo del compañero.

Antes del vídeo: abrir la URL desde el equipo que grabará, navegar a Mercados,
comprobar timestamps/estado y probar registro, lista personal y CSV. La demo no
convierte los endpoints públicos de terceros en una licencia de redistribución.

Validaciones estáticas: Ruff sin errores, mypy sin incidencias en los 14 módulos
seleccionados y Bandit sin hallazgos de gravedad media/alta en el alcance revisado.


## Actualización: mercados y pronósticos

Instalar también `requirements-ml.txt` antes de ejecutar el instalador de servicios.
El worker de modelos revisa nuevos cierres cada 30 minutos y no reentrena si el
hash del conjunto no cambia. `-twelve` usa límites locales persistentes de 6 créditos
por minuto y 600 por ventana de 24 horas, inferiores al plan Basic documentado de
8/min y 800/día. Cada petición consume un crédito; otras aplicaciones que usen la
misma clave pueden agotar la cuota fuera de estos contadores.

La configuración privada acepta `TWELVE_DATA_API_KEY` y
`TWELVE_DATA_PUBLIC_DISPLAY` (predeterminado 0). Mantener ese segundo valor en 0
si no existen derechos de visualización externa. Los precios y derivados de Twelve
Data se ocultan en todo acceso externo, incluidos el historial y el contexto del
asistente. La consulta interna directa por loopback permite inspeccionarlos.
Después de cambiar el archivo privado, reiniciar los servicios afectados:

```bash
systemctl --user restart market-explained-demo-web market-explained-demo-twelve
systemctl --user restart market-explained-demo-forecast
loginctl show-user "$USER" -p Linger
systemctl --user is-enabled market-explained-demo-web
```

La instalación actual verificó `Linger=yes`, seis servicios activos y recuperación
automática de web después de terminar su proceso: nuevo PID y `/health` HTTP 200.
No se reinició el túnel durante esta actualización, por lo que se conservó el enlace.
Consultar el informe de [modelos](PREDICTIVE_INTELLIGENCE.md) para resultados.
