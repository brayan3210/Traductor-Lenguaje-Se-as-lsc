# Sistema de autenticación — Señas Co

Documento técnico que explica **toda** la capa de autenticación: cómo está
construida, qué hace cada archivo, qué tablas crea, qué endpoints expone y
cómo se conecta con SMTP de Gmail y con OAuth de Google.

---

## 1. Vista general del flujo

### Flujo de registro
```
Usuario completa /registro
        │
        ▼
POST /api/registro
        │   ↳ valida (cliente + servidor)
        │   ↳ hashea contraseña con scrypt
        │   ↳ genera secreto TOTP (Google Authenticator)
        │   ↳ genera 8 recovery codes formato XXXX-XXXX
        │   ↳ genera token recovery_file (32 bytes urlsafe)
        │   ↳ inserta en `usuarios` (con hashes de todo)
        │   ↳ inserta hashes de los 8 codes en `recovery_codes`
        │   ↳ envía email de bienvenida con:
        │       · 8 códigos en HTML
        │       · adjunto recovery_*.txt con el token
        ▼
Sesión iniciada → redirige a /setup-2fa
```

### Flujo de login
```
POST /api/login {email, password}
        │   ↳ verifica hash
        │   ↳ si totp_enabled=False → sesión completa
        │   ↳ si totp_enabled=True  → sesión con pending_2fa=True
        ▼
                                       
   ┌────────── pending_2fa ─────────┐
   ▼              ▼                  ▼
   TOTP         Recovery code      Recovery file
   /api/login/2fa  /api/login/      /api/login/
                   recovery-code    recovery-file
        │              │                │
        ▼              ▼                ▼
   Sesión completa: pending_2fa = False
```

### Flujo de recuperación por email
```
POST /api/forgot-password {email}
        │   ↳ siempre responde "si existe te enviamos"
        │   ↳ si existe: crea token (32 bytes), guarda hash, expira 15 min
        │   ↳ envía email con link → /reset-password?token=...
        ▼
GET /reset-password?token=...   (renderiza formulario)
        │
        ▼
POST /api/reset-password {token, password}
        │   ↳ valida token vigente y no usado
        │   ↳ actualiza password_hash
        │   ↳ marca token como usado
```

### Flujo de Google OAuth
```
Click "Google" → GET /api/auth/google
        │   ↳ genera state aleatorio, lo guarda en sesión
        │   ↳ redirect a accounts.google.com/o/oauth2/v2/auth
        ▼
Usuario aprueba en Google
        ▼
GET /api/auth/google/callback?code=...&state=...
        │   ↳ valida state
        │   ↳ intercambia code por access_token
        │   ↳ obtiene perfil del usuario (sub, email, given_name, family_name)
        │   ↳ si google_id existe → login
        │   ↳ si email coincide   → vincular cuenta
        │   ↳ si nada coincide    → crear cuenta nueva
        ▼
Sesión iniciada → redirect a /
```

---

## 2. Archivos del sistema

### Modelos (capa de datos)

| Archivo | Responsabilidad |
|---|---|
| `models/usuario.py` | Tabla `usuarios`. Métodos: `asegurar_tabla`, `existe_email`, `obtener_por_email`, `obtener_por_id`, `obtener_por_google_id`, `crear`, `actualizar_password`, `activar_totp`, `vincular_google`. |
| `models/recovery.py` | Tablas `recovery_codes` y `password_reset_tokens`. Repos `RecoveryCodeRepository` y `PasswordResetRepository`. |

### Servicios (lógica de dominio)

| Archivo | Responsabilidad |
|---|---|
| `services/auth_service.py` | Orquesta TODO: registro, login, 2FA, recovery codes, recovery file, reset por email, Google login. Lanza `AuthError(mensaje, campo)` ante fallos. |
| `services/totp_service.py` | Wrapper sobre `pyotp` y `qrcode`. Funciones: `generar_secreto`, `uri_provisioning`, `qr_data_url`, `verificar_codigo`. |
| `services/email_service.py` | SMTP con Gmail App Password. Funciones genéricas (`enviar_correo`) y específicas (`email_bienvenida`, `email_reset_password`). |
| `services/google_oauth_service.py` | OAuth con Google sin Authlib (HTTP puro con `requests`). Funciones: `iniciar_flujo`, `intercambiar_codigo`. |

