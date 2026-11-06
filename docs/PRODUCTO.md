# Qué estamos construyendo

Explainable Market ayuda a una persona que está aprendiendo o analizando el mercado a pasar de «el precio cambió» a «qué información tengo para entender ese cambio». Reúne activos, series diarias, titulares verificables y preguntas educativas en un espacio coherente.

## Lectura de los materiales

`Checkpoint2.pdf` define como núcleo una lista de seguimiento explicable, movimientos acompañados de noticias y una línea temporal por activo con reacciones a una, tres y siete sesiones. También identifica que la fuente original de datos es estática y que falta conectar proveedores financieros reales y DeepSeek.

La imagen suministrada explora una experiencia educativa ligera, con navegación simple, seguimiento y explicaciones. Sus porcentajes de pronóstico, escenarios y rendimiento de predictores no aportan un modelo validado ni una fuente operativa. No se convierten en cifras ni funcionalidades pretendidamente reales.

La petición actual amplía lo anterior con landing pública, adaptación completa a móvil, un lenguaje visual sobrio basado en Apple y Carbon y un asistente flotante contextual.

## Público y propuesta

El público inicial son estudiantes y personas que quieren interpretar información financiera. La tarea principal es elegir un activo, observar sus datos, abrir las noticias y plantear mejores preguntas. La app facilita comprensión y trazabilidad; no gestiona dinero ni ejecuta transacciones.

El producto permite revisar la hipótesis de que una noticia esté relacionada con un movimiento, manteniendo visible que la coincidencia temporal no demuestra una causa. La clasificación de sentimiento mide el tono del titular, no su efecto económico real.

## Recorrido principal

1. La landing presenta la propuesta y da acceso al mercado sin registro obligatorio.
2. El panorama reúne activos y permite seleccionar uno para ver su gráfica y noticias.
3. El detalle muestra períodos reales, origen de los precios, fechas, CSV y ventanas de reacción.
4. El usuario puede abrir cada artículo original y solicitar su clasificación con DeepSeek.
5. Una cuenta propia guarda la lista elegida y separa el historial del chat.
6. La bolita acompaña todas las pantallas. El usuario puede preguntar qué está viendo o aclarar un concepto.

## Decisiones para el MVP

| Decisión | Motivo |
| --- | --- |
| Mantener Flask y SQLite | Aprovechar la base existente y proporcionar un sistema ejecutable con persistencia, sin una migración de framework que no aporta valor inmediato. |
| Una base nueva para datos verificables | Conservar el archivo anterior y evitar mezclar precios generados con fuentes externas. |
| Cierres diarios con fuente y fecha | Ofrecer una integración verificable sin afirmar que existe un feed contratado en tiempo real. |
| Navegación pública; cuenta para guardar | Permitir explorar antes de registrarse y asociar los datos personales a un usuario real. |
| Español en interfaz y explicaciones | Seguir el idioma de la solicitud. Los titulares conservan el texto del proveedor. |
| Diseño Carbon con composición limpia | IBM Plex Sans local, tokens semánticos, azul de interacción, grises, tablas legibles y estados explícitos. |
| IA contextual desde el servidor | No confiar en precios o instrucciones que un cliente pudiera inventar al enviar una solicitud. |
| IA solicitada por el usuario | Evitar análisis de pago automáticos durante cada actualización de noticias. |

## Alcance implementado

Landing, panorama, cuentas, listas, búsqueda de activos, detalle por período, fuentes reales, noticias y filtros, exportación de cierres, ventanas completas de reacción, integración DeepSeek para chat y sentimiento, biblioteca y metodología, temas claro/oscuro y layouts responsive.

Los controles responsive y la lógica del cliente están implementados; requieren inspección visual final en un navegador disponible. DeepSeek requiere sustituir la credencial rechazada por el proveedor antes de poder validar respuestas reales.

## Evolución posterior

Los siguientes pasos de producto requieren decisiones y trabajo adicional: proveedor financiero contratado y con licencia, verificación y recuperación de cuentas, observabilidad y backups operativos, pruebas con usuarios, automatización RPA ante una fuente concreta y modelo predictivo si hay datos, metodología y evaluación para sostenerlo. La etiqueta de «análisis predictivo» del documento no se usa para fingir predicciones en el MVP.
