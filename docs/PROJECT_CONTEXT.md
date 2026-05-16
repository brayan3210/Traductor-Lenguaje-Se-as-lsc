# Señas Co — Contexto completo del proyecto

> **Documento maestro** — léelo antes de empezar cualquier sesión nueva.
> Resume qué es el proyecto, cómo está construido, qué decisiones se han
> tomado y qué falta por hacer. Si lo mantienes actualizado, no tendrás
> que repetir nada de la historia.

---

## 1. Qué es Señas Co

Aplicación web académica que **traduce texto en español a Lengua de
Señas Colombiana (LSC)** mediante:

- Procesamiento de lenguaje natural con **spaCy** (modelo `es_core_news_md`).
- Un pipeline lingüístico que **reordena** la oración a la sintaxis LSC
  (TSOV: Tiempo · Sujeto · Objeto · Verbo) en lugar de hacer traducción
  palabra-por-palabra.
- Un diccionario visual en **MySQL** (XAMPP) con 202 entradas (alfabeto +
  números + palabras + frases) que apuntan a archivos `.mp4` o `.gif` en
  disco. El reproductor del frontend detecta el tipo automáticamente.
- Un **chat IA local** con **GPT4All** (Llama 3 8B) corriendo offline.
- Un **sistema de autenticación completo**: registro, login, 2FA TOTP,
  recovery codes (estilo Google), recovery file por email, reset por
  email, login con Google OAuth.

Es un proyecto académico para el diplomado **Servicios web con Flask**.
El stack: Flask + Jinja + MySQL + spaCy + PyMySQL + GPT4All.

**Usuario**: Brayan Cortés Leyton (brayancortesleyton@gmail.com).
Hispano-hablante, Windows + XAMPP + Python 3.12.

---

## 2. Stack técnico

| Capa | Tecnología | Notas |
|---|---|---|
| Backend | Flask 3.0.3 (Application Factory + Blueprints) | factory en `app.py` |
| BD | MySQL via XAMPP (PyMySQL 1.1.1) | DB: `traductor_lsc` |
| NLP | spaCy 3.7.5 + `es_core_news_md` | parser activo, tagger, morphologizer |
| Auth | werkzeug.security (scrypt), pyotp (TOTP), qrcode, Authlib (Google) | sesiones cookie firmadas |
| Email | `smtplib` + Gmail App Password | SMTP en `.env` |
| IA Chat | GPT4All 2.8.2 (Meta-Llama-3-8B-Instruct.Q4_0.gguf, 4.66 GB local) | sin red |
| Frontend | HTML5 + CSS3 (sin frameworks) + JS vanilla | dark institutional, glass morphism |

---

## 3. Estructura del proyecto

```
TraductorLSC/
├── app.py                       # Factory Flask, sesiones, registra blueprints
├── config/
│   └── settings.py              # Lectura del .env, clases de Config
├── database/
│   ├── connection.py            # Context managers PyMySQL
│   ├── init_db.py               # Crea esquema + carga seed
│   ├── schema.sql               # CREATE TABLEs idempotentes
│   └── seed_data.sql            # 202 INSERTs del diccionario
├── models/
│   ├── diccionario.py           # DiccionarioRepository, HistorialRepository
│   ├── usuario.py               # UsuarioRepository, dataclass Usuario
│   └── recovery.py              # RecoveryCodeRepository, PasswordResetRepository
├── services/
│   ├── nlp_service.py           # Tokenización, lematización, POS, dep, helpers WH/temporal/funcional
│   ├── traductor_service.py     # Pipeline LSC (etapas A-G), Sena, ResultadoTraduccion
│   ├── media_resolver.py        # Resuelve .mp4 ↔ .gif al vuelo desde disco
│   ├── auth_service.py          # Registro, login, 2FA, recovery, reset, Google
│   ├── totp_service.py          # Wrapper pyotp + qrcode
│   ├── email_service.py         # SMTP Gmail + templates HTML (bienvenida, reset)
│   ├── google_oauth_service.py  # OAuth Google con `requests` puro
│   └── chat_service.py          # GPT4All singleton perezoso
├── routes/
│   ├── __init__.py              # Re-exporta blueprints
│   ├── main.py                  # Rutas HTML (home, traductor, diccionario, chat, auth views)
│   └── api.py                   # Rutas JSON (api/traducir, api/login, api/registro, api/2fa/*, api/auth/google, api/chat, etc.)
├── templates/
│   ├── base_sub.html            # Layout para páginas internas (nav + footer)
│   ├── index.html               # Home institucional con CTAs
│   ├── translator.html          # Reproductor con video + glosa + badges
│   ├── diccionario.html         # Explorador del diccionario
│   ├── chat.html                # Chat con IA local
│   ├── login.html, register.html
│   ├── login_2fa.html           # Verificación 2FA con tabs (TOTP/code/file)
│   ├── setup_2fa.html           # QR + activación 2FA
│   ├── recover.html             # Solicitar reset por email
│   └── reset_password.html      # Definir nueva contraseña
├── static/
│   ├── css/
│   │   ├── style.css            # Estilos globales + nav + user pill
│   │   ├── translator.css       # Reproductor + glosa + badges + leyenda
│   │   ├── diccionario.css
│   │   ├── chat.css
│   │   └── auth.css             # Split-screen, blobs, OTP, dropzone, tabs
│   ├── js/
│   │   ├── translator.js        # Lógica del reproductor (img/video alterno)
│   │   ├── diccionario.js
│   │   ├── chat.js
│   │   └── auth.js              # Toda la lógica de auth (registro, login, 2FA, recovery)
│   └── gifs/
│       ├── letras/              # 27 archivos del alfabeto (.mp4 o .gif)
│       └── palabras/            # 175 archivos de palabras y frases (.mp4 o .gif)
├── venv/                        # entorno virtual Python (no se commitea)
├── .env                         # secretos REALES (no se commitea)
├── .env.example                 # plantilla
├── requirements.txt
├── AUTH.md                      # Documento detallado del sistema de auth
├── GIFS_CHECKLIST.md            # Lista de los 202 archivos a buscar
└── PROJECT_CONTEXT.md           # ESTE documento
```

---

## 4. Pipeline de traducción a LSC (núcleo del proyecto)

`services/traductor_service.py::TraductorService.traducir()` ejecuta:

| Paso | Etapa | Qué hace |
|---|---|---|
| 0 | Cortocircuitos | Letra única → vuelve seña directa. Letras múltiples (≥2) → marca `es_letra_explicita` |
| 1 | NLP | spaCy tokeniza, lematiza, etiqueta POS y dependencias. **Nuevo:** dict manual de conjugaciones (`lematizador_verbos.py`) sobreescribe el lema de spaCy si la forma está mapeada (ej. `comeré → comer`) |
| 1.b | Remediación | Re-procesa palabras al inicio (verbos mal etiquetados como PROPN) prefijando "yo " |
| 2 | Marcado | Anota `es_negacion`, `es_wh`, `es_temporal`, `es_letra_explicita` |
| 3 | **A** — Filtrar funcionales | Elimina DET, ADP, PUNCT, SYM, X, clíticos, AUX cópula, SCONJ — respetando BD y letras explícitas |
| 4 | **E** — Marcador temporal | Adverbio temporal explícito o inferencia por tiempo verbal (`ayer`/`mañana`) si está en BD |
| 5 | **D** — Palabras WH | Si es interrogativa, las extrae para colocarlas al final |
| 6 | **Segmentación de cláusulas (NUEVO)** | Parte los tokens en cláusulas usando `y/e/o/u/pero/sino/porque` como delimitadores. El conector se descarta (en LSC se sustituye por pausa). |
| 7 | **C + F por cláusula** | Para cada cláusula: extrae negación, reordena TSOV (`LUGAR + SUJETO + OBJETO + ADJUNTOS + VERBO`), añade negación al final |
| 8 | Composición | `[T] + cláusula_1 + ··· + cláusula_n + [WH]`, marca `clausula_idx` en cada token |
| 9 | Búsqueda BD | Lookup masivo + **fallback a forma superficial** si el lema no aparece (cubre fallos como `adios → adio`) |
| 10 | **B** — Resolución conservadora | Para faltantes: deletrear SOLO si POS=PROPN o sigla |
| 11 | Resolver media | Cada Sena pasa por `media_resolver.resolver()` (preferencia .mp4 → .gif) |
| 12 | Glosa string | Concatena los tokens con `·` cuando cambia `clausula_idx` (visualiza la pausa) |

### Etapas (A–G) y la "Opción 1"
- **A**: filtra artículos y preposiciones.
- **B**: dactilología solo para nombres propios y siglas.
- **C**: negación al final.
- **D**: WH al final si es pregunta.
- **E**: marcador temporal al inicio.
- **F**: reordenamiento TSOV usando dependencias.
- **G**: UI con glosa visible, badges (pregunta/negación), tarjeta clara para palabras sin seña.
- **Opción 1**: mantener GIFs/MP4 como recursos visuales, ser honesto con el usuario sobre limitaciones (sin marcadores no manuales, sin clasificadores espaciales).

### Ejemplos de glosa actual

| Entrada | Glosa LSC | Notas |
|---|---|---|
| Mañana mi mamá no irá al hospital | `MAÑANA · HOSPITAL MAMA IR NO` | Tiempo separado + cláusula con neg al final |
| ¿Dónde estudias? | `ESTUDIAR DONDE` | WH al final |
| ¿Dónde vives? | `DONDE VIVES` | Frase compuesta atómica de la BD (`donde_vives`); no se reordena porque es una sola seña |
| El niño grande corre rápido | `NIÑO GRANDE RAPIDO CORRER` | Artículo eliminado, verbo al final |
| Yo no quiero comer | `YO QUERER COMER NO` | Negación al final |
| Iré al colegio mañana | `MAÑANA · COLEGIO IR` | Temporal separado, lema "ir" |
| Me llamo Brayan | `BRAYAN ME LLAMO` | "Brayan" deletreado con dactilología |
| Quiero comer manzana y beber agua | `MANZANA QUERER COMER · AGUA BEBER` | **2 cláusulas** separadas por `·` |
| Comeré pan y beberé agua | `PAN COMER · AGUA BEBER` | Verbos en infinitivo (dict de conjugaciones) + cláusulas |
| Mañana iré al colegio porque quiero estudiar | `MAÑANA · COLEGIO IR · QUERER ESTUDIAR` | 3 bloques: tiempo + 2 cláusulas |
| adios | `ADIOS` | Resuelto por fallback de forma superficial (spaCy lematiza mal a "adio") |
| Te digo adiós | `ADIOS HABLAR` | "digo" → "hablar" vía dict manual |

### Lematización: cómo se obtiene el infinitivo

