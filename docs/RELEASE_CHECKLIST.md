# Revisión del repositorio antes de publicar

Esta revisión prepara el árbol y el índice para un commit público. No certifica la
seguridad absoluta del producto ni elimina exposiciones de commits anteriores.

## Alcance de la revisión del 12 de noviembre de 2026

- `.env.example` conserva únicamente campos de credenciales vacíos e incluye
  BigModel, DeepSeek y Twelve Data. La configuración privada del servicio no cambia.
- Bases, backups, claves, configuración local, registros, sesiones del navegador
  y capturas de pruebas están excluidos de Git y del contexto Docker.
- El PDF académico con credenciales antiguas y una imagen de referencia opaca se
  retiran del seguimiento. Permanecen en disco; no se borra el historial.
- El README presenta capacidades, límites, instalación local y documentos de
  operación, sin depender de un enlace temporal ni de la configuración del autor.
- MIT, OFL, contribuciones, conducta, política de seguridad y plantillas de GitHub
  conservan responsabilidades separadas de las licencias de datos financieros.
- El control de publicación revisa también el índice real de Git, no solo los
  archivos de trabajo. Los hallazgos muestran rutas y motivos, nunca los valores.

## Comandos de comprobación

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check .
.venv/bin/mypy
.venv/bin/bandit -q -r market_explained ai.py charts.py collector.py config.py db.py -ll
.venv/bin/pip-audit -r requirements.txt -r requirements-ml.txt
node --check static/app.js
.venv/bin/python scripts/check_repository_hygiene.py
# Después de seleccionar únicamente los cambios revisados:
.venv/bin/python scripts/check_repository_hygiene.py --staged
git diff --cached --check
git status --short
```

Las comprobaciones no sustituyen la lectura privada del diff y de cualquier nuevo
archivo binario. No publicar bases de datos como fixtures ni capturas con cuentas,
cookies o claves. Las pruebas externas y el despliegue requieren evidencia aparte.

### Resultados de esta revisión

| Comprobación local | Resultado |
| --- | --- |
| unittest, Python 3.12 | 79 pruebas aprobadas; sin llamadas externas |
| Ruff / mypy | Sin incidencias; mypy revisó 23 archivos seleccionados |
| Bandit, código de aplicación y scripts | Sin hallazgos de gravedad media/alta |
| pip-audit, dependencias de ejecución y ML | Sin vulnerabilidades conocidas en la resolución auditada |
| JavaScript / compilación Python | Sintaxis y compilación correctas |
| Enlaces locales de README, contribuciones, seguridad y este documento | Destinos existentes |
| Claves privadas actuales frente a blobs Git alcanzables | Sin coincidencias en la revisión dirigida |
| Secretos históricos conocidos frente a archivos publicables actuales | Sin coincidencias |

Los resultados locales no afirman que los jobs remotos de GitHub Actions ni un
build Docker hayan finalizado. No se cambiaron los procesos de la demo; el servicio
web permaneció activo. El estado de publicación se comprueba aparte con el índice.

## Pendiente fuera del commit

La revisión inicial encontró una clave de proveedor antigua, bases y secreto de
sesión de versiones anteriores y un PDF con credenciales de demostración. También
existía una copia de la clave en un ejemplo de configuración histórico. Después
se autorizó y preparó la limpieza de ambas ramas publicadas, preservando el árbol
actual y validándolo en un checkout independiente. Véase
[el informe de limpieza](HISTORY_CLEANUP.md). No se publican valores sensibles.

Las credenciales actuales del servicio privado y los secretos históricos conocidos
no coincidieron con los blobs de la historia saneada. La revocación de claves
antiguas, la revisión de contraseñas reutilizadas y la posible purga de cachés en
GitHub siguen pendientes. La sustitución del historial es una excepción autorizada
expresamente por el propietario; se conserva recuperación privada.

La aplicación pública sigue siendo una demo servida por la laptop. Ni este commit
ni una ejecución de CI equivalen a un despliegue cloud permanente. Las restricciones
de visualización de Twelve Data permanecen activas.
