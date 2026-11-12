# Proveedores del asistente educativo

## Implementado

La integración mantiene las funciones públicas de `ai.py`, la validación JSON y
las restricciones educativas. Se selecciona un solo proveedor mediante variables
de entorno; no se envía una consulta a un segundo proveedor cuando el primero falla.

| Proveedor | Selección | Credencial privada | Modelo predeterminado |
| --- | --- | --- | --- |
| Zhipu / BigModel | `AI_PROVIDER=bigmodel` | `BIGMODEL_API_KEY` | `BIGMODEL_MODEL=glm-5.3-flash` |
| DeepSeek | `AI_PROVIDER=deepseek` | `DEEPSEEK_API_KEY` | `DEEPSEEK_MODEL=deepseek-flash` |

DeepSeek continúa siendo el valor predeterminado para instalaciones existentes.
La demo actual selecciona BigModel. Sus credenciales están fuera del repositorio,
en `~/.config/market-explained-demo/server.env`, con permisos 0600. Tras cambiar
esa configuración:

```bash
systemctl --user restart market-explained-demo-web
```

BigModel recibe solicitudes únicamente en su endpoint HTTPS oficial, con la clave
en Authorization. GLM-5.3-Flash requiere razonamiento activado: se usa
`thinking.type=enabled`, `reasoning_effort=low`, salida JSON y un presupuesto de
4096 tokens en las llamadas actuales. El tiempo de espera es 45 segundos y la
respuesta se limita a 2 MB. Solo se procesa el contenido final; `reasoning_content`
no se devuelve al navegador ni se guarda en el historial. DeepSeek conserva los
parámetros anteriores.

La interfaz identifica proveedor y modelo y avisa de que la consulta y su contexto
se envían al proveedor seleccionado. Las respuestas aceptadas del asistente siguen
el almacenamiento de mensajes existente; no se envían credenciales al cliente.
Los errores públicos no incluyen el cuerpo de error del proveedor ni sus datos
de cuenta. Una respuesta truncada o JSON inválido produce un error controlado.

Sin clave del proveedor seleccionado, el asistente ofrece la guía determinista
local ya existente. Con clave configurada pero rechazada, no sustituye una llamada
fallida por una respuesta local que pudiera confundirse con el modelo. La
clasificación de titulares requiere un proveedor válido. Las restricciones del
prompt y la validación de esquema reducen riesgos, pero no garantizan la exactitud
de una respuesta generativa.

La ingesta Binance/Yahoo/Nasdaq/Twelve Data y los modelos numéricos de pronóstico
son independientes del asistente. Una clave de IA no sustituye la de Twelve Data.
No se ha añadido una interfaz de carga de imágenes.

## Validado el 12 de noviembre de 2026

- La API oficial aceptó la credencial y respondió con `glm-5.3-flash` y JSON válido.
- El endpoint público `/api/chat` respondió HTTP 200 en español, inglés y chino
  simplificado mediante una sesión de invitado con CSRF y Origin válidos. Se borró
  únicamente el historial generado por esa sesión de prueba.
- El clasificador devolvió tres resultados válidos para tres titulares reales
  existentes. Esa prueba no escribió las clasificaciones en la base de noticias.
- Las 70 pruebas automatizadas pasaron sin llamar a servicios externos. Siete
  pruebas nuevas cubren contratos GLM/DeepSeek, selección explícita, claves
  ausentes, errores seguros, respuestas incompletas y validación de alcance/idioma.
- Ruff, mypy (22 archivos seleccionados), Bandit de gravedad media/alta,
  compilación Python y comprobación de sintaxis JavaScript pasaron.

Las pruebas reales verifican conectividad y formato, no precisión financiera ni
disponibilidad futura. No se verificó de nuevo la credencial antigua de DeepSeek.
Las claves compartidas por chat deben rotarse para una instalación duradera;
no deben copiarse a incidencias, documentación o commits.

## Referencias oficiales

- [API y autenticación BigModel](https://docs.bigmodel.cn/cn/api/introduction)
- [GLM-5.3-Flash](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash)
- [Parámetros GLM-5.3](https://docs.bigmodel.cn/cn/guide/models/text/glm-5.3)
- [Chat Completions DeepSeek](https://api-docs.deepseek.com/api/create-chat-completion/)
