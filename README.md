<div align="center">

# Señas Co — Traductor de Lenguaje de Señas Colombiano (LSC)

**Plataforma web que traduce texto en español a Lengua de Señas Colombiana, con un diccionario visual, un asistente IA local y autenticación segura con 2FA.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![spaCy](https://img.shields.io/badge/spaCy-3.7.5-09A3D5?logo=spacy&logoColor=white)](https://spacy.io/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Gunicorn](https://img.shields.io/badge/Gunicorn-22.0-499848?logo=gunicorn&logoColor=white)](https://gunicorn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Tabla de contenidos

1. [Descripción](#descripción)
2. [Características](#características)
3. [Stack tecnológico](#stack-tecnológico)
4. [Arquitectura](#arquitectura)
5. [Estructura del proyecto](#estructura-del-proyecto)
6. [Requisitos previos](#requisitos-previos)
7. [Instalación paso a paso](#instalación-paso-a-paso)
8. [Configuración (`.env`)](#configuración-env)
9. [Base de datos](#base-de-datos)
10. [Ejecución](#ejecución)
11. [API REST](#api-rest)
12. [Despliegue en producción](#despliegue-en-producción)
13. [Roadmap](#roadmap)
14. [Contribuir](#contribuir)
15. [Licencia](#licencia)
16. [Autor](#autor)

---

## Descripción

**Señas Co** es una aplicación web full-stack pensada para **acercar el español escrito a la comunidad sorda colombiana**. El sistema toma una frase en español, la procesa con NLP (lematización, manejo de verbos, sinónimos, marcadores LSC) y devuelve la **secuencia de videos/GIFs** correspondientes en Lengua de Señas Colombiana, respetando la gramática y los marcadores propios de la LSC.

Además del traductor, la plataforma incluye:

- Un **diccionario visual** navegable por categorías (letras, números, palabras, frases).
- Un **asistente conversacional con IA local** (GPT4All) para resolver dudas sobre la LSC sin enviar datos a terceros.
- Un sistema completo de **cuentas de usuario** con verificación por email, login con Google, **doble factor (TOTP)** y recuperación de contraseña.

> El objetivo es ofrecer una herramienta gratuita, accesible y respetuosa con los datos del usuario, que pueda usarse tanto en aulas como en entornos personales.

---

## Características

- **Traducción texto → señas** con pipeline NLP basado en `spaCy` (`es_core_news_md`).
- **Diccionario visual** con más de 80 entradas iniciales (letras del alfabeto, números, vocabulario común y frases de cortesía).
- **Asistente IA local** ejecutado en el propio servidor mediante `gpt4all` (sin telemetría externa).
- **Autenticación robusta**:
  - Registro con verificación de correo (SMTP).
  - Login con Google OAuth 2.0 (`Authlib`).
  - Segundo factor TOTP (compatible con Google Authenticator / Authy) mediante `pyotp` + QR.
  - Códigos de recuperación de un solo uso.
  - Reset de contraseña con tokens firmados y expiración.
- **API REST** documentada en `routes/api.py` (traducir, diccionario, estadísticas, salud, auth, OAuth).
- **Frontend responsivo** servido directamente por Flask con CSS y JS planos (sin build step).
- **Persistencia** sobre MySQL/MariaDB con esquema versionado y scripts de seed.
- **Pool de conexiones** propio (`database/connection.py`) y `teardown` por request.
- **Listo para producción** con `gunicorn` y configuración separada (`DevelopmentConfig` / `ProductionConfig`).

---

## Stack tecnológico

| Capa             | Tecnología                                         |
| ---------------- | -------------------------------------------------- |
| Lenguaje         | Python 3.10+                                       |
| Framework web    | Flask 3.0 + Flask-CORS                             |
| NLP              | spaCy 3.7 (`es_core_news_md`)                      |
| Base de datos    | MySQL 8 / MariaDB 10 (probado con XAMPP)           |
| Driver SQL       | PyMySQL 1.1                                        |
| Auth / Seguridad | `cryptography`, `pyotp`, `qrcode`, `Authlib`       |
| LLM local        | `gpt4all` (Meta-Llama-3-8B Q4 por defecto)         |
| Servidor WSGI    | Gunicorn 22 (Linux) / `flask run` (Windows dev)    |
| Frontend         | HTML5, CSS3, JavaScript vanilla, Jinja2            |

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│                          Navegador del usuario                   │
│   (Jinja2 templates · CSS · JS vanilla · MediaPlayer HTML5)      │
└───────────────────────────────┬──────────────────────────────────┘
                                │  HTTP / fetch
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Flask App (app.py)                          │
│  ┌──────────────┐   ┌──────────────────────────────────────────┐ │
│  │  Blueprints  │   │              Services                    │ │
│  │  main · api  │──▶│  nlp · traductor · auth · totp · email   │ │
│  └──────────────┘   │  google_oauth · chat (LLM) · media       │ │
│                     └─────────────────┬────────────────────────┘ │
│                                       │                          │
│                                       ▼                          │
│                     ┌──────────────────────────────────────┐     │
│                     │            Repositories              │     │
│                     │  Diccionario · Usuario · Recovery    │     │
│                     └─────────────────┬────────────────────┘     │
└───────────────────────────────────────┼──────────────────────────┘
                                        ▼
                       ┌────────────────────────────────┐
                       │   MySQL / MariaDB (XAMPP)      │
                       │   senas · usuarios · historial │
                       └────────────────────────────────┘
```

El pipeline de traducción funciona así:

1. **Sanitización** del texto recibido (`MAX_TEXTO_LEN = 2000`).
2. **NLP** con spaCy → tokens, lemas y POS.
3. **Reglas LSC**: lematización de verbos, sustitución de sinónimos, eliminación de artículos y marcadores temporales (`marcadores_lsc.py`).
4. **Resolución de media**: para cada token, se busca en el diccionario una seña activa y se devuelve su URL.
5. **Historial**: cada petición queda registrada en la tabla `historial` para estadísticas y auditoría.

---

## Estructura del proyecto

```
TraductorLSC/
├── app.py                      # Factory Flask (create_app)
├── requirements.txt            # Dependencias congeladas
├── .env.example                # Plantilla de variables de entorno
│
├── config/
│   └── settings.py             # Config base / Development / Production
│
├── database/
│   ├── connection.py           # Pool PyMySQL
│   ├── init_db.py              # CLI: aplicar esquema + seed
│   ├── schema.sql              # DDL completo
│   ├── seed_data.sql           # Diccionario base
│   └── seed_sustantivos_p0.sql # Sustantivos prioridad P0
│
├── models/                     # Repositorios (acceso a datos)
│   ├── diccionario.py
│   ├── usuario.py
│   └── recovery.py
│
├── routes/                     # Blueprints HTTP
│   ├── main.py                 # Vistas HTML
│   └── api.py                  # API REST JSON
│
├── services/                   # Lógica de negocio
│   ├── nlp_service.py
│   ├── traductor_service.py
│   ├── lematizador_verbos.py
│   ├── sinonimos.py
│   ├── marcadores_lsc.py
│   ├── frases_largas.py
│   ├── media_resolver.py
│   ├── auth_service.py
│   ├── totp_service.py
│   ├── email_service.py
│   ├── google_oauth_service.py
│   └── chat_service.py         # GPT4All
│
├── templates/                  # Jinja2 (translator, diccionario, auth…)
├── static/
│   ├── css/                    # Hojas de estilo por vista
│   ├── js/                     # Scripts por vista
│   └── gifs/                   # Media de señas (letras y palabras)
│
└── docs/                       # Documentación técnica interna
    ├── AUTH.md                 # Detalle del módulo de autenticación
    ├── PROJECT_CONTEXT.md      # Contexto de diseño y decisiones
    └── GIFS_CHECKLIST.md       # Inventario de señas disponibles
```

---

## Requisitos previos

| Herramienta                  | Versión mínima | Notas                                                        |
| ---------------------------- | -------------- | ------------------------------------------------------------ |
| **Python**                   | 3.10           | Recomendado 3.11                                             |
| **MySQL / MariaDB**          | 8.0 / 10.5     | XAMPP 8.x funciona out-of-the-box                            |
| **pip**                      | 23+            | Incluido con Python                                          |
| **Git**                      | 2.40+          | Para clonar el repositorio                                   |
| **Modelo spaCy ES**          | —              | Se descarga en el paso de instalación                        |
| **Cuenta SMTP (opcional)**   | —              | Gmail App Password para verificación de correo y recuperación |
| **Google Cloud (opcional)**  | —              | Solo si activas login con Google                             |

---

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone https://github.com/brayan3210/Traductor-Lenguaje-Se-as-lsc.git
cd Traductor-Lenguaje-Se-as-lsc
```

### 2. Crear y activar el entorno virtual

**Windows · PowerShell**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Windows · CMD**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux / macOS**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar las dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Descargar el modelo de spaCy en español

```bash
python -m spacy download es_core_news_md
```

> Si tu equipo es modesto, puedes usar `es_core_news_sm` y ajustar `SPACY_MODEL` en el `.env`.

### 5. Configurar las variables de entorno

```bash
cp .env.example .env       # Linux / macOS
copy .env.example .env     # Windows
```

Edita el archivo `.env` siguiendo la sección [Configuración (`.env`)](#configuración-env).

### 6. Inicializar la base de datos

Con XAMPP/MySQL en marcha:

```bash
python -m database.init_db
```

Esto crea la BD, las tablas y carga el diccionario base. Para opciones avanzadas:

```bash
python -m database.init_db --schema   # solo crea tablas
python -m database.init_db --seed     # solo carga datos
python -m database.init_db --verify   # muestra el conteo por categoría
```

### 7. Levantar el servidor

```bash
python app.py
```

Abre [http://127.0.0.1:5000](http://127.0.0.1:5000) en tu navegador.

---

## Configuración (`.env`)

Plantilla con las variables soportadas:

```ini
# --- Flask ---
FLASK_APP=app.py
FLASK_ENV=development         # development | production
FLASK_DEBUG=True
SECRET_KEY=cambia-esta-clave-en-produccion

# --- MySQL ---
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=traductor_lsc

# --- NLP ---
SPACY_MODEL=es_core_news_md
MAX_TOKENS=80

# --- Servidor ---
HOST=0.0.0.0
PORT=5000

# --- SMTP (Gmail App Password) ---
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tucorreo@gmail.com
SMTP_APP_PASSWORD=xxxxxxxxxxxxxxxx
SMTP_FROM_NAME=Señas Co
APP_BASE_URL=http://127.0.0.1:5000

# --- 2FA ---
TOTP_ISSUER=Señas Co

# --- Google OAuth (opcional) ---
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/api/auth/google/callback
```

> **Importante**: `.env` está incluido en `.gitignore`. **Nunca** lo subas al repositorio. En producción, genera un `SECRET_KEY` aleatorio con `python -c "import secrets; print(secrets.token_hex(32))"`.

---

## Base de datos

El esquema vive en [`database/schema.sql`](database/schema.sql) y declara cinco tablas:

| Tabla                   | Propósito                                            |
| ----------------------- | ---------------------------------------------------- |
| `senas`                 | Diccionario principal de señas (letra, número, palabra, frase) |
| `usuarios`              | Cuentas con soporte para TOTP y Google OAuth         |
| `recovery_codes`        | Códigos de recuperación de un solo uso               |
| `password_reset_tokens` | Tokens de reset con expiración                       |
| `historial`             | Auditoría de traducciones (anonimizable)             |

Todos los campos usan `utf8mb4` para soportar caracteres especiales y emojis sin sorpresas. La carga de seed pobla `senas` con las letras del alfabeto, números 0–10 y vocabulario base; ver [`docs/GIFS_CHECKLIST.md`](docs/GIFS_CHECKLIST.md).

---

## Ejecución

### Modo desarrollo (con recarga automática)

```bash
flask --app app run --debug --host 0.0.0.0 --port 5000
```

### Modo producción (Linux con Gunicorn)

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

| Parámetro | Significado                                  |
| --------- | -------------------------------------------- |
| `-w 4`    | 4 workers (regla: `2 × núcleos + 1`)         |
| `-b`      | Dirección y puerto de escucha                |
| `app:create_app()` | Factory que devuelve la app Flask    |

Detrás de un reverse proxy (nginx, Caddy) recuerda enviar `X-Forwarded-For` y `X-Forwarded-Proto`.

---

## API REST

Resumen de endpoints (prefijo `/api`):

| Método | Ruta                              | Descripción                                       |
| ------ | --------------------------------- | ------------------------------------------------- |
| POST   | `/api/traducir`                   | Traduce un texto a secuencia de señas             |
| GET    | `/api/diccionario`                | Lista entradas con filtros opcionales             |
| GET    | `/api/diccionario/buscar`         | Búsqueda por fragmento                            |
| GET    | `/api/diccionario/categorias`     | Lista categorías disponibles                      |
| GET    | `/api/stats`                      | Estadísticas de cobertura                         |
| GET    | `/api/historial`                  | Últimas traducciones                              |
| GET    | `/api/salud`                      | Health check (DB + NLP)                           |
| POST   | `/api/auth/registro`              | Crear cuenta                                      |
| POST   | `/api/auth/login`                 | Login con contraseña                              |
| POST   | `/api/auth/2fa/verificar`         | Verificar código TOTP                             |
| POST   | `/api/auth/recuperar`             | Enviar email de recuperación                      |
| POST   | `/api/auth/reset-password`        | Restablecer contraseña con token                  |
| GET    | `/api/auth/google`                | Iniciar flujo OAuth                               |
| GET    | `/api/auth/google/callback`       | Callback de Google                                |

**Ejemplo: traducir un texto**

```bash
curl -X POST http://127.0.0.1:5000/api/traducir \
  -H "Content-Type: application/json" \
  -d '{"texto": "hola buenos días"}'
```

Respuesta:

```json
{
  "success": true,
  "texto_original": "hola buenos días",
  "tokens": [
    {"palabra": "hola",        "tipo": "palabra", "gif_url": "/static/gifs/palabras/hola.mp4"},
    {"palabra": "buenos_dias", "tipo": "frase",   "gif_url": "/static/gifs/palabras/buenos_dias.mp4"}
  ],
  "total_senas": 2,
  "no_encontradas": 0
}
```

---

## Despliegue en producción

Recomendaciones para un despliegue real:

1. **Servidor**: Ubuntu 22.04 LTS o similar.
2. **Reverse proxy**: nginx o Caddy delante de Gunicorn con TLS (Let's Encrypt).
3. **Base de datos**: MySQL/MariaDB con usuario dedicado, **no `root`**, y backups automáticos.
4. **Variables de entorno**: gestiona el `.env` con un secret manager o `systemd` `EnvironmentFile=`.
5. **Servicio systemd** de ejemplo:

   ```ini
   [Unit]
   Description=Senas Co (Flask + Gunicorn)
   After=network.target

   [Service]
   User=senasco
   WorkingDirectory=/opt/senasco
   EnvironmentFile=/etc/senasco.env
   ExecStart=/opt/senasco/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

6. **Cabeceras de seguridad**: añade `Strict-Transport-Security`, `Content-Security-Policy` y `X-Content-Type-Options` desde el proxy.
7. **Modelo GPT4All**: si activas el chat, considera ejecutar la inferencia en una máquina aparte con GPU/CPU dedicada.

---

## Roadmap

- [ ] Tests automatizados (pytest + factories)
- [ ] Cobertura del diccionario para todas las categorías P0/P1
- [ ] Modo invitado para el traductor
- [ ] PWA con caché offline de los videos más usados
- [ ] Métricas y panel de observabilidad
- [ ] Internacionalización del frontend

---

## Contribuir

¡Las contribuciones son bienvenidas! Para colaborar:

1. Haz un fork del proyecto.
2. Crea una rama: `git checkout -b feature/mi-mejora`.
3. Realiza tus cambios siguiendo el estilo del repo (Black + isort).
4. Asegúrate de que `python -m database.init_db --verify` siga funcionando.
5. Abre un Pull Request explicando el "qué" y el "por qué".

Si encuentras un bug o quieres proponer una nueva seña al diccionario, abre un **Issue** describiendo el caso.

---

## Licencia

Distribuido bajo licencia **MIT**. Consulta [`LICENSE`](LICENSE) para más información.

---

## Autor

**Brayan Cortés Leytón**
[brayancortesleyton@gmail.com](mailto:brayancortesleyton@gmail.com)
GitHub: [@brayan3210](https://github.com/brayan3210)

<div align="center">

Hecho con dedicación para acercar la **Lengua de Señas Colombiana** a más personas.

</div>