`services/lematizador_verbos.py` provee un dict `forma → infinitivo` con
~250 entradas que cubren los 23 verbos del diccionario LSC + verbos
comunes. Se construye programáticamente:
- Generación regular: paradigmas completos para `-ar`, `-er`, `-ir`.
- Irregulares: `ser, estar, tener, querer, poder, ir, venir, decir, saber, ver, dormir, sentir, pensar, jugar` declarados manualmente.
- Excluye formas ambiguas (`como, se, vela, voto`) para no romper WH ni sustantivos.

Aplicado en `nlp_service.procesar()` antes de devolver el `Token`: si la
forma superficial está en el dict, ese infinitivo gana sobre el lema de
spaCy.

### Fallback de búsqueda en BD

`_resolver_senas` aplica esta cascada por cada token:
1. Buscar `token.clave` en el batch del diccionario.
2. Si no aparece, probar `normalizar(token.texto)` (la forma superficial cruda).
3. Si tampoco, evaluar la regla de dactilología (PROPN o sigla).
4. Si ninguna, marcar como `no_disponible`.

Cubre el caso `"adios"` donde spaCy lematiza mal a `"adio"`.

### Limitaciones residuales (modelo `md`)
- "como" (1ª pers. de "comer") se mantiene como `como` por ser ambiguo con la WH "cómo".
- "Comí" al inicio mantiene lema `comí` — fuera del dict por seguridad.

---

## 5. Soporte mixto MP4 + GIF

**Decisión clave**: la BD declara las URLs con extensión `.gif` por
compatibilidad histórica, pero `services/media_resolver.py` resuelve al
vuelo el archivo real en disco con esta lógica:

1. Lee la URL declarada (ej. `/static/gifs/letras/a.gif`).
2. Mira la misma carpeta buscando `a.mp4` (preferencia: MP4 por mejor calidad).
3. Si no, busca `a.gif`.
4. Si no, devuelve la URL original con `existe=False` para que el frontend muestre el fallback.

El JSON de `/api/traducir` y `/api/diccionario` incluye `media_type: "video" | "image"`
y `existe: bool` por entrada, y el JS de cada vista elige `<video>` o
`<img>` según corresponda. **Tanto el traductor como el diccionario** pasan
por el mismo resolver — pegar archivos nuevos en disco no requiere SQL.

**Beneficios**:
- El usuario puede mezclar `.mp4` y `.gif` en cualquier proporción sin tocar BD.
- Si tiene MP4 e GIF de la misma palabra, gana el MP4.
- Cero queries SQL al cambiar formatos.
- El reproductor controla velocidades 0.5x/1x/1.5x/2x con `playbackRate` (mejor que con GIFs).

**Convenciones**:
- Nombres en minúsculas, sin tildes, sin ñ (use `n_enye` para Ñ).
- Espacios → guion bajo: "buenos días" → `buenos_dias.mp4`.
- Carpetas: `static/gifs/letras/` (alfabeto) y `static/gifs/palabras/` (todo lo demás).

**Bug histórico arreglado**: el atributo HTML `hidden` en el reproductor
era anulado por las reglas CSS `display: grid` de los elementos hijos.
Quedó cubierto con la regla:
```css
.tx-player [hidden],
.tx-player__loader[hidden],
.tx-player__fallback[hidden],
.tx-player__media[hidden] { display: none !important; }
```

### Marcadores no manuales (NMM) y concordancia verbal espacial

`services/marcadores_lsc.py` provee constantes y helpers para anotar
cada Sena con información gramatical que un clip aislado no puede
expresar por sí mismo.

**Marcadores aplicados** (`_anotar_marcadores`):
| Caso | Marcador | Cuándo |
|---|---|---|
| Pregunta sí/no | `cejas_arriba` | Toda la oración interrogativa sin WH |
| Pregunta WH | `cejas_fruncidas` | Sobre la palabra WH; el resto con `cejas_arriba` |
| Negación | `cabeza_no` | Sobre la seña `no/nada/nunca/...` al final de la cláusula |
| Topicalización | `topico` | Primera seña sujeto/objeto de oración declarativa larga |

**Verbos direccionales** (`VERBOS_DIRECCIONALES`):
`dar, decir, hablar, mandar, enviar, traer, llevar, mostrar, ayudar,
invitar, llamar, preguntar, responder, explicar, enseñar, regalar,
prestar, devolver, mirar, saludar`.

Para cada uno, si en la cláusula hay sujeto + objeto pronominales o si
el texto crudo contiene un patrón clítico (`yo te ayudo`, `tú me das`,
`él me dijo`), se calcula la flecha (ej. `yo → tú`) y se adjunta al
`Sena` del verbo. El frontend la muestra como pill amarilla en la
esquina superior derecha del reproductor.

Los `me/te/le` se filtran en la etapa A pero la inferencia ocurre
**antes** de que se descarten porque escaneamos el texto original.

### Lazy loading de videos en el diccionario

`static/js/diccionario.js` usa **IntersectionObserver** para no cargar
los ~200 videos de golpe cuando se abre `/diccionario`. Estrategia:
- Cada `<video>` se crea con `preload="none"` y `data-src=URL` (sin `src` real).
- Al entrar al viewport (con margen de 300 px de pre-carga), el observer
  inyecta el `src`, llama `load()` y `play()`.
- Al salir del viewport, hace `pause()` para liberar CPU/decoder.
- Re-renderizar (filtros, búsqueda) `unobserve()` los videos antiguos para
  evitar memory leaks.
- Fallback: navegadores sin IntersectionObserver cargan todo (UX previa).

Resultado: la página carga ~10 videos visibles en lugar de 200, sin
"tirones" iniciales en el navegador.

## 5.b. Casos especiales del traductor

Dos cortocircuitos viven **fuera del pipeline TSOV** porque cubren
intenciones explícitas del usuario que el lematizador estropearía:

### Una sola letra
Si el input es exactamente 1 carácter alfabético (`"a"`, `"Z"`, `"ñ"`),
`TraductorService._buscar_letra_directa()` se ejecuta **antes** del
pipeline y devuelve la seña dactilológica directamente. Si no, "a"
sería filtrada como preposición ADP por la etapa A.

### Secuencia de letras (≥ 2)
Antes del filtro funcional, `_marcar_letras_explicitas()` cuenta los
tokens de una sola letra. Si hay 2+ los marca con `es_letra_explicita=True`.
Ese flag:
- Hace que `detectar_funcional` los conserve (aunque sean ADP).
- Hace que `_asignar_rol` les asigne `rol="otro"` para que **preserven
  su orden natural** (no se reordenan a TSOV).

Cubre casos como `"a, b, c"`, `"a b c d e"`, `"A E I O U"` y el alfabeto
completo. **No** se activa si hay solo 1 letra suelta entre palabras
("voy a casa") porque la condición es ≥ 2.

---

## 6. Sistema de autenticación

Detallado en `AUTH.md`. Resumen:

| Endpoint | Función |
|---|---|
| `POST /api/registro` | Crea usuario + secret TOTP + 8 recovery codes + token recovery file. Envía email con archivo adjunto |
| `POST /api/login` | Email + password. Si tiene 2FA → `requiere_2fa: true` |
| `POST /api/login/2fa` | Verifica TOTP de Google Authenticator |
| `POST /api/login/recovery-code` | Usa uno de los 8 códigos de respaldo |
| `POST /api/login/recovery-file` | Sube el `recovery_*.txt` que llegó por email |
| `POST /api/forgot-password` | Envía link de reset (15 min) — respuesta neutra siempre |
| `POST /api/reset-password` | Define nueva contraseña con el token |
| `GET  /api/2fa/setup` | Devuelve QR + secreto TOTP |
| `POST /api/2fa/activar` | Activa 2FA tras verificar primer código |
| `GET  /api/auth/google` | Redirige a Google OAuth |
| `GET  /api/auth/google/callback` | Recibe code, crea/vincula cuenta |
| `POST /api/logout` | Cierra sesión |
| `GET  /api/me` | Devuelve usuario actual |

**Tablas BD**:
- `usuarios` — id, nombres, apellidos, email, password_hash, totp_secret, totp_enabled, recovery_file_hash, google_id, email_verified, created_at, updated_at.
- `recovery_codes` — usuario_id, code_hash, usado, used_at.
- `password_reset_tokens` — usuario_id, token_hash, expira_en, usado.

**Seguridad aplicada**:
- Hash con werkzeug scrypt. Nunca plaintext.
- Tokens y códigos hasheados con HMAC-SHA256 (no se pueden invertir si la BD se filtra).
- Comparación timing-safe con `hmac.compare_digest`.
- Sesiones cookie firmadas, `HttpOnly`, `SameSite=Lax`, lifetime 7 días.
- OAuth state aleatorio (24 bytes) validado en callback.
- `forgot-password` no revela existencia (siempre 200).
- Tokens reset 32 bytes urlsafe, 15 min, un solo uso.

**Pill de usuario en nav**: si hay sesión activa, en el navbar de
cualquier página aparece avatar + nombre + botón logout. El context
processor en `app.py::_inyectar_usuario` lo expone como `current_user` a
todas las plantillas.

---

## 7. Chat IA local

`services/chat_service.py` envuelve `gpt4all.GPT4All` como singleton perezoso.

- **Modelo**: `Meta-Llama-3-8B-Instruct.Q4_0.gguf` (4.66 GB, ya descargado en `~/.cache/gpt4all/`).
- **Endpoint**: `POST /api/chat` con `{mensaje}` → `{respuesta}`.
- **System prompt**: pide respuestas en español de 1-3 frases, sin rodeos.
- **Tuning**: `n_threads = cpu - 1`, `max_tokens=160`, `temp=0.6`, `repeat_penalty=1.15`.
- **Vista**: `/ia` (renombrada por el usuario desde `/chat`). Burbujas tipo chat, badge "Local · Privado", typing indicator.
- **Latencia**: 10-30 s por respuesta en CPU. Primera petición tarda ~30-90s en cargar el modelo a RAM.

---

## 8. Configuración (`.env`)

```env
# Flask
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=...

# MySQL (XAMPP)
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=traductor_lsc

# NLP
SPACY_MODEL=es_core_news_md
MAX_TOKENS=80

# Servidor
HOST=0.0.0.0
PORT=5000

# SMTP (Gmail App Password — ROTAR si se filtró)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=brayancortesleyton@gmail.com
SMTP_APP_PASSWORD=xxxxxxxxxxxxxxxx
SMTP_FROM_NAME=Señas Co
APP_BASE_URL=http://127.0.0.1:5000

# 2FA
TOTP_ISSUER=Señas Co

# Google OAuth (vacío hasta crear el proyecto en Google Cloud)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/api/auth/google/callback
```

---

## 9. Cómo arrancar