### Rutas

| Archivo | Responsabilidad |
|---|---|
| `routes/api.py` | Todos los endpoints JSON (`/api/...`). |
| `routes/main.py` | Vistas HTML (`/login`, `/registro`, `/login/2fa`, `/setup-2fa`, `/recuperar`, `/reset-password`). |

### Plantillas

| Archivo | Vista |
|---|---|
| `templates/login.html` | Pantalla principal de login. |
| `templates/register.html` | Pantalla de registro. |
| `templates/login_2fa.html` | Paso 2 del login: TOTP / recovery code / recovery file (con tabs). |
| `templates/setup_2fa.html` | QR + input de 6 dígitos para activar 2FA. |
| `templates/recover.html` | Solicitar enlace de reset por email. |
| `templates/reset_password.html` | Formulario para fijar nueva contraseña. |

### Frontend

| Archivo | Responsabilidad |
|---|---|
| `static/css/auth.css` | Diseño split-screen, glass card, blobs, OTP, dropzone, tabs. |
| `static/js/auth.js` | Toda la lógica cliente: validación, llamadas a la API, OTP agrupado, dropzone, tabs, carga del QR. |

### Configuración

| Archivo | Cambio |
|---|---|
| `config/settings.py` | Variables `SMTP_*`, `APP_BASE_URL`, `TOTP_ISSUER`, `GOOGLE_*`. |
| `.env` (no se commitea) | Valores reales (App Password de Gmail, client_id de Google, etc.). |
| `.env.example` | Plantilla con las claves esperadas. |
| `requirements.txt` | `pyotp==2.9.0`, `qrcode[pil]==7.4.2`, `Authlib==1.3.2`. |

---

## 3. Tablas en la base de datos

Las tres tablas se crean **automáticamente al arrancar la app** (idempotente).
También están en `database/schema.sql` para instalaciones desde cero.

### `usuarios`
| Columna | Tipo | Notas |
|---|---|---|
| `id` | INT PK AI |  |
| `nombres` | VARCHAR(80) |  |
| `apellidos` | VARCHAR(80) |  |
| `email` | VARCHAR(120) UNIQUE | normalizado a minúsculas |
| `password_hash` | VARCHAR(255) | scrypt vía werkzeug |
| `totp_secret` | VARCHAR(64) NULL | base32 |
| `totp_enabled` | TINYINT(1) | 0/1 |
| `recovery_file_hash` | VARCHAR(255) NULL | HMAC-SHA256 del token |
| `google_id` | VARCHAR(64) NULL | sub del usuario en Google |
| `email_verified` | TINYINT(1) | 1 si vino por OAuth |
| `created_at`, `updated_at` | DATETIME |  |

### `recovery_codes`
| Columna | Tipo | Notas |
|---|---|---|
| `id` | INT PK AI |  |
| `usuario_id` | INT FK → usuarios.id (CASCADE) |  |
| `code_hash` | VARCHAR(255) | HMAC-SHA256 del código en plano |
| `usado` | TINYINT(1) | 0/1 |
| `created_at`, `used_at` | DATETIME |  |

### `password_reset_tokens`
| Columna | Tipo | Notas |
|---|---|---|
| `id` | INT PK AI |  |
| `usuario_id` | INT FK → usuarios.id (CASCADE) |  |
| `token_hash` | VARCHAR(255) | HMAC-SHA256 del token |
| `expira_en` | DATETIME | now() + 15 min |
| `usado` | TINYINT(1) |  |

---

## 4. Endpoints de la API

