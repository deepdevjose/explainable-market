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

El instalador crea cuatro servicios de **usuario**, habilitados para el inicio de
sesión: `market-explained-demo-web`, `-worker`, `-daily` y `-tunnel`. Se reinician
si fallan y no dependen del proceso del asistente ni de una terminal abierta.
No se configura ejecución después del cierre de sesión ni se modifica la política
de suspensión del equipo. El colector diario consulta cada 900 segundos; Binance
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
Los modelos predictivos y los proveedores aún no conectados no se presentan como
implementados. La ilustración de la portada es conceptual y está etiquetada.

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
