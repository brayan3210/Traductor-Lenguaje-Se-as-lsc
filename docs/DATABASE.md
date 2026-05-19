# Guía completa de la base de datos — Señas Co

> Esta guía explica **paso a paso** cómo se configura la base de datos del traductor LSC, tanto en local (XAMPP) como en producción. Está escrita para que entiendas qué pasa por debajo, no solo qué comando ejecutar.

---

## Tabla de contenidos

1. [Idea general — ¿cómo funciona?](#1-idea-general--cómo-funciona)
2. [Las 5 tablas, una por una](#2-las-5-tablas-una-por-una)
3. [Setup local con XAMPP (desarrollo)](#3-setup-local-con-xampp-desarrollo)
4. [Si alguien clona el repo desde GitHub](#4-si-alguien-clona-el-repo-desde-github)
5. [Despliegue en producción](#5-despliegue-en-producción)
6. [Actualizar el seed más adelante](#6-actualizar-el-seed-más-adelante)
7. [Backups y restauración](#7-backups-y-restauración)
8. [Preguntas frecuentes](#8-preguntas-frecuentes)
9. [Solución de problemas](#9-solución-de-problemas)

---

## 1. Idea general — ¿cómo funciona?

La pregunta más común es **"¿tengo que exportar la BD desde phpMyAdmin y subirla?"**. La respuesta corta es: **no**. El repositorio ya contiene todo lo necesario para reconstruir la base de datos desde cero.

### El concepto clave

En este proyecto, la BD **no se sube** como un archivo binario. Lo que se versiona en GitHub son **dos archivos `.sql` que son código** (texto):

| Archivo | Qué hace |
| ------- | -------- |
| `database/schema.sql` | Las **instrucciones** para crear la BD y las 5 tablas vacías |
| `database/seed_data.sql` | Los **datos iniciales** del diccionario (las ~387 señas) |

Y luego hay un script Python que ejecuta esos dos `.sql` contra tu MySQL:

| Archivo | Qué hace |
| ------- | -------- |
| `database/init_db.py` | Lee `schema.sql` + `seed_data.sql` y los aplica contra el MySQL que esté configurado en tu `.env` |

> **Analogía**: imagina que en lugar de regalarte una caja de Lego ya armada (que sería un dump SQL), te doy el manual de instrucciones (los `.sql`) y un brazo robótico (`init_db.py`) que arma la caja por ti. El manual viaja por GitHub; el robot lo ejecutas en tu computador.

### Por qué se hace así (y no con phpMyAdmin)

- **Versionable**: cada cambio en el diccionario queda en el historial de git. Puedes ver quién agregó "vida" y cuándo.
- **Reproducible**: cualquier persona que clone el repo obtiene exactamente la misma BD, sin importar el sistema operativo.
- **Sin datos sensibles**: el seed solo contiene el diccionario, no usuarios reales ni contraseñas.
- **Automatizable**: en producción no hay UI gráfica como phpMyAdmin; todo tiene que ser scripts.

---

## 2. Las 5 tablas, una por una

Cuando ejecutas `init_db.py` se crean **5 tablas** en la BD `traductor_lsc`. Solo **una** trae datos del seed; las otras 4 nacen vacías y se llenan con el uso real de la aplicación.

### Resumen visual

```
┌────────────────────────────────────────────────────────┐
│                  BD: traductor_lsc                     │
├────────────────────────────────────────────────────────┤
│  senas                    [387 filas precargadas]      │
│  ──────                                                │
│  Diccionario completo. La ÚNICA tabla que viaja con    │
│  datos en el seed.                                     │
├────────────────────────────────────────────────────────┤
│  usuarios                 [vacía al inicio]            │
│  ─────────                                             │
│  Se llena cuando alguien se registra.                  │
├────────────────────────────────────────────────────────┤
│  recovery_codes           [vacía al inicio]            │
│  ────────────────                                      │
│  Códigos de recuperación de 2FA. Una fila por código   │
│  generado.                                             │
├────────────────────────────────────────────────────────┤
│  password_reset_tokens    [vacía al inicio]            │
│  ──────────────────────                                │
│  Tokens de "olvidé mi contraseña". Expiran solos.      │
├────────────────────────────────────────────────────────┤
│  historial                [vacía al inicio]            │
│  ──────────                                            │
│  Cada traducción que hace un usuario queda registrada  │
│  para estadísticas.                                    │
└────────────────────────────────────────────────────────┘
```

### Detalle de cada tabla

#### `senas` — el diccionario LSC

La única que tiene datos cargados desde el seed.

| Columna | Tipo | Para qué sirve |
| ------- | ---- | -------------- |
| `id` | INT auto-incremental | Identificador único |
| `palabra` | VARCHAR(120) UNIQUE | La clave canónica: `vida`, `hola`, `papa_comida` |
| `gif_url` | VARCHAR(255) | Ruta declarada al video: `/static/gifs/palabras/vida.gif` |
| `tipo` | ENUM | `letra` / `numero` / `palabra` / `frase` |
| `categoria` | VARCHAR(50) | `saludos`, `comida`, `emociones`, etc. |
| `descripcion` | VARCHAR(255) | Texto humano que aparece en el diccionario |
| `activo` | TINYINT(1) | `1` si se muestra, `0` para desactivar sin borrar |
| `created_at` / `updated_at` | DATETIME | Auditoría |

> **Detalle técnico importante**: la columna `gif_url` siempre dice `.gif`, pero el archivo real en disco puede ser `.mp4` o `.m4v`. El servicio `media_resolver.py` resuelve esto al vuelo, por eso no tienes que actualizar la BD cada vez que cambias un video.

#### `usuarios` — cuentas de usuario

| Columna | Tipo | Para qué sirve |
| ------- | ---- | -------------- |
| `id` | INT | Identificador del usuario |
| `nombres`, `apellidos` | VARCHAR(80) | Nombre real |
| `email` | VARCHAR(120) UNIQUE | Identidad de login |
| `password_hash` | VARCHAR(255) | bcrypt hash de la contraseña (nunca texto plano) |
| `totp_secret` | VARCHAR(64) NULL | Secreto del 2FA si lo activó |
| `totp_enabled` | TINYINT(1) | 1 si 2FA está activo |
| `recovery_file_hash` | VARCHAR(255) NULL | Hash del archivo de recuperación |
| `google_id` | VARCHAR(64) NULL | ID de Google si entró con OAuth |
| `email_verified` | TINYINT(1) | 1 si verificó su correo |
| `created_at` / `updated_at` | DATETIME | Auditoría |

#### `recovery_codes` — códigos de recuperación 2FA

| Columna | Tipo | Para qué sirve |
| ------- | ---- | -------------- |
| `id` | INT | |
| `usuario_id` | INT FK | A qué usuario pertenece |
| `code_hash` | VARCHAR(255) | Hash del código (los códigos solo se ven una vez) |
| `usado` | TINYINT(1) | 1 si ya se usó (no se puede volver a usar) |
| `created_at` / `used_at` | DATETIME | |

#### `password_reset_tokens` — tokens de "olvidé contraseña"

| Columna | Tipo | Para qué sirve |
| ------- | ---- | -------------- |
| `id` | INT | |
| `usuario_id` | INT FK | A qué usuario pertenece |
| `token_hash` | VARCHAR(255) | Hash del token enviado por email |
| `expira_en` | DATETIME | Cuándo deja de valer |
| `usado` | TINYINT(1) | 1 si ya se usó |
| `created_at` | DATETIME | |

#### `historial` — log de traducciones

| Columna | Tipo | Para qué sirve |
| ------- | ---- | -------------- |
| `id` | INT | |
| `texto_original` | TEXT | Lo que escribió el usuario |
| `tokens_json` | TEXT | Las señas devueltas, en JSON |
| `total_senas` | INT | Cuántas señas se mostraron |
| `no_encontradas` | INT | Cuántas palabras no tuvieron seña |
| `ip_cliente` | VARCHAR(45) | IP del usuario (auditoría) |
| `created_at` | DATETIME | Cuándo se tradujo |

---

## 3. Setup local con XAMPP (desarrollo)

Pasos para que en tu máquina puedas correr la app de cero.

### 3.1 Tener MySQL corriendo

Abre el **XAMPP Control Panel** y arranca el módulo **MySQL** (botón "Start"). Espera a que el indicador se ponga verde.

> Si MySQL no arranca: probablemente otro proceso está usando el puerto 3306. En el botón "Config" → `my.ini` puedes cambiar el puerto, o cierra el otro proceso desde Servicios de Windows.

### 3.2 Configurar el `.env`

En la raíz del proyecto, copia la plantilla:

```powershell
copy .env.example .env
```

Edita las variables de BD según tu instalación de XAMPP. El default de XAMPP es:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=traductor_lsc
```

> Si pusiste contraseña al `root` de XAMPP, pónla en `DB_PASSWORD`.

### 3.3 Activar el entorno virtual

```powershell
venv\Scripts\Activate.ps1
```

Si todavía no has creado el `venv`:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download es_core_news_md
```

### 3.4 Crear la BD + tablas + cargar diccionario

**Un solo comando**:

```powershell
python -m database.init_db
```

Esto va a:

1. Conectarse a MySQL con las credenciales del `.env`.
2. Ejecutar `database/schema.sql`: `CREATE DATABASE IF NOT EXISTS traductor_lsc` + crear las 5 tablas.
3. Ejecutar `database/seed_data.sql`: `TRUNCATE TABLE senas` + insertar las 387 señas.
4. Imprimir un resumen con el conteo por categoría.

Salida esperada:

```
2026-05-19 13:00:00 [INFO] Aplicando esquema en traductor_lsc...
2026-05-19 13:00:00 [INFO] [schema] 8 sentencias ejecutadas
2026-05-19 13:00:01 [INFO] Cargando datos iniciales...
2026-05-19 13:00:02 [INFO] [seed] 31 sentencias ejecutadas

=== Diccionario cargado ===
  adjetivos       52
  animales         2
  cantidades       2
  colores          9
  comida          36
  ...
  TOTAL          387
```

### 3.5 Verificar desde phpMyAdmin (opcional)

Abre <http://localhost/phpmyadmin>. En la lista de la izquierda debe aparecer **`traductor_lsc`**. Click → debes ver las 5 tablas (senas, usuarios, recovery_codes, password_reset_tokens, historial). Click en `senas` → "Examinar" → deberías ver las 387 filas.

### 3.6 Levantar Flask

```powershell
venv\Scripts\python.exe app.py
```

Abre <http://127.0.0.1:5000> en el navegador.

---

## 4. Si alguien clona el repo desde GitHub

Para alguien que entra al proyecto por primera vez (otro desarrollador, un evaluador, tú mismo en otra máquina):

```bash
# 1. Clonar
git clone https://github.com/brayan3210/Traductor-Lenguaje-Se-as-lsc.git
cd Traductor-Lenguaje-Se-as-lsc

# 2. Entorno virtual + dependencias
python -m venv venv
# (Windows PowerShell)
venv\Scripts\Activate.ps1
# (Linux/Mac)
source venv/bin/activate

pip install -r requirements.txt
python -m spacy download es_core_news_md

# 3. Configurar conexión a la BD
cp .env.example .env       # Linux/Mac
copy .env.example .env     # Windows
# Editar .env: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# 4. Tener MySQL/MariaDB corriendo (XAMPP, Docker, lo que sea)

# 5. Crear BD + cargar diccionario  ← ÉSTE es el paso clave
python -m database.init_db

# 6. Arrancar Flask
python app.py
```

**Eso es todo**. Quien clona NO necesita:

- ❌ Que tú le envíes un dump SQL por correo.
- ❌ Importar nada manualmente en phpMyAdmin.
- ❌ Compartirle tu base de datos local.

Todo lo que necesita está en el repositorio: las instrucciones (`.sql`) y el script que las ejecuta (`init_db.py`).

---

## 5. Despliegue en producción

En producción ya no tienes XAMPP — tienes un servidor real (un VPS, un servidor dedicado, o un servicio gestionado como Railway/Render/AWS). Pero el flujo es **idéntico** al de desarrollo: cambia solo el `.env`.

### 5.1 Opciones de hosting para MySQL en producción

| Opción | Cuándo usar | Pros | Contras |
| ------ | ----------- | ---- | ------- |
| **MySQL gestionado** (PlanetScale, Railway, RDS, DigitalOcean) | Recomendado | Backups automáticos, SSL, alta disponibilidad | Cuesta |
| **MySQL en el mismo VPS** | Proyectos pequeños / personal | Gratis (solo costo del VPS) | Tú haces backups, parches de seguridad |
| **Docker MySQL** | Self-hosting moderno | Reproducible | Configurar volumes correctamente |

### 5.2 Pasos genéricos

Asumiendo un VPS con Ubuntu, MySQL ya instalado y un usuario para la app:

#### a) Crear el usuario y la BD en MySQL

Te conectas al servidor por SSH y entras a MySQL como root **una sola vez** para crear un usuario dedicado (NUNCA uses `root` en producción):

```sql
CREATE DATABASE traductor_lsc CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'senasco'@'localhost' IDENTIFIED BY 'TU_PASSWORD_LARGO_Y_ALEATORIO';
GRANT ALL PRIVILEGES ON traductor_lsc.* TO 'senasco'@'localhost';
FLUSH PRIVILEGES;
```

> Para generar un password seguro: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

#### b) Subir el código

```bash
git clone https://github.com/brayan3210/Traductor-Lenguaje-Se-as-lsc.git /opt/senasco
cd /opt/senasco
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download es_core_news_md
```

#### c) Configurar el `.env` de producción

`/opt/senasco/.env`:

```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<generado_con_secrets.token_hex(32)>

DB_HOST=localhost
DB_PORT=3306
DB_USER=senasco
DB_PASSWORD=<el_password_que_creaste_en_a>
DB_NAME=traductor_lsc

APP_BASE_URL=https://tudominio.com
GOOGLE_REDIRECT_URI=https://tudominio.com/api/auth/google/callback
# ... resto igual que en .env.example
```

#### d) Crear las tablas y cargar el diccionario

**Exactamente el mismo comando que en local**:

```bash
python -m database.init_db
```

El script lee del `.env` de producción, así que se conecta a la BD remota, crea las 5 tablas y carga las 387 señas. Cero diferencia respecto a desarrollo.

#### e) Arrancar la app con Gunicorn

```bash
gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
```

Detrás de nginx con TLS. Ver la sección "Despliegue en producción" del `README.md` para el systemd unit completo.

### 5.3 ¿Y la BD local? ¿La debo migrar?

**Depende**:

- Si tu BD local es de **pruebas** (usuarios falsos, traducciones de testing) → **no migres nada**. En prod arrancas con BD limpia, los usuarios reales se registran solos.
- Si la BD local tiene **datos importantes** que querés llevar (ej. un usuario admin) → ver sección [Backups y restauración](#7-backups-y-restauración).

El diccionario (la tabla `senas`) **nunca se "migra"** entre entornos: siempre se carga desde el seed del repo. Eso garantiza que dev y prod tengan exactamente el mismo diccionario en cualquier momento.

---

## 6. Actualizar el seed más adelante

Cuando agregues señas nuevas (más videos, más vocabulario):

### Flujo de trabajo

1. Editar `database/seed_data.sql` para añadir las nuevas filas `INSERT`.
2. (Opcional) Agregar los videos a `static/gifs/palabras/`.
3. Recargar el diccionario en local:
   ```powershell
   python -m database.init_db --seed
   ```
   El flag `--seed` solo aplica el seed: hace `TRUNCATE TABLE senas` y reinserta. **No toca** las otras 4 tablas, así que tus usuarios y su historial no se borran.
4. Probar en local.
5. Commit + push a GitHub.
6. En el servidor de producción:
   ```bash
   cd /opt/senasco
   git pull
   python -m database.init_db --seed
   ```

### Flags útiles de `init_db.py`

| Comando | Qué hace |
| ------- | -------- |
| `python -m database.init_db` | Schema + seed + verify (todo desde cero) |
| `python -m database.init_db --schema` | Solo crea tablas vacías |
| `python -m database.init_db --seed` | Solo recarga el diccionario |
| `python -m database.init_db --verify` | Solo imprime el resumen de conteos |

---

## 7. Backups y restauración

### Backup periódico (producción)

Cron diario que guarda un dump comprimido:

```bash
# /etc/cron.d/senasco-backup
0 3 * * *  senasco  /usr/bin/mysqldump -u senasco -p<PASSWORD> traductor_lsc | gzip > /var/backups/senasco-$(date +\%F).sql.gz
```

> Mejor aún: usar el servicio de backups del proveedor (RDS Snapshots, DO Managed Database backups, etc.).

### Backup manual desde local

```powershell
# Windows / XAMPP
"C:\xampp\mysql\bin\mysqldump.exe" -u root traductor_lsc > backup.sql

# Linux / Mac
mysqldump -u root traductor_lsc > backup.sql
```

### Restaurar un backup

```powershell
# 1. Borrar la BD actual (opcional)
mysql -u root -e "DROP DATABASE IF EXISTS traductor_lsc"

# 2. Recrear vacía
mysql -u root -e "CREATE DATABASE traductor_lsc CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"

# 3. Importar
mysql -u root traductor_lsc < backup.sql
```

### Migrar usuarios de local a producción (caso raro)

Si necesitas llevarte unos pocos usuarios específicos:

```bash
mysqldump -u root traductor_lsc usuarios > usuarios_local.sql
scp usuarios_local.sql user@servidor:/tmp/
ssh user@servidor "mysql -u senasco -p traductor_lsc < /tmp/usuarios_local.sql"
```

> Antes de hacer esto en serio, asegúrate de que los `id` no choquen con usuarios ya creados en prod. Mejor exportar solo emails y crear nuevamente.

---

## 8. Preguntas frecuentes

### ¿Tengo que exportar la BD de phpMyAdmin para subirla a GitHub?

**No.** El diccionario ya está en `database/seed_data.sql` (texto plano, versionado). Las otras 4 tablas nacen vacías en cada entorno: los usuarios y el historial son específicos de cada instalación.

### Si edito el seed, ¿los usuarios se borran?

**No**, mientras uses `python -m database.init_db --seed`. Ese flag solo toca la tabla `senas`. Si corres `python -m database.init_db` (sin flags) sí se aplica el schema completo, lo cual incluye `DROP TABLE IF EXISTS senas;` pero las otras tablas usan `CREATE TABLE IF NOT EXISTS`, así que también sobreviven.

### ¿Puedo usar MariaDB en lugar de MySQL?

**Sí**. El esquema es 100% compatible con MariaDB 10.5+. XAMPP de hecho trae MariaDB por defecto en versiones recientes.

### ¿Y si quiero PostgreSQL?

Habría que adaptar el `schema.sql` (sintaxis ligeramente distinta) y cambiar `pymysql` por `psycopg2` en `database/connection.py`. No es trivial, pero tampoco enorme.

### ¿Por qué el seed empieza con `TRUNCATE TABLE senas`?

Para que `init_db.py --seed` sea **idempotente**: lo puedes correr 50 veces y siempre quedas con el mismo estado, sin duplicar señas.

### ¿Cómo agrego un seed adicional sin tocar el principal?

Usa el patrón de `database/seed_sustantivos_p0.sql`: archivo aparte con `INSERT IGNORE` (no rompe si ya existe la palabra) y lo ejecutas manualmente:

```powershell
"C:\xampp\mysql\bin\mysql.exe" -u root traductor_lsc < database/mi_patch.sql
```

### ¿Cuánto pesa la BD en disco?

Las 387 señas + esquema = **~150 KB** sin contar índices. Insignificante. Lo pesado son los **videos** (`static/gifs/`), no la BD.

---

## 9. Solución de problemas

### `ModuleNotFoundError: No module named 'pymysql'`

No activaste el venv o no instalaste dependencias:
```powershell
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### `pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")`

MySQL no está corriendo. Abre XAMPP Control Panel y arranca MySQL.

### `pymysql.err.OperationalError: (1045, "Access denied for user 'root'@'localhost'")`

La contraseña del `.env` no coincide. En XAMPP default, `DB_PASSWORD=` (vacío). Si pusiste contraseña, ajústalo.

### `pymysql.err.ProgrammingError: (1146, "Table 'traductor_lsc.senas' doesn't exist")`

Olvidaste correr `init_db.py`. Hazlo:
```powershell
python -m database.init_db
```

### Después de cambiar el seed no veo los cambios en la app

Dos posibles causas:

1. **No recargaste la BD**:
   ```powershell
   python -m database.init_db --seed
   ```
2. **No reiniciaste Flask**: Ctrl+C en su terminal y arráncalo de nuevo.

Y en el navegador, **Ctrl+Shift+R** para forzar refresh sin caché.

### En producción, `init_db` se queda colgado

Probablemente el firewall del servidor de BD no acepta conexiones desde tu IP. Si la BD está en otra máquina, abre el puerto 3306 (o el que uses) para la IP del servidor de la app, **NUNCA al mundo entero**.

### "Conexión SSL requerida" al usar BD gestionada

Algunos proveedores (PlanetScale, AWS RDS con SSL forzado) requieren TLS. Edita `database/connection.py` para pasar `ssl={'ca': '/ruta/al/ca.pem'}` al `pymysql.connect()`.

---

## Apéndice — Archivos relevantes

```
database/
├── connection.py            # Pool de conexiones PyMySQL (singleton)
├── init_db.py               # Script CLI que ejecuta los .sql
├── schema.sql               # DDL: CREATE DATABASE + 5 CREATE TABLE
├── seed_data.sql            # Diccionario completo (~387 INSERTs)
└── seed_sustantivos_p0.sql  # Patch idempotente con INSERT IGNORE

config/
└── settings.py              # Lee DB_HOST, DB_USER, ... del .env

.env                          # No commiteado. Credenciales reales.
.env.example                  # Plantilla pública (DB_PASSWORD vacío).
```
