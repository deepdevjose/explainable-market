# Limpieza de historial — 12 de noviembre de 2026

## Alcance

Repositorio: `deepdevjose/explainable-market`. Ramas publicadas: `main` y
`feat/multi-market-data-foundation`. La autorización expresa del propietario
permite sustituir su historia; los identificadores de commits anteriores cambian.
El checkout independiente de `ning-111/explainable_market` pertenece a otro remoto
y no se modifica ni se publica desde esta operación.

Se utilizó `git-filter-repo` con eliminación de datos sensibles en una copia privada:

- Eliminación histórica de `env (1).txt`, `data/`, bytecode Python, el PDF académico
  con credenciales antiguas y la captura de referencia heredada.
- Redacción de los valores secretos históricos conocidos que persistían en texto
  y mensajes, incluyendo el ejemplo de configuración. No se incluyen sus valores.
- Conservación de los cambios funcionales y de la aplicación actual; un solo commit
  de preparación pública agrupa la documentación y los controles nuevos.
- Copia de recuperación privada, con directorio 0700 y archivos de respaldo 0600,
  fuera del repositorio. No debe compartirse, sincronizarse públicamente ni subirse.

## Evidencia

Antes de actualizar la documentación final, se examinaron 215 versiones de archivos
de las dos ramas saneadas: sin rutas privadas, patrones de credenciales reconocidos
ni coincidencias con los secretos históricos y de servicio conocidos. El árbol
actual resultó idéntico al del commit de preparación antes de modificar estos
informes. Los únicos cambios posteriores describen el proceso de limpieza.

En un checkout separado de la versión saneada pasaron las 79 pruebas, Ruff, mypy
(23 archivos seleccionados) y el control del índice. Las bases y configuración
privada de la demo permanecen en su ubicación original. El saneamiento no supone
rotación de credenciales ni un despliegue nuevo.

## Colaboradores y límites

Volver a clonar el repositorio limpio es la opción más sencilla para colaboradores.
No fusionar ramas antiguas: pueden reintroducir el historial sensible. Preservar
antes cualquier trabajo local y aplicar solo los cambios revisados sobre la versión
nueva. No hacer push de la copia de recuperación ni de otro clon antiguo.

Cambiar referencias no garantiza la eliminación de cachés, forks o clones externos.
La revisión previa no encontró referencias remotas de pull requests, pero eso no
certifica que GitHub haya purgado todos los objetos antiguos. La comprobación
posterior al push confirmó HTTP 200 y la presencia de un valor sensible conocido
en una URL raw del historial anterior. No se guarda ni reproduce su contenido.
Por tanto, la eliminación de esa copia pública sigue pendiente: el propietario debe
solicitar a GitHub Support la purga según [el procedimiento oficial](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
El soporte puede exigir que el riesgo no sea mitigable únicamente revocando claves.
No se ha enviado una solicitud de soporte ni se han revocado claves de terceros.
Se preparó un borrador privado para soporte, fuera del repositorio. La limpieza de
las ramas no debe presentarse como eliminación completa de la exposición.

Las credenciales expuestas deben revocarse aunque ya no estén en las ramas.
Ver [SECURITY.md](../SECURITY.md). No se afirma que una búsqueda dirigida equivalga
a una auditoría de seguridad completa.