| Método | Ruta | Body | Devuelve |
|---|---|---|---|
| POST | `/api/registro` | `{nombres, apellidos, email, password}` | `{success, usuario, next: "/setup-2fa"}` + sesión |
| POST | `/api/login` | `{email, password}` | `{success, usuario, requiere_2fa, next}` + sesión |
| POST | `/api/login/2fa` | `{codigo}` | `{success, usuario, next}` |
| POST | `/api/login/recovery-code` | `{codigo}` | `{success, usuario, next}` |
| POST | `/api/login/recovery-file` | multipart `archivo` | `{success, usuario, next}` |
| POST | `/api/forgot-password` | `{email}` | `{success, mensaje}` (siempre 200, no revela existencia) |
| POST | `/api/reset-password` | `{token, password}` | `{success, mensaje}` |
| GET  | `/api/2fa/setup` | — | `{success, secret, qr_data_url, totp_enabled}` |
| POST | `/api/2fa/activar` | `{codigo}` | `{success}` |
| POST | `/api/logout` | — | `{success, next}` |
| GET  | `/api/auth/google` | — | redirect a Google |
| GET  | `/api/auth/google/callback` | query `code, state` | redirect a `/` |
| GET  | `/api/me` | — | `{success, usuario}` (requiere sesión) |

Errores siguen el formato:
```json
{ "success": false, "error": "...", "campo": "email|password|..." }
```

---

## 5. Seguridad — qué hicimos y por qué

| Mecanismo | Implementación |
|---|---|
| **Hash de contraseña** | `werkzeug.security.generate_password_hash` (scrypt). Nunca plaintext en BD. |
| **Hash de tokens y códigos** | `hmac.sha256(SECRET_KEY, valor)`. Si la BD se filtra, los tokens siguen siendo inútiles. |
| **Comparación constante** | `hmac.compare_digest(...)` para evitar timing attacks. |
| **SQL inyección** | Todas las queries usan parámetros ligados (`%s`). |
| **Sesión cookie** | Firmada con `SECRET_KEY`, `HttpOnly`, `SameSite=Lax`. Lifetime 7 días. |
| **OAuth state** | Aleatorio (`secrets.token_urlsafe(24)`), validado en el callback. |
| **No revelar emails** | `forgot-password` responde igual exista o no la cuenta. |
| **Token de reset** | 32 bytes urlsafe, 15 min, un solo uso, los previos se invalidan. |
| **Recovery codes** | `secrets.choice` sobre alfabeto sin caracteres ambiguos (sin O, 0, I, 1, L). |
| **TOTP** | `pyotp` con ventana de ±30 s para reloj un poco desfasado. |
| **CORS con sesión** | `supports_credentials=True` + `credentials: 'same-origin'` en JS. |

---

## 6. Configurar SMTP (Gmail App Password)

1. Activa 2FA en tu cuenta de Google: <https://myaccount.google.com/security>
2. Crea un App Password: <https://myaccount.google.com/apppasswords>
3. Copia los 16 caracteres (sin espacios) en `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tucorreo@gmail.com
SMTP_APP_PASSWORD=xxxxxxxxxxxxxxxx
SMTP_FROM_NAME=Señas Co
APP_BASE_URL=http://127.0.0.1:5000
```

> ⚠️ **Tu App Password actual ya quedó expuesta en el chat con la IA. Revócala desde el panel de Google y crea otra antes de subir el proyecto a cualquier sitio público.**

---

## 7. Configurar "Iniciar sesión con Google"

1. Entra a <https://console.cloud.google.com/>.
2. Crea un proyecto nuevo (ej. "Señas Co").
3. **APIs y servicios → Pantalla de consentimiento OAuth**:
   - Tipo: **Externo**.
   - Nombre: Señas Co.
   - Email de soporte: tu correo.
   - Permisos: `email`, `profile`, `openid`.
   - Usuarios de prueba: añade tu correo.
4. **Credenciales → Crear credenciales → ID de cliente OAuth**:
   - Tipo: **Aplicación web**.
   - Orígenes autorizados: `http://127.0.0.1:5000`
   - URI de redirección: `http://127.0.0.1:5000/api/auth/google/callback`
