# Evidencia de validación anterior

> Evidencia histórica del MVP, no el estado completo actual. La auditoría posterior
> confirmó que el archivo de credenciales, el secreto de sesión y las bases sí
> entraron en Git en f51fc78; la afirmación anterior sobre .gitignore era incorrecta.
> Fueron retirados del seguimiento sin reescribir historia. Deben rotarse las claves.
> Configuración actual: solo entorno; no se cargan archivos locales. Consulta
> [SECURITY.md](../SECURITY.md) y [el informe actual](IMPLEMENTATION_REPORT.md).

Fecha: 6 de noviembre de 2026 (Asia/Shanghai).

## Resultado

La implementación local conecta la aplicación a una base SQLite nueva y a fuentes externas reales. Las rutas y pruebas de integración pasan. Quedan pendientes el ensayo real de IA con una credencial válida y la revisión visual en navegador.

## Comprobado

- Instalación de dependencias en el `venv/` existente: Flask 3.1.3 y Waitress 3.0.2.
- Compilación de los módulos Python y validación sintáctica de `static/app.js` con Node.
- 19 pruebas de integración satisfactorias, aisladas en bases temporales.
- Inicio real con `./run.sh`, servido por Waitress en `127.0.0.1:5050`.
- HTTP 200 en landing, panorama, noticias, biblioteca, login, registro y detalle de AAPL, además de CSS, JavaScript y tipografía local.
- `/health`: base conectada y detección de configuración de IA. Este endpoint no certifica conectividad con DeepSeek.
- Recogida real de AAPL, MSFT, NVDA y SPY: **508 cierres diarios** y **71 titulares RSS**, persistidos en `data/market-live.db`. Son los conteos de esta recogida, no cifras permanentes del producto.
- Fuente de precios de esta recogida: Nasdaq. Yahoo devolvió HTTP 403 desde este entorno; la alternativa recibió y guardó las series.
- Descarga y servicio local de IBM Plex Sans, junto con la licencia OFL.
- La clave del archivo suministrado no aparece en HTML, respuestas de APIs ni archivos fuente. El archivo de credenciales y `.env` están excluidos mediante `.gitignore`.

## Cobertura de las 19 pruebas

Renderizado sin datos y ausencia de siembra ficticia; registro, hash de contraseña y seguimiento persistente; aislamiento entre usuarios; login y redirección local; CSRF y origen; logout solo por POST; acceso a lista privada; gráfica con sentimiento aún desconocido y ventanas completas; filtros de noticias; CSV y procedencia en API; contexto de chat derivado del servidor e historial separado; error explícito de IA sin guardar una respuesta falsa; entradas JSON inválidas; validación del alcance de respuesta; sentimiento validado y persistido; límites de uso; conservación de precios ante caída del proveedor; idempotencia y reemplazo de serie al cambiar de proveedor; cabeceras y ausencia de secretos públicos.

Las respuestas de IA en estas pruebas están sustituidas para verificar el contrato y la lógica. No son evidencia de capacidad, exactitud o resistencia a jailbreak de un modelo real.

## Pendiente y bloqueos observados

1. **DeepSeek**: una solicitud real de chat y una comprobación del endpoint de modelos devolvieron HTTP 401. La credencial se cargó, pero no fue aceptada. El usuario decidió dejar su sustitución pendiente. No se validó sentimiento ni chat en vivo.
2. **Revisión visual**: el intento de conectar el navegador devolvió `The browser access host is unavailable` y no enumeró navegadores. No se capturaron pantallas ni se validaron visualmente breakpoints, teclado, contraste, tema oscuro o comportamiento en un teléfono.
3. **Publicación**: no se registró ni desplegó un servicio externo. El proyecto utiliza Flask/Waitress; el runtime del hosting de Sites es Workers y requiere una migración para ejecutar un backend equivalente. El código y el arranque local quedan preparados para revisión.

## Próxima aceptación

- Sustituir la clave en `.env`, reiniciar y probar una pregunta sobre pantalla, una de conceptos, una fuera de tema y una solicitud de recomendación de inversión; verificar las fuentes citadas y el rechazo adecuado.
- Solicitar sentimiento real en un activo y comprobar texto, persistencia y estado de errores.
- Abrir landing, app y chat a 375, 768 y 1440 px; comprobar navegación, tablas con desplazamiento local, foco, zoom, teclado y ausencia de desbordamiento general.
- Recorrer registro → añadir activo → panorama → detalle → fuente → CSV → chat → cerrar sesión.
- Antes de publicación comercial, revisar licencias de datos, HTTPS, secretos, recuperación de cuentas, backups, monitorización y dimensionamiento.