```powershell
# 1. Levantar XAMPP (Apache opcional, MySQL obligatorio)
# 2. En la terminal del proyecto:
cd C:\Users\braya\OneDrive\Escritorio\TraductorLSC
venv\Scripts\activate
python app.py
# → http://127.0.0.1:5000
```

Si es primera vez:
```powershell
pip install -r requirements.txt
python -m spacy download es_core_news_md
python -m database.init_db    # crea BD + tablas + seed (NO toca usuarios)
```

Las tablas `usuarios`, `recovery_codes`, `password_reset_tokens` se
crean **solas** al arrancar la app (idempotente).

---

## 10. Estado actual (✅ hecho / ⏳ pendiente / ⚠️ limitación conocida)

### ✅ Hecho
- Pipeline LSC completo (etapas A → G).
- Modelo spaCy `es_core_news_md` con parser activo.
- Detección de frases multi-palabra (n-gramas).
- Remediación de POS al inicio de oración.
- **Cortocircuito para una sola letra** (`_buscar_letra_directa`).
- **Detección de secuencias de deletreo** ≥ 2 letras con preservación de orden.
- **Segmentación de cláusulas** por `y/e/o/u/pero/sino/porque` con separador visual `·`.
- **Dict manual de conjugaciones verbales** (`services/lematizador_verbos.py`, ~250 formas) que cubre los 23 verbos del diccionario LSC + irregulares frecuentes.
- **Fallback de búsqueda** a la forma superficial cuando el lema falla (cubre `adios → adio`).
- Soporte nativo MP4 + GIF con resolver dinámico, aplicado en traductor Y diccionario.
- **Lazy loading de videos** en el diccionario con IntersectionObserver (no satura el navegador).
- Reproductor con `<video>` + `<img>` alternables, controles de velocidad exactos.
- Glosa LSC visible con badges de pregunta/negación + separador `·` entre cláusulas.
- **Marcadores no manuales** (`services/marcadores_lsc.py`): el reproductor muestra overlays con la expresión facial esperada — cejas levantadas (pregunta sí/no, tópico), cejas fruncidas (pregunta WH), cabeza moviéndose lateral (negación), tópico (cejas + pausa al inicio).
- **Concordancia verbal espacial**: verbos direccionales (`dar, decir, ayudar, traer, llamar, mostrar, mirar, …`) reciben una flecha visual `yo → tú`, `tú → yo`, `él/ella → yo`, etc. La detección combina pronombres explícitos en la cláusula con un escaneo regex del texto crudo para capturar clíticos (`me/te/le`) que la etapa A descarta.
- Disclaimer actualizado para mencionar videos y limitaciones reales (no solo GIFs).
- Diccionario de **204 entradas** en BD (incluye `con_gusto` y `rosado`).
- Sistema de auth completo: registro, login, 2FA TOTP, recovery codes, recovery file, reset por email, Google OAuth, logout.
- Email SMTP con Gmail App Password (envíos verificados).
- Chat IA local con Llama 3 8B operativo.
- Pill de usuario logueado en nav.
- Documentación: AUTH.md, GIFS_CHECKLIST.md, PROJECT_CONTEXT.md (este).

### ⏳ Pendiente — contenido (no código)

**Inventario auditado 2026-05-14**: BD viva tiene **218 entradas
activas** pero solo **53 archivos en disco (24% de cobertura visual)**.

Detalle por categoría (en disco / en BD):

| Categoría | Cobertura | Falta |
|---|---|---|
| Letras | 26/27 | Solo `ñ` (`n_enye.mp4`) |
| Saludos | 10/16 | bien, como_estas, hasta_luego, mal, mas_o_menos, mucho_gusto |
| Colores | 8/9 | `naranja` |
| Familia | 8/13 | esposo, esposa, mama, papa, familia |
| Comida | 1/13 | TODO menos `cafe` (agua, pan, leche, …) |
| Verbos | **0/35** | TODO (ser, estar, tener, querer, ir, comer, …) |
| Números | **0/11** | TODO (uno, dos, tres, …, diez) |
| Adjetivos | 0/17 | TODO (grande, pequeño, bueno, malo, feliz, …) |
| Lugares | 0/14 | TODO (casa, colegio, trabajo, …) |
| Tiempo | 0/12 | TODO (hoy, mañana, ayer, …) |
| Cuerpo | 0/8 | TODO (cabeza, mano, ojo, …) |
| Conectores | 0/7 | TODO (mas, muy, no, pero, porque, si, tambien) |
| Preguntas | 0/7 | TODO (que, donde, cuando, como, por_que, cuanto, quien) |
| Días | 0/7 | TODO (lunes…domingo) |
| Emociones | 0/5 | TODO (feliz, triste, enojado, sorprendido, cansado) |
| Animales | 0/2 | perro, gato (P0 2026-05-14) |
| Personas | 0/5 | niño, niña, bebe, amigo, amiga (P0 2026-05-14) |
| Frases | 0/10 | TODO (como_te_llamas, me_llamo, …) |

**Huérfanos** (archivo en disco sin entrada en BD): 0. Sano.

**Priorización para sustentación** (los ≈30 archivos que más mueven la aguja):
1. Ñ (1 archivo): `n_enye.mp4`.
2. Números 0–10 (11 archivos): impactan TODA traducción con cantidad.
3. Verbos top-10 (10 archivos): ser, estar, tener, ir, comer, beber,
   ver, hablar, querer, hacer. Sin verbos en video, el reproductor
   muestra el TSOV en glosa pero todas las acciones quedan
   pendientes — pérdida visual enorme.
4. Sustantivos P0 (10 archivos): los recién insertados — perro,
   gato, mama, papa, niño, niña, bebe, amigo, amiga, familia.

Total mínimo razonable: **32 archivos**. Tiempo estimado: una sesión
de 3–4 h descargando del INSOR.

**Otras tareas de contenido**:
- Configurar Google Cloud Console → completar `GOOGLE_CLIENT_ID` y
  `SECRET` en `.env` para que el botón "Iniciar con Google" funcione.

### ⏳ Pendiente — código (ver sección 15 para roadmap, 16 para seguridad, 17 para cierre)
- Marcadores no manuales en escala (gradient continuo, no discreto).
- Detección fuzzy de frases canónicas (matchear "Colombia tiene dos mares" → `colombia_dos_mares`).
- Avatar 3D o video de intérprete para señas continuas (lejos del alcance académico).

### ⚠️ Limitaciones residuales
- spaCy `md` lematiza mal "como" y "comí" — el dict manual los excluye por ambigüedad con WH/sustantivos.
- Sustantivos no signados en BD salen como `no_disponible` (ampliar BD).
- No se interpretan marcadores no manuales — limitación inherente a clips aislados.
- App Password de Gmail se compartió en chat → **rotar** en https://myaccount.google.com/apppasswords.

---

## 11. Decisiones de diseño que NO se deben revertir sin justificación

1. **Carpetas `static/gifs/`** se quedan con ese nombre aunque dentro haya MP4. Renombrar obligaría a tocar 202 URLs en BD por cero ganancia.
2. **Frases compuestas atómicas** (ej. `donde_vives`) NO se reordenan a TSOV; corresponden a una sola seña en LSC real.
3. **Dactilología solo para PROPN/siglas**. Nunca para palabras comunes — eso era el bug original.
4. **El campo `gif_url` en BD** sigue llamándose así por compatibilidad. Conceptualmente es `media_url`.
5. **No tocar el seed_data.sql** para cambiar extensiones — el resolver lo resuelve dinámicamente.
6. **Llama 3 8B** como modelo de chat por defecto (en vez de orca-mini) porque el usuario ya lo tiene descargado.
7. **Sesiones en cookie firmada** (no en BD) porque es suficiente para alcance académico.
8. **POSTs sin CSRF token** porque la app no se expone públicamente. Si se desplegara a producción, agregar `flask-wtf`.

---

## 12. Cómo agregar una nueva palabra al diccionario

1. Encuentra el `.mp4` (o `.gif`) y nómbralo igual que la clave en BD,
   en minúsculas y con `_` en vez de espacios. Ej: `tomar.mp4`.
2. Pégalo en `static/gifs/palabras/`.
3. Inserta la fila en BD vía phpMyAdmin:
   ```sql
   INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion)
   VALUES ('tomar', '/static/gifs/palabras/tomar.gif', 'palabra', 'verbos', 'Verbo tomar');
   ```
   (Usa `.gif` en la URL aunque tu archivo sea `.mp4`; el resolver hará la magia.)
4. Reinicia el servidor (o si tiene auto-reload, refresca la página).

---

## 13. Comandos útiles

```powershell
# Activar entorno
venv\Scripts\activate

# Arrancar app
python app.py

# Re-generar QR de spaCy (si cambias modelo)
python -m spacy download es_core_news_md

# Reinicializar BD (¡borra el diccionario!)
python -m database.init_db

# Inspeccionar el resolver
python -c "from services.media_resolver import resolver; print(resolver('/static/gifs/letras/a.gif'))"
```

---

## 14. Para próximas sesiones

Cuando empieces una sesión nueva:
1. **Lee este archivo primero**.
2. Verifica `ls static/gifs/letras/ static/gifs/palabras/` para ver qué archivos hay.
3. `git log --oneline -10` (si hay git) para ver cambios recientes.
4. Si algo falla, mira los logs del servidor en background con el nombre del task.

Si el usuario pide algo que ya está hecho, responde citando este
documento. Si pide algo nuevo, agrégalo a "Pendiente" en sección 10
cuando termines y actualiza este archivo.

---

## 15. Roadmap detallado de mejoras futuras

Esta sección reemplaza el viejo "pendiente — código (mejoras opcionales)"
con un análisis exhaustivo. Cada propuesta lleva: **qué resuelve**,
**cómo se implementaría**, **costo estimado**, **dependencias**, y
**veredicto** (recomendable, viable con esfuerzo, o fuera de alcance).

Las propuestas están ordenadas por impacto/esfuerzo, no por capricho.
Si el proyecto sigue activo, abordar de arriba hacia abajo.

---

### 15.1 — TIER 1: Mejoras de fidelidad LSC (días, alto impacto)

