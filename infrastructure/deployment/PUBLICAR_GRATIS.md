# Publicar la aplicación completa sin depender de la laptop

Estado: configuración preparada, **sitio todavía no desplegado**. Hace falta una
cuenta de hosting y una máquina accesible. No se crea ningún recurso al ejecutar
las pruebas ni al consultar este documento.

## Qué puede alojar GitHub

GitHub conserva el código y ejecuta validaciones. GitHub Pages aloja HTML/CSS/JS;
no ejecuta Flask, SQLite ni el worker. No se sustituye la aplicación por una captura,
una página informativa o una versión sin cuentas para aparentar un despliegue.

La publicación completa necesita: GitHub → máquina Linux externa → HTTPS público.
Opcionalmente, una página de GitHub Pages podrá enlazar la URL final cuando exista.

## Opción gratuita compatible: Oracle Cloud Always Free

1. El propietario crea su cuenta en https://signup.cloud.oracle.com. Oracle solicita
   verificación de identidad con tarjeta; puede realizar una retención temporal.
   No compartas contraseña, tarjeta ni claves privadas en el chat o repositorio.
2. En la región de origen, buscar una instancia Ubuntu marcada **Always Free**.
   Usar una configuración dentro de las cuotas que la consola indique actualmente.
   Verificar también volumen de arranque, red y cualquier servicio adicional.
   No elegir una máquina paga ni basarse solo en los créditos de prueba de 30 días.
3. Si no hay capacidad gratuita, detenerse. No pasar a Pay As You Go para continuar.
   La disponibilidad gratuita no garantiza capacidad ni SLA y Oracle puede recuperar
   instancias consideradas inactivas según sus condiciones.
4. Crear la VM con una clave SSH propia, IP pública y almacenamiento persistente.
   Autorizar SSH únicamente desde la IP del administrador; HTTP 80 y HTTPS 443
   deben poder recibirse desde Internet para acceso público y validación de TLS.
   Revisar tanto las reglas de red OCI como el firewall de Ubuntu. No exponer 5050.
5. Instalar Docker Engine y Compose siguiendo la documentación oficial de Ubuntu:
   https://docs.docker.com/engine/install/ubuntu/. No ejecutar scripts de terceros.

Documentación primaria consultada el 6 de noviembre de 2026:

- https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- https://www.oracle.com/cloud/free/faq/

Render Free no es equivalente para esta arquitectura: su filesystem es efímero,
no permite disco persistente gratuito y puede suspenderse por inactividad. Las
cuentas SQLite no deben depender de ese filesystem:
https://render.com/docs/free.

## Arranque en la VM (no en la laptop)

Estos pasos requieren que la rama validada esté publicada en GitHub. No clonar
main mientras todavía contenga la configuración antigua. Una vez publicada:

```bash
git clone --single-branch --branch feat/multi-market-data-foundation \
  https://github.com/deepdevjose/explainable-market.git
cd explainable-market
```

Elegir un hostname que apunte a la IP de la VM. Si no tienes dominio, sslip.io o
nip.io permiten un nombre basado en tu IP sin comprar un dominio; dependen de un
servicio DNS externo. Ejemplo documental: `203.0.113.10.sslip.io` (IP reservada para
documentación, **no usar literalmente**). Sustituirla por la IP pública real.

https://sslip.io/ documenta resolución y certificados TLS para estos nombres.

Crear una configuración privada **una sola vez**, usando el hostname real:

```bash
sudo python3 scripts/init_production.py --host TU_HOST_PUBLICO
sudo docker compose \
  --env-file /etc/market-explained/.env.production \
  -f infrastructure/deployment/compose.production.yaml config --quiet
sudo docker compose \
  --env-file /etc/market-explained/.env.production \
  -f infrastructure/deployment/compose.production.yaml up --build -d
```

El script genera SECRET_KEY en el servidor, con permisos 0600, fuera del repositorio.
No imprime su valor y se niega a reemplazar una configuración existente. El archivo
se pasa explícitamente a Docker, que inyecta variables de proceso; Flask no incorpora
ningún lector implícito de credenciales. DeepSeek es opcional y no se configura con
la credencial expuesta anteriormente.

El Compose de producción añade un proxy Caddy con HTTPS automático, el proceso
web, el worker de Binance y el colector diario. Publica únicamente 80/443. Mantiene
SQLite y los certificados en volúmenes persistentes, reinicia procesos tras fallos
y fija la IP del proxy que Waitress puede confiar. Si la subred 172.30.0.0/24 ya
está ocupada en la VM, cambiarla y mantener alineadas la IP del proxy y TRUSTED_PROXY.

Los volúmenes nuevos empiezan sin cuentas. Si necesitas trasladar cuentas existentes,
hacer una migración privada por SSH y backup consistente siguiendo
[DATA_OPERATIONS.md](../../docs/DATA_OPERATIONS.md). Nunca subir la base al repositorio
público. No mezclar archivos WAL entre bases ni usar `down -v`.

## Verificar que está publicada

```bash
sudo docker compose \
  --env-file /etc/market-explained/.env.production \
  -f infrastructure/deployment/compose.production.yaml ps
sudo docker compose \
  --env-file /etc/market-explained/.env.production \
  -f infrastructure/deployment/compose.production.yaml logs --tail=50 proxy web worker
curl --fail https://TU_HOST_PUBLICO/health
```

Comprobar desde otra conexión: landing, registro/login, lista persistente, mercados,
fuentes, CSV y timestamps/estado de Binance. No omitir verificaciones de certificado.
Reiniciar servicios y confirmar que una cuenta de prueba conserva su lista. Apagar
la laptop y abrir la URL desde otro dispositivo es la aceptación del requisito de
independencia. Solo entonces registrar la URL como desplegada.

La captura continua de trades hace crecer SQLite. Vigilar espacio libre, backups,
RAM y frescura antes de ampliar pares; este despliegue no borra historia de forma
automática para encajar en una cuota gratuita. Always Free tiene límites operativos.

## Actualizar desde GitHub

En la VM, obtener y revisar un commit validado de la rama antes de reconstruir:

```bash
git pull --ff-only
sudo docker compose \
  --env-file /etc/market-explained/.env.production \
  -f infrastructure/deployment/compose.production.yaml up --build -d
```

No se configura acceso SSH desde GitHub Actions ni se copian claves automáticamente.
La laptop no ejecuta la web ni el worker una vez iniciados en la VM. La configuración
preparada no equivale a una VM creada o un certificado emitido; aún deben verificarse.