5. Copia `client_id` y `client_secret` a `.env`:

```env
GOOGLE_CLIENT_ID=xxxxxxxxxxxx-xxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/api/auth/google/callback
```

6. Reinicia el servidor. El botón **Google** del login y registro ya redirige al flujo OAuth.

---

## 8. Cómo probar (cliente curl)

```bash
# 1) Registro
curl -c /tmp/c.txt -X POST -H "Content-Type: application/json" \
     -d '{"nombres":"X","apellidos":"Y","email":"xy@correo.com","password":"abc12345"}' \
     http://127.0.0.1:5000/api/registro

# 2) Mirar la sesión activa
curl -b /tmp/c.txt http://127.0.0.1:5000/api/me

# 3) Obtener QR para 2FA
curl -b /tmp/c.txt http://127.0.0.1:5000/api/2fa/setup

# 4) Activar 2FA con un código generado por Google Authenticator
curl -b /tmp/c.txt -X POST -H "Content-Type: application/json" \
     -d '{"codigo":"123456"}' http://127.0.0.1:5000/api/2fa/activar

# 5) Login con 2FA habilitado
curl -c /tmp/c.txt -X POST -H "Content-Type: application/json" \
     -d '{"email":"xy@correo.com","password":"abc12345"}' \
     http://127.0.0.1:5000/api/login
# → {"requiere_2fa": true, "next": "/login/2fa"}

# 6) Completar 2FA
curl -b /tmp/c.txt -X POST -H "Content-Type: application/json" \
     -d '{"codigo":"123456"}' http://127.0.0.1:5000/api/login/2fa

# 7) Forgot password
curl -X POST -H "Content-Type: application/json" \
     -d '{"email":"xy@correo.com"}' http://127.0.0.1:5000/api/forgot-password
```

---

## 9. Diagrama de archivos enviados al usuario en el registro

Al crear la cuenta, el correo de bienvenida incluye:

1. **HTML embebido**: 8 códigos de recuperación en formato `XXXX-XXXX` (mostrados una sola vez).
2. **Adjunto** `recovery_<nombre>.txt`:

```
==============================================
  Señas Co — Archivo de recuperación de cuenta
==============================================

Usuario: xy@correo.com
Token:   <64 caracteres urlsafe>

Sube este archivo en la pantalla de recuperación si
pierdes acceso a tu autenticador y a tus códigos.
NO compartas este archivo con nadie.
```

El **token** que aparece en el archivo se hashea con HMAC-SHA256 antes de
guardarse en `usuarios.recovery_file_hash`. Cuando el usuario sube el
archivo en `/login/2fa` (pestaña "Archivo"), el servidor extrae la línea
`Token:`, la rehashea y compara con `compare_digest`.

---

## 10. Cascada de recuperación

Cuando el usuario pierde el acceso:

| Tiene… | Mecanismo |
|---|---|
| Su autenticador (Google Authenticator, Authy, …) | Pestaña "Autenticador" en `/login/2fa`. |
| Uno de los 8 códigos de recuperación | Pestaña "Código" en `/login/2fa`. Se invalida tras usarse. |
| El archivo `recovery_*.txt` | Pestaña "Archivo" en `/login/2fa`. Sube el .txt. |
| Solo el correo | `/recuperar` → recibe link → fija nueva contraseña. |
| **Nada** | Fin de la línea. (No tenemos backdoor.) |

---

## 11. Próximos pasos sugeridos

- **Endurecer cookies en producción**: `SESSION_COOKIE_SECURE=True` cuando se sirva por HTTPS.
- **Rate limit** en `/api/login` y `/api/forgot-password` (Flask-Limiter).
- **CAPTCHA** en `/registro` para evitar bots.
- **Registro de auditoría**: tabla `eventos_auth` con `(usuario_id, evento, ip, ua, ts)`.
- **Regenerar códigos** desde una pantalla de "Mi cuenta" (botón rotar 2FA).
- **Eliminar cuenta** + descarga de datos (RGPD-friendly).