#### 15.1.A — Frases canónicas con video de intérprete real
**Qué resuelve**: cuando el usuario escribe una frase culturalmente
fija ("Colombia tiene dos mares…", "¿Cómo te llamas?", "Mucho gusto en
conocerte"), el sistema reproduce un video grabado por un intérprete
LSC certificado en lugar de generar glosa TSOV con clips aislados.
Esto es **lo más fiel posible a LSC nativa** sin avatar 3D.

**Cómo**: el mecanismo existe — la tabla `senas` tiene `tipo='frase'`
y el detector de n-gramas en `_buscar_frase` lo activa. Solo falta
**contenido**:
1. Identificar las 50–100 frases más usadas en contextos cotidianos
   (presentaciones, preguntas frecuentes, geografía, frases
   institucionales tipo INSOR).
2. Grabar con un intérprete LSC (estudiantes de "Tecnología en
   Interpretación" en universidades de Bogotá; FENASCOL ofrece
   servicios pagos).
3. Por cada frase: video MP4 (1–3 MB, 3–8 s, 240×240 o 320×320),
   nombrar `clave_canonica.mp4` (ej. `colombia_dos_mares.mp4`),
   colocar en `static/gifs/palabras/`, insertar fila en `senas`.

**Costo**: 1–2 sesiones de grabación (2–3 h cada una) + edición simple
con FFmpeg. **$0 si tienes un intérprete amigo, $200–$1.000 USD si
contratas**.

**Dependencias**: ninguna. El sistema ya soporta esto.

**Veredicto**: ⭐ **Altamente recomendable** — máximo impacto por mínimo
esfuerzo de código (cero) y razonable de contenido.

---

#### 15.1.B — Detección fuzzy de frases canónicas
**Qué resuelve**: hoy el detector de n-gramas exige las palabras
**consecutivas y en orden exacto**. "Colombia tiene dos mares" NO
matchea `colombia_dos_mares` porque "tiene" rompe la secuencia. La
detección fuzzy permitiría: si las palabras clave (`colombia, mares`)
y los números/colores característicos están presentes, usar el video
canónico aunque haya palabras intermedias.

**Cómo**: nuevo método en `nlp_service.py::buscar_frase_fuzzy(tokens, frases_db)`:
1. Para cada frase canónica en BD, extraer su lista de tokens clave
   (sustantivos, verbos, números, adjetivos — ignorar funcionales).
2. Calcular score de similitud entre los tokens del input y los
   tokens clave de cada frase canónica (Jaccard, o cosine sobre BoW).
3. Si el mejor score > umbral (ej. 0.7), reproducir el video canónico.
4. Si no, caer al pipeline TSOV normal.

**Costo**: ~50 líneas de código nuevo + ajuste del umbral con casos
reales. **2–3 días de trabajo**.

**Dependencias**: requiere 15.1.A primero (para tener frases en BD).

**Veredicto**: ⭐ **Recomendable** después de 15.1.A. Eleva mucho la
sensación de fidelidad sin gastar en contenido nuevo.

---

#### 15.1.C — Diccionario de conjugaciones expandido
**Qué resuelve**: `services/lematizador_verbos.py` cubre los 23 verbos
del diccionario LSC + irregulares principales. Faltan ~150 verbos
comunes en español (subir, bajar, salir, entrar, abrir, cerrar,
entender, esperar, llegar, …). Sin sus conjugaciones, el sistema falla
en oraciones simples como "Subo al bus" → spaCy lematiza "subo" como
"subo" (no "subir").

**Cómo**: ampliar la lista `VERBOS_REGULARES` en `lematizador_verbos.py`.
Para los irregulares, declararlos manualmente en `VERBOS_IRREGULARES`.
~100 nuevas entradas cubrirían el 95% del español cotidiano.

**Costo**: 1 día de trabajo lingüístico + testing. **Cero riesgo**, no
toca otra capa.

**Veredicto**: ⭐ **Altamente recomendable**. Mejora cuantificable
inmediata.

---

#### 15.1.D — Sustantivos comunes faltantes en BD
**Qué resuelve**: hoy `mamá, papá, niño, niña, familia` salen como
`no_disponible` porque no están en BD. Cualquier frase familiar pierde
una palabra clave. El usuario ve "MAMÁ" en gris con texto "Sin seña LSC".

**Cómo**: agregar entradas en `senas` con sus videos LSC del INSOR.
Lista mínima:
```
mamá, papá, niño, niña, bebé, abuelo, abuela, tío, tía,
primo, prima, sobrino, sobrina, novio, novia, amigo, amiga,
señor, señora, joven, anciano, vecino, profesor, profesora,
estudiante, doctor, enfermero, policía, …
```

**Costo**: solo contenido (descargar/grabar videos + INSERT en BD).
~2 horas por cada 20 entradas si los videos están listos.

**Veredicto**: ⭐ **Crítico** para uso real. Sin esto el sistema queda
"académico" pero no "usable".

---

### 15.2 — TIER 2: Mejoras estructurales (semanas, mediano impacto)

#### 15.2.A — Marcadores no manuales con intensidad continua
**Qué resuelve**: hoy el marcador es discreto (un código fijo por
seña). En LSC real, las cejas se levantan **gradualmente** durante
toda la pregunta y bajan en la última seña. No es booleano sino una
curva de intensidad. Mostrarlo gradualmente daría más realismo
visual al overlay.

**Cómo**: `services/marcadores_lsc.py` ampliado con `intensidad: float
[0,1]`. La curva se calcula según la posición del token dentro de la
cláusula:
- Para preguntas WH: intensidad sube hasta la palabra WH al final.
- Para negación: pico en la seña de negación, decae después.
- Para tópico: pico al inicio, decae rápido.

Frontend interpola el color/opacidad del overlay según `intensidad`.

**Costo**: 3–5 días (lógica + UI fluida).

**Veredicto**: 🌗 **Viable con esfuerzo**. Es pulido, no funcionalidad
crítica.

---

#### 15.2.B — Reconocimiento de voz a texto (WebSpeech / Whisper)
**Qué resuelve**: el usuario puede **dictar** en lugar de escribir,
útil para hablantes nativos que prefieren la voz. Mejora accesibilidad
(personas con problemas motrices) y velocidad.

**Cómo**: dos rutas:
1. **WebSpeech API** (gratis, en navegador, español): botón de
   micrófono en el textarea del traductor. Usuario habla → input se
   llena con texto → traduce normal.
2. **Whisper local** (gratis, OpenAI, instalado vía pip): si el
   usuario quiere mayor precisión, se sube audio a `/api/transcribir`
   y se procesa con Whisper. Más lento pero más preciso.

**Costo**: WebSpeech: 1 día. Whisper: 3–5 días + RAM extra (modelo
base ~1 GB). Recomendable WebSpeech para alcance académico.

**Veredicto**: ⭐ **Recomendable** la versión WebSpeech.

---

#### 15.2.C — Historial de traducciones por usuario
**Qué resuelve**: hoy `historial` registra IP pero no usuario. El
usuario logueado debería ver SUS traducciones recientes y marcar
favoritas para acceso rápido.

**Cómo**:
1. Agregar columna `usuario_id INT NULL` a `historial` con FK a
   `usuarios.id`.
2. Modificar `routes/api.py::traducir` para inyectar `session.user_id`.
3. Vista `/perfil` con dos secciones: "mis traducciones recientes"
   y "favoritas".
4. Tabla auxiliar `favoritos(usuario_id, historial_id)` o booleano
   en `historial`.

**Costo**: 2–3 días.

**Veredicto**: 🌗 **Viable**. Bonita UX pero no esencial.

---

#### 15.2.D — Modo aprendizaje (gamificado)
**Qué resuelve**: el proyecto puede crecer de "traductor" a
"plataforma educativa LSC". Lecciones interactivas, quiz, ranking de
usuarios, progreso por categoría.

**Cómo**: módulos:
- `lecciones`: ordenadas, cada una con 5–10 señas a aprender.
- `quiz`: ver video → escribir palabra (o multiple choice).
- `progreso`: porcentaje por categoría, racha de días.
- `ranking`: liderboard global.

**Costo**: 2–4 semanas para versión decente.

**Veredicto**: 🌗 **Viable con tiempo**. Buena idea para tesis o
proyecto de grado ampliado, no para sustentación corta.

---

#### 15.2.E — PWA (Progressive Web App) instalable
**Qué resuelve**: la app se puede "instalar" en celular/tablet sin
pasar por App Store. Funciona offline (con limitaciones), se ve como
app nativa.

**Cómo**:
- `manifest.json` con iconos y nombre.
- Service worker que cachea HTML/CSS/JS y los videos visitados.
- Lógica de fallback offline (mostrar último diccionario cargado).

**Costo**: 3–5 días.

**Veredicto**: 🌗 **Viable** si quieres distribución móvil sencilla.

---

#### 15.2.F — Compartir traducción por URL única
**Qué resuelve**: el usuario hace una traducción interesante y quiere
compartirla en WhatsApp, redes, embed en blog. Hoy no hay URL
permanente.

**Cómo**: tabla `traduccion_compartida(uuid, texto, glosa, created_at)`.
Endpoint `POST /api/compartir` genera UUID. URL pública
`/t/<uuid>` muestra la traducción en modo lectura. OG metadata para
preview en redes.

**Costo**: 1–2 días.

**Veredicto**: 🌗 **Viable**. Pequeño pero bonito.

---

### 15.3 — TIER 3: Tecnologías avanzadas (meses, alto impacto pero alto costo)

#### 15.3.A — Avatar 3D LSC fiel (HamNoSys + SiGML + WebGL)
**Qué resuelve**: la única forma de tener señas REALMENTE continuas y
con marcadores no manuales integrados sin grabar todo con un
intérprete. El avatar puede animar cualquier frase si tiene la
notación de cada seña.

**Cómo**: tres capas, todas requieren expertise:
1. **Avatar 3D riggado**: modelo humanoide con rig de manos detallado
   y blendshapes faciales. Mixamo o Ready Player Me como base. Custom
   rigging de dedos (50+ huesos). 1–3 meses de animador 3D.
2. **Diccionario glosa → SiGML**: cada seña LSC necesita su script
   HamNoSys/SiGML (~50–100 símbolos por seña). Requiere lingüista
   LSC con conocimiento de HamNoSys. **6–12 meses para 200 señas**.
3. **Engine WebGL**: sistema de blending de animaciones que toma
   SiGML y lo renderiza con `three.js`. Sin engines maduros open
   source actuales — JASigning está deprecated. Construir desde
   cero: 4–6 meses de dev gráfico.

**Total**: ~1.5–2 años con un equipo de 3 personas. **$30K–$100K USD**.

**Dependencias**: lingüista LSC + animador 3D + dev gráfico.

**Veredicto**: 🚫 **Fuera de alcance académico**. Solo viable como
proyecto industrial financiado o tesis doctoral en grupo.

---

#### 15.3.B — Reconocimiento LSC → Español (sentido inverso)
**Qué resuelve**: el usuario sordo signa en cámara y el sistema
transcribe a español. Es el camino opuesto del traductor actual y
abre la app a comunicación bidireccional real.

**Cómo**: pipeline de visión por computador:
1. Captura cámara → MediaPipe extrae landmarks de manos/cara/cuerpo.
2. Modelo de ML (transformer o LSTM) entrenado con corpus LSC para
   clasificar la secuencia de landmarks → palabra/seña.
3. Concatenar predicciones con language model para reconstruir
   oración en español.

**Costo**: dataset es el cuello de botella. Hay corpus pequeños (~500
señas anotadas), pero LSC tiene poco material académico publicado.
Sin dataset robusto, accuracy < 60%. **6–12 meses de investigación**
mínimo, equipo con experiencia en CV/ML.

**Veredicto**: 🚫 **Frontera de investigación**. Tesis de maestría o
doctorado, no diplomado.

---

#### 15.3.C — Modelo NLP especializado LSC (fine-tuning)
**Qué resuelve**: en lugar de las reglas TSOV codificadas en
`traductor_service.py`, entrenar un modelo seq2seq (BART, T5,
mT5-small) con pares (español, glosa LSC). El modelo aprende el
reordenamiento, los marcadores, las elisiones — todo de una vez.

**Cómo**:
1. Construir corpus paralelo español ↔ glosa LSC (mínimo 5.000 pares
   de calidad). FENASCOL/INSOR podrían tener material publicado.
2. Fine-tune mT5-small o BART-Spanish con HuggingFace.
3. Reemplazar el pipeline TSOV con inferencia del modelo.

**Costo**: corpus es lo difícil. Si lo tienes, fine-tuning en una GPU
prestada (Colab Pro) toma horas. **2–3 meses de trabajo**.

**Dependencias**: corpus disponible.

**Veredicto**: 🌗 **Viable como tesis**. Más sofisticado que las
reglas pero requiere data.

---

#### 15.3.D — Detección de emociones del texto → expresión del avatar
**Qué resuelve**: si el avatar 3D está disponible, el sistema podría
inferir el tono emocional del texto ("¡Qué triste!", "¡Genial!") y
modular las cejas/ojos del avatar para reflejarlo. Es un nivel
adicional encima del avatar.

**Cómo**: clasificador de sentimiento (BERT-Spanish fine-tuned) →
mapping a blendshape facial → animar al avatar.

**Costo**: 2–4 semanas si el avatar ya existe.

**Veredicto**: 🚫 **Solo si existe 15.3.A**.

---

### 15.4 — TIER 4: Operacional / despliegue

#### 15.4.A — Despliegue en producción (HTTPS + dominio)
**Qué resuelve**: hoy corre en `127.0.0.1:5000` con Werkzeug (servidor
de desarrollo). Para uso real necesita gunicorn + nginx + HTTPS +
dominio.

**Cómo**: VPS pequeño (DigitalOcean, Linode, $6/mes) + Let's Encrypt
+ nginx como reverse proxy + gunicorn. Migrar BD a MySQL externo o
mantener en mismo VPS.

**Costo**: 1–2 días + $6/mes.

**Veredicto**: ⭐ **Recomendable si vas a presentar a usuarios reales**.

---

#### 15.4.B — CSRF, rate limiting, observabilidad
**Qué resuelve**: para producción real, falta:
- Tokens CSRF en formularios (flask-wtf).
- Rate limiting en `/api/login` y `/api/forgot-password` (flask-limiter).
- Logs estructurados (loguru o structlog).
- Métricas (Prometheus + Grafana).

**Costo**: 3–5 días.

**Veredicto**: ⭐ **Crítico** para producción real, **opcional** para
académico.

---

#### 15.4.C — Tests automatizados
**Qué resuelve**: hoy verificamos manualmente con curl. Falta suite de
pytest que cubra: pipeline TSOV, marcadores, recovery, OAuth, etc.

**Cómo**: `pytest` + `pytest-flask` + fixture de BD limpia. ~50 tests
para coverage decente.

**Costo**: 1 semana.

**Veredicto**: 🌗 **Recomendable** para mantener calidad a largo
plazo.

---

### 15.5 — Resumen ejecutivo de prioridades

| Prioridad | Item | Tiempo | Impacto |
|---|---|---|---|
| **P0** | 15.1.D Sustantivos comunes en BD | días | crítico |
| **P0** | 15.1.A Frases canónicas con intérprete | semana | crítico |
| **P1** | 15.1.C Diccionario verbos expandido | día | alto |
| **P1** | 15.1.B Detección fuzzy de frases | días | alto |
| **P2** | 15.2.B Reconocimiento voz (WebSpeech) | día | medio |
| **P2** | 15.4.A Despliegue HTTPS | días | medio |
| **P3** | 15.2.A Marcadores con intensidad | semana | bajo |
| **P3** | 15.2.C Historial por usuario | días | bajo |
| **P3** | 15.2.D Modo aprendizaje | semanas | medio |
| **P4** | 15.3.C Modelo NLP fine-tuned | meses | alto |
| **P5** | 15.3.A Avatar 3D LSC | años | muy alto |
| **P5** | 15.3.B Reconocimiento LSC → texto | años | muy alto |

**Lectura**: P0–P1 son lo que mantiene la promesa actual y la eleva
significativamente. P2–P3 son pulido y crecimiento. P4–P5 son
investigación/proyectos industriales.

---

## 16. Auditoría de seguridad y errores críticos

Revisión completa del código realizada el **2026-05-14**. Cada hallazgo
lleva: severidad, dónde está, qué riesgo abre y cómo se remedia.

Se evaluaron: `app.py`, `config/settings.py`, `routes/api.py`,
`routes/main.py`, `services/auth_service.py`, `services/email_service.py`,
`services/google_oauth_service.py`, `services/chat_service.py`,
`services/traductor_service.py`, `models/usuario.py`, `models/diccionario.py`,
`models/recovery.py`, `database/connection.py`, `static/js/*.js`,
`templates/*.html`, `.env`, `.gitignore`.

---

### 16.1 — 🔴 CRÍTICOS (resolver antes de cualquier despliegue)

#### 16.1.A — Gmail App Password expuesta en `.env` y en historial de chat
**Dónde**: `.env` línea 26 — `SMTP_APP_PASSWORD=qbdzdldsegrsenbj`.
**Riesgo**: la contraseña fue compartida en conversaciones (queda
indexada en logs locales del cliente, transcript JSONL). Cualquier
persona con acceso al equipo puede leer correos, enviar phishing
suplantando `Señas Co` y restablecer contraseñas de usuarios.
**Remediar**: ya marcado como TODO. Rotar **hoy** en
<https://myaccount.google.com/apppasswords> y reemplazar el valor en
`.env`. Considerar mover los secretos fuera de `.env` (variables de
entorno del sistema o un gestor como `pass`/`KeePass`).

#### 16.1.B — `FLASK_DEBUG=True` + `HOST=0.0.0.0`
**Dónde**: `.env` líneas 7 y 19, leído por `config/settings.py`.
**Riesgo**: con `debug=True`, Werkzeug expone el **debugger interactivo
con PIN** en cualquier traceback no manejado. Combinado con
`HOST=0.0.0.0`, el servidor escucha en TODAS las interfaces de red —
cualquier dispositivo de la red WiFi local puede conectarse a
`http://<tu-ip>:5000` y, si dispara una excepción, intentar adivinar el
PIN para **ejecutar código arbitrario** en tu máquina (RCE).
**Remediar**:
- Para desarrollo local: `HOST=127.0.0.1` y `FLASK_DEBUG=False` salvo
  que estés debuggeando activamente.
- Para entregar el proyecto: `FLASK_DEBUG=False` permanente, y servir
  detrás de `waitress` o `gunicorn`, nunca con el server de desarrollo
  de Flask.

#### 16.1.C — MySQL root sin contraseña
**Dónde**: `.env` líneas 12–13 — `DB_USER=root`, `DB_PASSWORD=` (vacío).
**Riesgo**: el XAMPP que viene de fábrica acepta conexiones `root`
sin password. Si el puerto `3306` está accesible en LAN (XAMPP lo
expone por defecto en algunas instalaciones), cualquiera en la red
puede `mysql -h <tu-ip> -u root` y borrar tu BD.
**Remediar**:
1. En phpMyAdmin → cuenta `root` → asignar contraseña.
2. Crear un usuario MySQL específico para la app con privilegios
   mínimos (`SELECT, INSERT, UPDATE, DELETE` sobre `traductor_lsc`).
3. Reemplazar `DB_USER`/`DB_PASSWORD` en `.env`.

#### 16.1.D — `SECRET_KEY` débil en desarrollo y vacía en producción
**Dónde**: `config/settings.py` línea 40 (default
`dev-secret-cambiar-en-produccion`) y `.env` línea 8
(`local-dev-secret-please-rotate-in-prod`).
**Riesgo**: la clave firma las cookies de sesión Flask. Una clave
predecible permite a un atacante **forjar sesiones de cualquier
usuario** (incluyendo `user_id=1`). Además, los hashes de recovery
codes y reset tokens usan esa clave como HMAC; si se filtra, un
atacante puede recalcular hashes y autenticarse sin el código.
**Remediar**: generar 32 bytes aleatorios y guardarlos:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### 16.2 — 🟠 ALTOS (resolver antes de exponer la app a otros usuarios)

#### 16.2.A — Sin protección CSRF en endpoints POST
**Dónde**: todos los `@api_bp.post(...)` en `routes/api.py`.
**Riesgo**: Aunque `SESSION_COOKIE_SAMESITE=Lax` mitiga muchos casos,
un atacante puede:
- Engañar al usuario para hacer click en un link que dispare un POST
  no idempotente cross-site con `<form method=post>` (Lax permite POST
  top-level).
- Hacer logout forzado a través de un `<form action="/api/logout">`.
- En navegadores antiguos que no respetan Lax, ejecutar cualquier
  acción autenticada.
**Remediar**: instalar `flask-wtf` y aplicar `csrf.protect()` global.
Excluir solo lo que se llame con `fetch()` desde el mismo origen
después de validar el token explícito en cabecera `X-CSRF-Token`.

#### 16.2.B — Sin rate limiting en endpoints sensibles
**Dónde**: `/api/login`, `/api/login/2fa`, `/api/login/recovery-code`,
`/api/forgot-password`, `/api/reset-password`, `/api/registro`.
**Riesgo**: brute-force de contraseñas, códigos TOTP (10⁶ combinaciones),
códigos de recuperación (≈3·10¹⁰ pero limitados a 8 vigentes por
usuario), y enumeración de cuentas vía registro. Sin throttling, un
atacante puede probar miles de intentos por minuto.
**Remediar**: `flask-limiter` con backend de memoria o Redis:
```python
limiter.limit("5 per minute")(login)         # password
limiter.limit("10 per minute")(login_2fa)    # TOTP
limiter.limit("3 per hour")(forgot_password) # email enumeration
```

#### 16.2.C — `CORS(supports_credentials=True)` con orígenes abiertos
**Dónde**: `app.py` línea 40.
**Riesgo**: con `supports_credentials=True` y sin lista blanca de
origins, **cualquier sitio web** puede llamar a tu API desde el
navegador del usuario (`fetch('http://127.0.0.1:5000/api/...',
{credentials: 'include'})`) y leer la respuesta. El SameSite=Lax de
las cookies mitiga POST, pero GET (incluyendo `/api/me`, `/api/historial`)
queda expuesto a sitios externos cuando el usuario está logueado.
**Remediar**: limitar a orígenes específicos:
```python
CORS(app, supports_credentials=True,
     origins=["http://127.0.0.1:5000", "http://localhost:5000"])
```

#### 16.2.D — `SESSION_COOKIE_SECURE` no se activa
**Dónde**: `app.py` línea 38 — solo se configura `HttpOnly` y
`SameSite`.
**Riesgo**: cuando despliegues con HTTPS, sin el flag `Secure` las
cookies viajarán también por HTTP plano si un atacante fuerza un
downgrade (sslstrip, Wi-Fi público). En LAN no aplica, pero queda
abierto para producción.
**Remediar**: añadir `app.config["SESSION_COOKIE_SECURE"] = not Config.DEBUG`.

#### 16.2.E — TOTP sin protección contra reuso (anti-replay)
**Dónde**: `services/auth_service.py::verificar_2fa` y
`totp_service.verificar_codigo` (no inspeccionado pero típicamente
solo valida la ventana actual).
**Riesgo**: un atacante que ve el código TOTP (sobre el hombro, captura
de pantalla, malware en el dispositivo) tiene los 30 s de la ventana
actual + 30 s de la previa para usarlo **varias veces**. Si la
contraseña ya fue robada, el atacante puede reusar el mismo código
mientras esté vigente.
**Remediar**: guardar el último `counter` aceptado por usuario
(columna `last_totp_counter INT`) y rechazar códigos con counter ≤
último aceptado. Trivial con `pyotp.totp.TOTP.now()` → tomar el step
desde `time() // 30`.

#### 16.2.F — Enumeración de cuentas vía `/api/registro`
**Dónde**: `services/auth_service.py::registrar` línea 99 —
`"Ese correo ya está registrado."`.
**Riesgo**: un atacante puede probar emails uno a uno y saber cuáles
están registrados (útil para phishing dirigido). El endpoint
`/api/forgot-password` SÍ devuelve respuesta neutra (bien), pero
`/api/registro` no.
**Remediar**: cuando el email ya exista, enviar un correo silencioso
("alguien intentó registrarse con tu correo") y devolver la **misma
respuesta de éxito** ("revisa tu correo"). Patrón estándar en
servicios modernos.

#### 16.2.G — Posible XSS reflejado en el traductor
**Dónde**: `static/js/translator.js` línea 354 — inserta
`sena.palabra` vía `innerHTML` después de pasar por `prettyWord()`
(línea 576), que solo reemplaza `_` por espacio y **no escapa HTML**.
**Vector**: en el flujo `no_disponible`, `sena.palabra` viene de
`token.texto`, que se origina en el textarea del usuario. Si el
usuario teclea `<img src=x onerror=alert(1)>` y la palabra cae al
camino de `no_disponible`, se renderiza como HTML real.
**Riesgo**: self-XSS (el usuario se ataca solo) — bajo en práctica
porque no hay UGC compartido. Pero si en el futuro `/api/historial`
muestra texto de otros usuarios, escalaría a XSS real.
**Remediar**: en `prettyWord()` escapar `<>&"'` antes de devolver, o
usar `textContent` y construir el DOM con `createElement` (patrón ya
aplicado en `chat.js`).

---

### 16.3 — 🟡 MEDIOS (no bloquean entrega académica, mejorar cuando se pueda)

#### 16.3.A — `/api/historial` sin autenticación
**Dónde**: `routes/api.py::historial`.
**Riesgo**: devuelve `texto_original` e `ip_cliente` de TODAS las
traducciones. Cualquiera (con o sin cuenta) puede ver qué tradujeron
otros. Privacidad débil.
**Remediar**: exigir `session["user_id"]` y filtrar por
`usuario_id` (requiere primero agregar la columna — ver 15.2.C).

#### 16.3.B — `/api/chat` sin auth ni throttle
**Dónde**: `routes/api.py::chat`.
**Riesgo**: un atacante puede saturar el CPU del servidor pidiendo
respuestas continuamente a Llama 3 (cada inferencia dura varios
segundos y ocupa todos los cores). Denegación de servicio efectiva
con muy poco esfuerzo.
**Remediar**: exigir login + `flask-limiter` (`@limiter.limit("10 per
minute")`).

#### 16.3.C — IP del cliente confiada desde `X-Forwarded-For` sin proxy validado
**Dónde**: `routes/api.py::_ip_cliente`.
**Riesgo**: hoy NO hay proxy reverso, así que cualquiera puede mandar
`X-Forwarded-For: 1.2.3.4` y falsificar la IP del historial. Útil
para evadir auditoría.
**Remediar**: solo leer ese header cuando un proxy de confianza esté
configurado (`werkzeug.middleware.proxy_fix.ProxyFix(app.wsgi_app,
x_for=1)`). Hasta entonces, usar solo `request.remote_addr`.

#### 16.3.D — Recovery file no se invalida tras uso
**Dónde**: `services/auth_service.py::usar_recovery_file`.
**Riesgo**: el `recovery_file_hash` queda igual después de usarlo,
así que un atacante que obtuvo una copia del archivo puede usarlo
indefinidamente. Distinto de los recovery codes (que sí se marcan
como `usado=1`).
**Remediar**: rotar el `recovery_file_hash` después de cada uso
exitoso y enviar el nuevo archivo por email automáticamente. O
considerarlo de un solo uso y obligar a generar uno nuevo desde el
panel del usuario.

#### 16.3.E — `confirmar_reset` no invalida sesiones existentes
**Dónde**: `services/auth_service.py::confirmar_reset`.
**Riesgo**: si un atacante secuestra una sesión activa, el usuario
real puede resetear su contraseña pensando que va a expulsar al
atacante — pero la sesión del atacante sigue funcionando porque la
cookie firmada sigue siendo válida.
**Remediar**: rotar el `SECRET_KEY` de la cookie por usuario
(columna `session_version INT`) e incrementarla al cambiar password.
Validar en cada request que `session_version` coincida.

#### 16.3.F — Logging incluye PII (emails)
**Dónde**: `services/email_service.py` línea 65 — `logger.info("Email
enviado a %s asunto=%r", destinatario, asunto)`.
**Riesgo**: los emails registrados van a stdout/disco. Si los logs se
publican accidentalmente (ej. en un repo de GitHub o capturas de
pantalla), se filtran direcciones personales.
**Remediar**: hash o trunco del email en logs:
`destinatario[:3] + "***@" + destinatario.split("@",1)[1]`.

#### 16.3.G — Recovery file: sin límite de tamaño en upload
**Dónde**: `routes/api.py::login_recovery_file`.
**Riesgo**: `archivo.read()` lee todo el contenido sin validar tamaño.
Flask aplica `MAX_CONTENT_LENGTH` global (no configurado), por defecto
sin límite. Un atacante puede enviar un archivo gigantesco y agotar
memoria.
**Remediar**: `app.config["MAX_CONTENT_LENGTH"] = 64 * 1024` (64 KB
sobra para un `recovery.txt`).

---

### 16.4 — 🟢 BAJOS (cosméticos / hardening avanzado)

#### 16.4.A — `_serializar_usuario` revela `totp_enabled`
Aunque útil para la UI propia, expone públicamente qué cuentas tienen
2FA, ayudando a un atacante a priorizar objetivos. Solo enviar el
flag al propio usuario en `/api/me`, no en respuestas de login (donde
ya se sabe si requiere_2fa).

#### 16.4.B — `setup_2fa_data`: rama muerta de secreto sin persistir
`routes/api.py` línea 339–343: si `fila["totp_secret"]` fuese `None`
genera un secreto que **no se persiste**, así que `activar_2fa` no lo
encontrará. En práctica nunca se ejecuta porque registro siempre
asigna `totp_secret`, pero es código que dice una cosa y hace otra.
**Remediar**: borrar la rama o persistir el secreto generado.

#### 16.4.C — Sin headers de seguridad HTTP
Faltan: `X-Content-Type-Options: nosniff`, `Referrer-Policy:
same-origin`, `Content-Security-Policy` (al menos
`default-src 'self'; img-src 'self' data:; media-src 'self'`),
`X-Frame-Options: DENY`. Trivial de añadir con `flask-talisman`.

#### 16.4.D — Recovery codes generados con alfabeto de 31 caracteres
`auth_service.py` línea 333: `"ABCDEFGHJKMNPQRSTUVWXYZ23456789"` (sin
I/L/O/0/1 para evitar ambigüedades). Está bien diseñado, pero formato
`XXXX-XXXX` da solo 31⁸ ≈ 8·10¹¹ combinaciones; con 8 códigos
activos por usuario, espacio efectivo ≈ 10¹¹. Suficiente para 2FA
backup, pero no usarlo como mecanismo principal de auth.

#### 16.4.E — Migración suave de columnas captura `Exception` muda
`models/usuario.py` líneas 78–82: ignora cualquier error en `ALTER
TABLE`. Si una columna falla por una razón distinta a "ya existe"
(permisos, charset incompatible), no te enterarás hasta que algo
explote en runtime.
**Remediar**: capturar solo `pymysql.err.OperationalError` con código
`1060` (Duplicate column).

---

### 16.5 — ✅ Bien implementado (no tocar)

- **SQL Injection**: todas las consultas usan parámetros ligados
  (`%s`) en `pymysql`. La whitelist de campos en
  `DiccionarioRepository.actualizar` previene inyección por nombre de
  columna.
- **Password hashing**: `werkzeug.security.generate_password_hash`
  usa `scrypt` con sal aleatoria. Resistente a rainbow tables y
  brute-force con GPU.
- **Comparación de tokens**: `hmac.compare_digest` en
  `usar_recovery_code` y `usar_recovery_file` previene ataques de
  timing.
- **OAuth state**: `secrets.token_urlsafe(24)` + verificación con
  `state_recibido != state_esperado` antes del intercambio. Bloquea
  CSRF en el callback de Google.
- **Reset token TTL**: 15 minutos, invalidación de pendientes antes
  de crear uno nuevo, marcado como `usado=1` tras éxito. Implementación
  correcta.
- **`.gitignore`** cubre `.env`, `venv/`, `__pycache__/`, logs y
  `*.db/*.sqlite`. Bien.
- **`render_template`** usa Jinja2 con autoescape activado por
  defecto (`.html`). No hay `|safe` ni `Markup()` en plantillas.
- **Chat IA**: `chat.js::addMessage` usa `textContent` y
  `createElement`. Sin XSS en la zona de mayor riesgo.

---

### 16.6 — Plan de remediación priorizado

| Orden | Acción | Esfuerzo | Severidad |
|---|---|---|---|
| 1 | Rotar Gmail App Password (16.1.A) | 5 min | 🔴 |
| 2 | `FLASK_DEBUG=False` + `HOST=127.0.0.1` (16.1.B) | 1 min | 🔴 |
| 3 | Poner password a MySQL root + usuario dedicado (16.1.C) | 10 min | 🔴 |
| 4 | Generar `SECRET_KEY` aleatorio (16.1.D) | 2 min | 🔴 |
| 5 | `flask-limiter` en login/2fa/forgot (16.2.B) | 2 h | 🟠 |
| 6 | Lista blanca de CORS (16.2.C) | 5 min | 🟠 |
| 7 | `SESSION_COOKIE_SECURE` condicional (16.2.D) | 2 min | 🟠 |
| 8 | TOTP anti-replay con `last_counter` (16.2.E) | 1 h | 🟠 |
| 9 | Escape HTML en `prettyWord` (16.2.G) | 5 min | 🟠 |
| 10 | `flask-wtf` CSRF global (16.2.A) | 2 h | 🟠 |
| 11 | Auth + throttle en `/api/chat` y `/api/historial` (16.3.A/B) | 30 min | 🟡 |
| 12 | `MAX_CONTENT_LENGTH` para uploads (16.3.G) | 1 min | 🟡 |
| 13 | Hash de emails en logs (16.3.F) | 10 min | 🟡 |
| 14 | `flask-talisman` para headers (16.4.C) | 15 min | 🟢 |

**Lectura**: con 4–5 horas de trabajo enfocado, el proyecto pasa de
"código académico funcional" a "código mínimamente seguro para
demostración en red local". Para exposición pública en internet se
necesita además 15.4.A (HTTPS, dominio, proxy reverso).

---

## 17. Cierre del proyecto — lo que realmente falta para entregar

Esta sección agrupa lo MÍNIMO necesario para que Señas Co se presente
como proyecto cerrado en la sustentación del diplomado, separando lo
**indispensable** de lo **opcional aspiracional**.

### 17.1 — Indispensable (sin esto el proyecto queda inconsistente)

1. **Cobertura del diccionario para sustantivos comunes**
   (ver 15.1.D — P0).
   **Por qué bloquea**: hoy "Yo veo a mi mamá" deja "mamá" como
   `no_disponible`. La presentación quedaría flaca sin sustantivos
   familiares básicos. **Recomendado**: 30 nuevas entradas mínimo
   (familiares + roles cotidianos). Tiempo estimado: 2–3 horas si
   los videos del INSOR están descargados.

2. **Frase canónica con video de intérprete real** como prueba de
   concepto (1 sola es suficiente). El video del INSOR que mandaste
   (`colombia_dos_mares.m4v`) es perfecto. **Por qué importa**:
   demostrar que el sistema soporta el modo "frase fija con
   intérprete real" además del modo "TSOV con clips". Es la
   diferencia entre "experimento de NLP" y "herramienta híbrida".
   Tiempo: 10 minutos (descargar + 1 INSERT en BD).

3. **Cierre de la dactilología "perro"** (NO se debe deletrear).
   Verificar: `SELECT palabra, tipo FROM senas WHERE palabra='perro';`.
   Si no existe → agregar entrada. Si existe pero el sistema sigue
   deletreándolo → mirar si spaCy lo etiqueta como `PROPN`
   (debug con `python -c "import spacy; n=spacy.load('es_core_news_md');
   print([(t.text,t.pos_,t.lemma_) for t in n('perro')])"`).
   **Tiempo**: 15 minutos.

4. **Rotación de credenciales filtradas** (ver 16.1.A): rotar Gmail
   App Password antes de mostrar el proyecto a cualquiera. **Tiempo**:
   5 minutos.

5. **Apagar `FLASK_DEBUG` y restringir HOST** (ver 16.1.B). Crítico
   incluso para demo local porque cualquier excepción en pantalla
   abre el debugger PIN. **Tiempo**: 1 minuto.

6. **Variables de entorno seguras**: `SECRET_KEY` aleatoria
   (16.1.D), `DB_PASSWORD` no vacía (16.1.C). **Tiempo**: 5 minutos.

7. **Documento de presentación / README ejecutivo**: el actual
   `PROJECT_CONTEXT.md` es interno; falta un README breve y vendible
   (1–2 páginas) para la mesa evaluadora. Debe explicar: qué resuelve,
   qué NO resuelve, cómo se ejecuta, y una guía de 5 ejemplos para
   demostrar en vivo.

**Tiempo total indispensable**: ≈ 4–5 horas de trabajo enfocado.

### 17.2 — Recomendado (eleva calidad de la sustentación)

1. **15.1.C** — expandir conjugaciones a ~150 verbos (1 día).
2. **15.1.B** — detección fuzzy de frases canónicas (2–3 días).
3. **16.2.B** — rate limiting básico en login (2 horas).
4. **16.2.A** — CSRF global con flask-wtf (2 horas).
5. **15.4.C** — suite mínima de tests (10–15 tests sobre el pipeline
   TSOV y el flujo de auth). Da una garantía de regresión y se ve
   bien en la rúbrica.

**Tiempo recomendado total**: ≈ 1 semana de trabajo.

### 17.3 — Fuera del alcance académico (mencionar en presentación pero no implementar)

- **Avatar 3D LSC** (15.3.A) — declarar como "trabajo futuro" con
  el análisis de viabilidad ya documentado en sección 15.
- **Reconocimiento LSC → texto** (15.3.B).
- **Modelo NLP fine-tuned con corpus LSC** (15.3.C).
- **Despliegue público con HTTPS** (15.4.A) — el proyecto se entrega
  en LAN local, no en internet abierta.

### 17.4 — Mensaje claro para la sustentación

> "Señas Co traduce español a LSC con tres modos complementarios:
> (1) frases canónicas con video de intérprete real cuando existen;
> (2) glosa TSOV con clips aislados + marcadores no manuales
> + concordancia direccional cuando no; (3) dactilología SOLO para
> nombres propios y siglas, nunca para palabras comunes. La
> limitación principal es la cobertura del diccionario, no la
> arquitectura; el sistema escala añadiendo entradas a la BD sin
> tocar código. El avatar 3D y el reconocimiento bidireccional
> quedan documentados como trabajo futuro de escala industrial."

---

## 18. Rastro de sesiones

Resumen de cambios por sesión, en orden cronológico inverso (más reciente
arriba). Sirve para entender en qué estado quedó cada hito sin tener que
leer todo el chat.

### Sesión 2026-05-14 — Auditoría de seguridad + cierre del proyecto

**Pedido del usuario**: revisar TODO el proyecto evaluando seguridad,
errores críticos y vulnerabilidades. Recapitular en el documento lo
que falta para cerrar el proyecto. Aclarar si está bien o mal que
palabras como "perro", "marcela", "carlitos" se deletreen letra por
letra.

**Cambios aplicados** (cero código, solo documentación):

1. **Sección 16 nueva — Auditoría de seguridad**: revisión completa
   de `app.py`, `routes/api.py`, `services/auth_service.py`,
   `services/email_service.py`, `services/google_oauth_service.py`,
   `services/chat_service.py`, `services/traductor_service.py`,
   `models/*`, `database/connection.py`, `static/js/*`, `.env`.
   Resultado: **24 hallazgos** clasificados por severidad:
   - **4 críticos (🔴)**: App Password expuesta, FLASK_DEBUG+HOST,
     MySQL root sin password, SECRET_KEY débil.
   - **7 altos (🟠)**: sin CSRF, sin rate limiting, CORS abierto,
     SESSION_COOKIE_SECURE, TOTP replay, enumeración de cuentas en
     registro, XSS reflejado en translator.js.
   - **7 medios (🟡)**: /api/historial y /api/chat sin auth,
     X-Forwarded-For falsificable, recovery file no se invalida,
     reset no invalida sesiones, logs con PII, upload sin límite
     de tamaño.
   - **5 bajos (🟢)**: revela totp_enabled, rama muerta en
     setup_2fa_data, sin headers HTTP, espacio de recovery codes,
     migración silencia excepciones.
   - **Tabla 16.5 con lo bien implementado**: SQL injection cubierta,
     scrypt para passwords, hmac.compare_digest, OAuth state,
     reset token TTL, .gitignore, Jinja autoescape, chat.js sin
     XSS.
   - **Tabla 16.6 plan de remediación** con esfuerzo estimado: 4–5
     horas para pasar de "académico" a "mínimamente seguro".

2. **Sección 17 nueva — Cierre del proyecto**: separa lo
   indispensable de lo opcional para la sustentación. Identifica 7
   items críticos (≈5 h de trabajo) + recomendaciones (≈1 semana) +
   fuera de alcance (avatar 3D, etc.).

3. **Aclaración sobre dactilología** (también discutida en chat):
   - `marcela`, `carlitos`, `bryan` → deletreo es CORRECTO en LSC
     (PROPN sin name sign asignado).
   - `perro`, `casa`, `agua` → deletreo es INCORRECTO en LSC.
     Estas palabras tienen seña propia. Si el sistema las deletrea
     es por una de dos razones: (a) la palabra no está en BD —
     cobertura insuficiente (P0 en roadmap, 15.1.D); o (b) spaCy
     las etiqueta como PROPN al inicio de oración (la remediación
     en `nlp_service.remediar_inicio_oracion` ya cubre verbos pero
     no sustantivos comunes).

4. **Renumerada sección "Rastro de sesiones" de 16 a 18** para hacer
   sitio a las secciones de seguridad y cierre.

**Acción inmediata recomendada al usuario**:
- Rotar Gmail App Password en <https://myaccount.google.com/apppasswords>.
- Cambiar `FLASK_DEBUG=False` y `HOST=127.0.0.1` en `.env`.
- Asignar password a `root` de MySQL via phpMyAdmin.
- Generar `SECRET_KEY` aleatoria con `secrets.token_urlsafe(32)`.

**Segunda iteración (mismo día) — caso "perro" resuelto + P0 parcialmente cerrado**:

5. **`database/seed_data.sql` sección 17 nueva**: añadidas **10
   entradas de sustantivos comunes** que faltaban en BD y son P0:
   `perro, gato, mama, papa, niño, niña, bebe, amigo, amiga,
   familia`. Header del archivo actualizado de "160 palabras" a
   "170 palabras", total 212 entradas.

6. **`database/seed_sustantivos_p0.sql` nuevo**: script standalone
   con `INSERT IGNORE` para aplicar las 10 entradas a la BD viva
   sin truncar el resto. Idempotente (se puede correr varias
   veces). Aplicar con `mysql -u root traductor_lsc <
   database/seed_sustantivos_p0.sql` o desde phpMyAdmin.

7. **`GIFS_CHECKLIST.md` actualizado**:
   - Contador total: 202 → 212.
   - Sección nueva "Sustantivos comunes P0 — pendientes" con tabla
     de los 10 archivos a conseguir y nota técnica sobre el
     mapeo BD-con-ñ ↔ archivo-sin-ñ (el `gif_url` en BD ya apunta
     a la ruta sin ñ; no hay magia en runtime, solo el resolver
     cambia la extensión).

8. **Diagnóstico técnico del caso "perro"**:
   - Confirmado: `perro` no estaba en `seed_data.sql` ni había
     archivo en `static/gifs/palabras/`.
   - Causa raíz cuando aparecía DELETREADO: spaCy etiqueta "Perro"
     como `PROPN` al inicio de oración (falso positivo del POS
     tagger). La regla `_debe_deletrearse` deletreaba todo PROPN.
   - Causa raíz cuando aparecía GRIS: spaCy etiqueta "perro" en
     minúscula como `NOUN`, pero la palabra no estaba en BD.
   - **Fix aplicado**: agregar a BD. El lookup en BD se hace
     ANTES de la regla de deletreo (línea 470 de
     `traductor_service.py`), así que aunque siga llegando como
     PROPN, la entrada en BD se encuentra primero y deja de
     deletrearlo.
   - **`remediar_inicio_oracion` solo cubre PROPN→VERB**; no
     intenta corregir PROPN→NOUN porque sería frágil sin un
     diccionario explícito de sustantivos comunes.

**Pendiente físico para el usuario**:
- Descargar los 10 videos LSC del INSOR
  (<https://educativo.insor.gov.co/diccionario/>) y colocarlos como
  `perro.mp4, gato.mp4, mama.mp4, papa.mp4, nino.mp4, nina.mp4,
  bebe.mp4, amigo.mp4, amiga.mp4, familia.mp4` en
  `static\gifs\palabras\`. Sin tilde y sin ñ en los nombres de
  archivo (Windows + servidor web).

### Sesión 2026-05-07 — Roadmap detallado y video INSOR como referencia

**Pedido del usuario**: ampliar el documento de contexto con un roadmap
exhaustivo de mejoras futuras (lo que se puede hacer, lo que está
lejos del alcance, qué implica un avatar 3D), y aclarar cómo integrar
videos específicos del INSOR (referencia: video de "Colombia tiene
dos mares, uno en el Pacífico y uno en el Atlántico" en
`https://educativo.insor.gov.co/wp-content/uploads/2020/12/03-Dos-Ejemplo-1.m4v`).

**Cambios aplicados** (cero código, solo documentación):
1. Sección 15 nueva: **Roadmap detallado de mejoras futuras** con 4
   tiers (1: días/alto impacto; 2: semanas; 3: meses/avanzado; 4:
   operacional) y 22 propuestas concretas detalladas con costo,
   dependencias y veredicto.
2. Tabla resumen de prioridades P0–P5.
3. Renumerada "Rastro de sesiones" a sección 16.
4. Sección 10 (estado pendiente) reescrita para apuntar a la nueva
   sección 15 en lugar de listar items inline.

**Recomendaciones puestas en P0–P1 (prioridad máxima)**:
- 15.1.D: Sustantivos comunes faltantes en BD (`mamá, papá, niño…`).
- 15.1.A: Frases canónicas con video de intérprete real.
- 15.1.C: Diccionario de conjugaciones expandido (~150 verbos más).
- 15.1.B: Detección fuzzy de frases canónicas (matchear "Colombia
  tiene dos mares" → `colombia_dos_mares`).

**Lejos del alcance académico** (P5): avatar 3D LSC fiel
(HamNoSys+SiGML+WebGL → 1-2 años, $30K-$100K), reconocimiento LSC →
español por visión (frontera de investigación, requiere corpus
inexistente).

### Sesión 2026-05-06 — Marcadores no manuales + concordancia direccional

**Pedido del usuario**: implementar las dos mejoras opcionales restantes
(marcadores no manuales + concordancia verbal espacial). Saltar avatar
3D para más adelante.

**Cambios aplicados**:
1. **Nuevo módulo `services/marcadores_lsc.py`**:
   - Constantes `Marcador(codigo, label, icono)` para CEJAS_ARRIBA,
     CEJAS_FRUNCIDAS, CABEZA_NO, CABEZA_SI, TOPICO.
   - Set `VERBOS_DIRECCIONALES` con 20 verbos comunes en LSC.
   - Mapping `_PUNTOS_PRONOMBRE` para asociar pronombres a puntos del
     espacio LSC (`yo, tú, él/ella, nosotros, ustedes, ellos`).
   - Función `construir_direccion(sujeto_lema, objeto_lema)` para
     pronombres explícitos.
   - Función `inferir_direccion_global(texto)` con 18 patrones regex
     que reconocen combinaciones sujeto+clítico (`yo te X`, `tú me X`,
     `él me X`, etc.) en el texto crudo, antes del filtro funcional.
2. **Sena extendida**: 5 campos nuevos (`marcador_codigo`, `marcador_label`,
   `marcador_icono`, `direccion`, `direccion_label`).
3. **`TraductorService._anotar_marcadores`**: nuevo paso 10.b después de
   resolver señas y antes de construir la glosa string. No modifica el
   orden ni la composición — solo adjunta info gramatical.
4. **`TraductorService._anotar_direccionales`**: heurística cascada —
   primero pronombres explícitos en la cláusula, fallback a regex sobre
   texto crudo. Lematiza `sena.palabra` con el dict de verbos para
   reconocer formas conjugadas en casos no_disponible.
5. **`lematizador_verbos.py` ampliado**: añadidos `dar` (doy/das/da/...),
   `traer`, `poner`, `hacer`, `decir/dijo` ya estaba.
6. **BD ampliada**: nuevas entradas `dar, decir, traer, llevar` (verbos
   direccionales que faltaban). Total ahora: **208 entradas**.
7. **Frontend**: dos overlays nuevos en el reproductor de video:
   - Pill superior izquierda (color según marcador) con el icono y label
     del marcador no manual.
   - Pill amarilla superior derecha con la flecha direccional.
   - Animación `nmm-in` (fade + slide) al cambiar de seña.
   - JS `actualizarOverlaysGramaticales(sena)` se llama en cada cambio.

**Verificación end-to-end**:
- "¿Comes pan?" → ambas señas con cejas_arriba (pregunta sí/no)
- "¿Dónde estudias?" → ESTUDIAR cejas_arriba, DONDE cejas_fruncidas
- "Yo no quiero comer" → YO con tópico, NO con cabeza_no
- "Yo te ayudo" → ayudar con `[yo → tú]`
- "Tú me das pan" → dar con `[tú → yo]`
- "Él me dijo" → hablar con `[él/ella → yo]`
- "Te traigo café" → traer con `[yo → tú]` (clítico implícito)
- "Quiero comer manzana y beber agua" → manzana con tópico, separación `·` entre cláusulas

### Sesión 2026-05-05 — Fidelidad LSC + optimizaciones

**Pedido del usuario**: aplicar las mejoras documentadas como pendientes
para que el proyecto sea más fiel a LSC, optimizar la carga del
diccionario, añadir entradas faltantes a la BD, arreglar el bug de
"adios" no detectado.

**Cambios aplicados**:
1. **Segmentación de cláusulas** (`services/traductor_service.py`):
   - Nueva constante `COORDINADORES = {"y","e","o","u","pero","sino","porque"}`.
   - Método `_segmentar_clausulas(tokens)` que parte la lista en bloques.
   - Pipeline reescrito: etapas C+F se aplican **por cláusula**, no globalmente.
   - Nuevo campo `clausula_idx` en `Token` y `clausula` en `Sena`.
   - Glosa muestra `·` cuando cambia el índice de cláusula (`_construir_glosa_string`).
2. **Dict manual de conjugaciones** (`services/lematizador_verbos.py`, NUEVO):
   - 23 verbos regulares expandidos con paradigmas completos (-ar/-er/-ir).
   - 14 verbos irregulares declarados manualmente (ser, estar, tener, querer, poder, ir, venir, decir, saber, ver, dormir, sentir, pensar, jugar).
   - ~250 entradas totales después de excluir formas ambiguas.
   - Aplicado en `nlp_service.procesar()` antes de devolver el `Token`.
3. **Fallback de búsqueda en BD** (`services/traductor_service.py::_resolver_senas`):
   - Si `token.clave` (lema) no aparece en la BD, prueba con `normalizar(token.texto)` (la forma superficial).
   - Cubre el bug de `"adios"` que spaCy lematiza como `"adio"`.
   - Helper `_buscar_en_bd(palabra)` para lookups individuales.
4. **Lazy loading de videos** (`static/js/diccionario.js`):
   - IntersectionObserver con `rootMargin: '300px 0px'`.
   - Videos creados con `preload="none"` y `data-src` en lugar de `src` directo.
   - Al entrar al viewport: inyecta `src`, `load()`, `play()`.
   - Al salir: `pause()` para liberar decoder.
   - `unobserve` al re-renderizar para evitar leaks.
5. **Nuevas entradas en BD**:
   - `con_gusto` (frase, saludos) — apunta a `con_gusto.gif` (tiene MP4 en disco).
   - `rosado` (palabra, colores) — apunta a `rosado.gif` (tiene MP4 en disco).
   - Añadidas en `database/seed_data.sql` y aplicadas a la BD viva con INSERT IGNORE.
6. **Disclaimer del traductor actualizado** (`templates/translator.html`):
   - Reconoce que ahora son "videos" (no solo GIFs estáticos).
   - Mantiene la honestidad sobre limitaciones (expresiones faciales, clasificadores).

**Verificación**:
- "Quiero comer manzana y beber agua" → `MANZANA QUERER COMER · AGUA BEBER` ✅
- "Mañana iré al colegio porque quiero estudiar" → `MAÑANA · COLEGIO IR · QUERER ESTUDIAR` ✅
- "Comeré pan y beberé agua" → `PAN COMER · AGUA BEBER` ✅
- "adios" sin tilde → `ADIOS` ✅
- "Te digo adiós" → `ADIOS HABLAR` ✅
- Diccionario carga sin tirones (lazy de los 200+ videos).

### Sesión 2026-05-04 — Pipeline LSC + auth + chat IA

- Pipeline LSC etapas A → G implementado.
- Soporte mixto MP4 + GIF con resolver dinámico.
- Sistema de auth completo (registro, login, 2FA, recovery, OAuth Google, SMTP).
- Chat IA local con Llama 3 8B.
- Cortocircuito para letra única + secuencia de letras.
- Documento `PROJECT_CONTEXT.md` (este) creado.

### Sesión 2026-05-03 — Fundamentos del traductor

- Estructura inicial: Flask factory, blueprints, MySQL, spaCy.
- Diccionario sembrado con 202 entradas.
- Reproductor de GIFs en el traductor.
- Vistas institucionales (home, traductor, diccionario).
