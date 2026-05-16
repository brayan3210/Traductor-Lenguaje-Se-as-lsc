# Checklist de recursos visuales LSC

Esta es la guía completa de los **202 archivos** que necesitas conseguir
para que el traductor muestre todas las señas. Es un documento vivo: ve
marcando lo que tengas y descartando lo que ya esté hecho.

> **Sobre el formato**: los archivos pueden ser `.gif` o `.mp4`. Si el
> reproductor todavía está en modo solo-GIF, convierte el MP4 con
> [ezgif.com/video-to-gif](https://ezgif.com/video-to-gif). Cuando se
> habilite soporte nativo MP4 en la app, podrás dejar el MP4 tal cual.

---

## 🌐 Fuentes recomendadas (en orden de calidad y autoridad)

| Fuente | URL | Tipo | Notas |
|---|---|---|---|
| **INSOR Educativo** | <https://educativo.insor.gov.co/diccionario/> | MP4 | Fuente oficial Colombia. Calidad alta. **Primera opción siempre**. |
| **FENASCOL** (Federación Nacional de Sordos de Colombia) | <https://fenascol.org.co/> | MP4 / YouTube | Material institucional. |
| **Spread The Sign — Colombia** | <https://www.spreadthesign.com/es.co/search/> | MP4 | Filtra "Español (Colombia)". Más amplio que INSOR. |
| **Centro de Relevo (MinTIC)** | <https://centroderelevo.gov.co> | Videos | Servicio oficial; útil para frases. |
| **YouTube — INSOR Oficial** | <https://www.youtube.com/@insorcolombia> | Video | Series didácticas. Recortar con [yt-dlp](https://github.com/yt-dlp/yt-dlp) o [SaveTube]. |
| **YouTube — FENASCOL Oficial** | <https://www.youtube.com/@fenascol> | Video | Series didácticas. |

⚠️ **Importante**: respeta los créditos. Si el proyecto es académico está
bien usar el material; si lo subes público a producción, cita la fuente
en cada video y pide autorización formal.

---

## 📂 `static/gifs/letras/` — 27 archivos

**Categoría**: alfabeto dactilológico LSC (deletreo manual).
**Búsqueda en INSOR**: "alfabeto", "dactilológico", "abecedario"
**Búsqueda en YouTube**: "alfabeto LSC", "abecedario lengua de señas colombiana".

| Archivo | Letra | Buscar literal | ✓ |
|---|---|---|---|
| `a.gif` | A | "letra A LSC" / "A dactilológico" | ☐ |
| `b.gif` | B | "letra B LSC" | ☐ |
| `c.gif` | C | "letra C LSC" | ☐ |
| `d.gif` | D | "letra D LSC" | ☐ |
| `e.gif` | E | "letra E LSC" | ☐ |
| `f.gif` | F | "letra F LSC" | ☐ |
| `g.gif` | G | "letra G LSC" | ☐ |
| `h.gif` | H | "letra H LSC" | ☐ |
| `i.gif` | I | "letra I LSC" | ☐ |
| `j.gif` | J | "letra J LSC" | ☐ |
| `k.gif` | K | "letra K LSC" | ☐ |
| `l.gif` | L | "letra L LSC" | ☐ |
| `m.gif` | M | "letra M LSC" | ☐ |
| `n.gif` | N | "letra N LSC" | ☐ |
| `n_enye.gif` | Ñ | "letra Ñ LSC" / "letra eñe" | ☐ |
| `o.gif` | O | "letra O LSC" | ☐ |
| `p.gif` | P | "letra P LSC" | ☐ |
| `q.gif` | Q | "letra Q LSC" | ☐ |
| `r.gif` | R | "letra R LSC" | ☐ |
| `s.gif` | S | "letra S LSC" | ☐ |
| `t.gif` | T | "letra T LSC" | ☐ |
| `u.gif` | U | "letra U LSC" | ☐ |
| `v.gif` | V | "letra V LSC" | ☐ |
| `w.gif` | W | "letra W LSC" | ☐ |
| `x.gif` | X | "letra X LSC" | ☐ |
| `y.gif` | Y | "letra Y LSC" | ☐ |
| `z.gif` | Z | "letra Z LSC" | ☐ |

> 💡 **Truco**: muchos canales de YouTube tienen el alfabeto entero en un
> solo video. Con [yt-dlp + ffmpeg] puedes recortar segmentos:
> `ffmpeg -i alfabeto.mp4 -ss 00:01:23 -t 2 a.mp4`

---

## 📂 `static/gifs/palabras/` — 175 archivos

### 1. Números (11)
**Buscar**: "número 0 LSC", "uno LSC", … o "números del 0 al 10 LSC"

| Archivo | Palabra | ✓ |
|---|---|---|
| `cero.gif` | 0 | ☐ |
| `uno.gif` | 1 | ☐ |
| `dos.gif` | 2 | ☐ |
| `tres.gif` | 3 | ☐ |
| `cuatro.gif` | 4 | ☐ |
| `cinco.gif` | 5 | ☐ |
| `seis.gif` | 6 | ☐ |
| `siete.gif` | 7 | ☐ |
| `ocho.gif` | 8 | ☐ |
| `nueve.gif` | 9 | ☐ |
| `diez.gif` | 10 | ☐ |

### 2. Saludos y cortesía (15)
**Buscar**: "saludos LSC", "hola lengua de señas", "buenos días LSC"

| Archivo | Palabra | ✓ |
|---|---|---|
| `hola.gif` | hola | ☐ |
| `adios.gif` | adiós | ☐ |
| `gracias.gif` | gracias | ☐ |
| `por_favor.gif` | por favor | ☐ |
| `perdon.gif` | perdón | ☐ |
| `buenos_dias.gif` | buenos días | ☐ |
| `buenas_tardes.gif` | buenas tardes | ☐ |
| `buenas_noches.gif` | buenas noches | ☐ |
| `bienvenido.gif` | bienvenido | ☐ |
| `como_estas.gif` | ¿cómo estás? | ☐ |
| `bien.gif` | bien | ☐ |
| `mal.gif` | mal | ☐ |
| `mas_o_menos.gif` | más o menos | ☐ |
| `mucho_gusto.gif` | mucho gusto | ☐ |
| `hasta_luego.gif` | hasta luego | ☐ |

### 3. Familia (10)
**Buscar**: "familia LSC", "papá mamá hermano LSC"

| Archivo | Palabra | ✓ |
|---|---|---|
| `madre.gif` | madre / mamá | ☐ |
| `padre.gif` | padre / papá | ☐ |
| `hermano.gif` | hermano | ☐ |
| `hermana.gif` | hermana | ☐ |
| `hijo.gif` | hijo | ☐ |
| `hija.gif` | hija | ☐ |
| `abuelo.gif` | abuelo | ☐ |
| `abuela.gif` | abuela | ☐ |
| `esposo.gif` | esposo | ☐ |
| `esposa.gif` | esposa | ☐ |

### 4. Verbos básicos (31)
**Buscar**: "verbo X LSC", "[verbo en infinitivo] lengua de señas colombiana"

| Archivo | Verbo | ✓ |
|---|---|---|
| `ser.gif` | ser | ☐ |
| `estar.gif` | estar | ☐ |
| `tener.gif` | tener | ☐ |
| `querer.gif` | querer | ☐ |
| `poder.gif` | poder | ☐ |
| `ir.gif` | ir | ☐ |
| `venir.gif` | venir | ☐ |
| `comer.gif` | comer | ☐ |
| `beber.gif` | beber / tomar | ☐ |
| `dormir.gif` | dormir | ☐ |
| `trabajar.gif` | trabajar | ☐ |
| `estudiar.gif` | estudiar | ☐ |
| `hablar.gif` | hablar | ☐ |
| `escuchar.gif` | escuchar / oír | ☐ |
| `ver.gif` | ver | ☐ |
| `llamar.gif` | llamar | ☐ |
| `ayudar.gif` | ayudar | ☐ |
| `necesitar.gif` | necesitar | ☐ |
| `saber.gif` | saber | ☐ |
| `vivir.gif` | vivir | ☐ |
| `cantar.gif` | cantar | ☐ |
| `jugar.gif` | jugar | ☐ |
| `leer.gif` | leer | ☐ |
| `escribir.gif` | escribir | ☐ |
| `correr.gif` | correr | ☐ |
| `caminar.gif` | caminar | ☐ |
| `bailar.gif` | bailar | ☐ |
| `cocinar.gif` | cocinar | ☐ |
| `mirar.gif` | mirar | ☐ |
| `sentir.gif` | sentir | ☐ |
| `pensar.gif` | pensar | ☐ |

### 5. Colores (8)
**Buscar**: "colores LSC"

| Archivo | Color | ✓ |
|---|---|---|
| `rojo.gif` | rojo | ☐ |
| `azul.gif` | azul | ☐ |
| `verde.gif` | verde | ☐ |
| `amarillo.gif` | amarillo | ☐ |
| `blanco.gif` | blanco | ☐ |
| `negro.gif` | negro | ☐ |
| `naranja.gif` | naranja | ☐ |
| `morado.gif` | morado / lila | ☐ |

### 6. Preguntas / interrogativos (7)
**Buscar**: "interrogativos LSC", "qué quién dónde cuándo cómo cuánto LSC"

| Archivo | Palabra | ✓ |
|---|---|---|
| `que.gif` | qué | ☐ |
| `quien.gif` | quién | ☐ |
| `donde.gif` | dónde | ☐ |
| `cuando.gif` | cuándo | ☐ |
| `como.gif` | cómo | ☐ |
| `cuanto.gif` | cuánto | ☐ |
| `por_que.gif` | por qué | ☐ |

### 7. Lugares (14)
**Buscar**: "lugares LSC", "casa colegio hospital LSC"

| Archivo | Palabra | ✓ |
|---|---|---|
| `casa.gif` | casa | ☐ |
| `colegio.gif` | colegio / escuela | ☐ |
| `hospital.gif` | hospital | ☐ |
| `tienda.gif` | tienda | ☐ |
| `parque.gif` | parque | ☐ |
| `iglesia.gif` | iglesia | ☐ |
| `banco.gif` | banco | ☐ |
| `restaurante.gif` | restaurante | ☐ |
| `calle.gif` | calle | ☐ |
| `ciudad.gif` | ciudad | ☐ |
| `oficina.gif` | oficina | ☐ |
| `supermercado.gif` | supermercado | ☐ |
| `farmacia.gif` | farmacia / droguería | ☐ |
| `trabajo.gif` | trabajo | ☐ |

### 8. Adjetivos (17)
**Buscar**: "adjetivos LSC", "grande pequeño bueno malo LSC"

| Archivo | Adjetivo | ✓ |
|---|---|---|
| `grande.gif` | grande | ☐ |
| `pequeno.gif` | pequeño | ☐ |
| `bueno.gif` | bueno | ☐ |
| `malo.gif` | malo | ☐ |
| `rapido.gif` | rápido | ☐ |
| `lento.gif` | lento | ☐ |
| `bonito.gif` | bonito / lindo | ☐ |
| `feo.gif` | feo | ☐ |
| `caliente.gif` | caliente | ☐ |
| `frio.gif` | frío | ☐ |
| `alto.gif` | alto | ☐ |
| `bajo.gif` | bajo | ☐ |
| `joven.gif` | joven | ☐ |
| `viejo.gif` | viejo | ☐ |
| `nuevo.gif` | nuevo | ☐ |
| `limpio.gif` | limpio | ☐ |
| `sucio.gif` | sucio | ☐ |

### 9. Conectores (7)
**Buscar**: "conectores LSC", "pero porque sí no LSC"

| Archivo | Conector | ✓ |
|---|---|---|
| `pero.gif` | pero | ☐ |
| `porque.gif` | porque | ☐ |
| `si.gif` | sí | ☐ |
| `no.gif` | no | ☐ |
| `tambien.gif` | también | ☐ |
| `muy.gif` | muy | ☐ |
| `mas.gif` | más | ☐ |

> Nota: `y`, `o`, `n` se generan reusando el alfabeto dactilológico, no
> necesitas archivos aparte.

### 10. Partes del cuerpo (8)
**Buscar**: "cuerpo humano LSC", "partes del cuerpo LSC"

| Archivo | Palabra | ✓ |
|---|---|---|
| `cabeza.gif` | cabeza | ☐ |
| `mano.gif` | mano | ☐ |
| `ojo.gif` | ojo | ☐ |
| `boca.gif` | boca | ☐ |
| `pie.gif` | pie | ☐ |
| `corazon.gif` | corazón | ☐ |
| `brazo.gif` | brazo | ☐ |
| `pierna.gif` | pierna | ☐ |

### 11. Tiempo (12)
**Buscar**: "tiempo LSC", "hoy mañana ayer LSC", "días horas LSC"

| Archivo | Palabra | ✓ |
|---|---|---|
| `hoy.gif` | hoy | ☐ |
| `manana.gif` | mañana (día siguiente) | ☐ |
| `ayer.gif` | ayer | ☐ |
| `ahora.gif` | ahora | ☐ |
| `tarde.gif` | tarde | ☐ |
| `noche.gif` | noche | ☐ |
| `dia.gif` | día | ☐ |
| `semana.gif` | semana | ☐ |
| `mes.gif` | mes | ☐ |
| `ano.gif` | año | ☐ |
| `hora.gif` | hora | ☐ |
| `minuto.gif` | minuto | ☐ |

### 12. Comida y bebida (13)
**Buscar**: "alimentos LSC", "comida LSC"

| Archivo | Palabra | ✓ |
|---|---|---|
| `agua.gif` | agua | ☐ |
| `pan.gif` | pan | ☐ |
| `leche.gif` | leche | ☐ |
| `cafe.gif` | café | ☐ |
| `fruta.gif` | fruta | ☐ |
| `manzana.gif` | manzana | ☐ |
| `banana.gif` | banano / plátano | ☐ |
| `arroz.gif` | arroz | ☐ |
| `pollo.gif` | pollo | ☐ |
| `carne.gif` | carne | ☐ |
| `pescado.gif` | pescado | ☐ |
| `huevo.gif` | huevo | ☐ |
| `queso.gif` | queso | ☐ |

### 13. Emociones (5)
**Buscar**: "emociones LSC", "sentimientos LSC"

| Archivo | Palabra | ✓ |
|---|---|---|
| `feliz.gif` | feliz / contento | ☐ |
| `triste.gif` | triste | ☐ |
| `enojado.gif` | enojado / bravo | ☐ |
| `sorprendido.gif` | sorprendido | ☐ |
| `cansado.gif` | cansado | ☐ |

### 14. Días de la semana (7)
**Buscar**: "días de la semana LSC"

| Archivo | Día | ✓ |
|---|---|---|
| `lunes.gif` | lunes | ☐ |
| `martes.gif` | martes | ☐ |
| `miercoles.gif` | miércoles | ☐ |
| `jueves.gif` | jueves | ☐ |
| `viernes.gif` | viernes | ☐ |
| `sabado.gif` | sábado | ☐ |
| `domingo.gif` | domingo | ☐ |

### 15. Frases comunes (10)
**Buscar**: "frases básicas LSC", "presentación personal LSC"

| Archivo | Frase | ✓ |
|---|---|---|
| `como_te_llamas.gif` | ¿cómo te llamas? | ☐ |
| `me_llamo.gif` | me llamo… | ☐ |
| `cuantos_anos_tienes.gif` | ¿cuántos años tienes? | ☐ |
| `tengo_anos.gif` | tengo … años | ☐ |
| `donde_vives.gif` | ¿dónde vives? | ☐ |
| `vivo_en.gif` | vivo en… | ☐ |
| `necesito_ayuda.gif` | necesito ayuda | ☐ |
| `no_entiendo.gif` | no entiendo | ☐ |
| `repite_por_favor.gif` | repite por favor | ☐ |
| `te_quiero.gif` | te quiero | ☐ |

---

## 🛠️ Flujo recomendado para conseguir un archivo

1. **Buscar** en INSOR Educativo el término en español. Si no está, ir a Spread The Sign / FENASCOL / YouTube oficial.
2. **Descargar** el video original (botón de descarga, o con yt-dlp si es YouTube).
3. **Recortar** el segmento exacto de la seña — normalmente 1.5 a 3 segundos. Herramientas:
   - [ezgif.com](https://ezgif.com) — todo en navegador, fácil.
   - [FFmpeg](https://ffmpeg.org/) — línea de comandos:
     ```bash
     ffmpeg -i original.mp4 -ss 00:00:05 -t 2.5 -an -vf "scale=320:-1" sena.mp4
     ```
4. **Convertir** a GIF (si la app aún no soporta MP4):
   ```bash
   ffmpeg -i sena.mp4 -vf "fps=15,scale=320:-1:flags=lanczos" -loop 0 sena.gif
   ```
   O usa [ezgif.com/video-to-gif](https://ezgif.com/video-to-gif) (10 s).
5. **Renombrar** exactamente como aparece en la tabla de arriba.
6. **Pegar** en `static/gifs/letras/` o `static/gifs/palabras/` según corresponda.
7. **Recargar** la página — el GIF aparece automáticamente sin tocar BD ni código.

## 🎯 Recomendación de prioridad

Si vas a hacer esto por etapas para una sustentación o entrega:

| Prioridad | Categoría | Razón |
|---|---|---|
| 🥇 | Letras (A–Z, Ñ) | Habilita la dactilología — sin esto los nombres propios no funcionan. |
| 🥈 | Saludos + Frases comunes | Las primeras 5 demos que harás siempre incluyen saludos. |
| 🥉 | Verbos básicos + Pronombres tónicos | Núcleo de cualquier oración. |
| 4️⃣ | Familia + Lugares + Tiempo | Demos típicas tipo "mi familia vive en…". |
| 5️⃣ | Resto | Colores, comida, emociones, números — completa cobertura. |

---

## 📊 Sobre MP4 vs GIF (importante leer)

**Lo que pasa hoy**: el reproductor (`<img src="…gif">`) acepta **solo GIFs**. Si pones un MP4, no lo reproduce.

**Tres caminos**:

1. **Convertir todos los MP4 a GIF** — funcional pero la calidad baja y el peso sube.
2. **Mantener MP4 originales en una carpeta paralela** y convertir a GIF para el reproductor — duplicas archivos pero conservas calidad para el futuro.
3. **Soportar MP4 nativamente** (recomendado) — un solo cambio en el reproductor:
   - Si la URL termina en `.mp4` → usar `<video autoplay muted loop>`.
   - Si en `.gif` → usar `<img>`.
   - El JS detecta automáticamente.

El cambio para soportar MP4 nativo es ~30 líneas y deja la app más rápida y con mejor calidad. Pídelo cuando quieras y se hace en una sesión.

---

## ✅ Progreso (manual)

Lleva tu cuenta aquí:

- Letras: __ / 27
- Números: __ / 11
- Saludos: __ / 15
- Familia: __ / 10
- Verbos: __ / 31
- Colores: __ / 8
- Preguntas: __ / 7
- Lugares: __ / 14
- Adjetivos: __ / 17
- Conectores: __ / 7
- Cuerpo: __ / 8
- Tiempo: __ / 12
- Comida: __ / 13
- Emociones: __ / 5
- Días: __ / 7
- Frases: __ / 10
- **Sustantivos P0 (2026-05-14): __ / 10** ← prioridad alta

**TOTAL: __ / 212**

---

## 🆕 Sustantivos comunes P0 — pendientes (2026-05-14)

Estas 10 entradas YA están en BD (`seed_data.sql` sección 17 +
`seed_sustantivos_p0.sql`) pero faltan los archivos en disco.
Hasta que los pongas, el traductor mostrará "Sin seña LSC" (gris).

**Categoría**: animales, familia informal y personas básicas.
**Búsqueda en INSOR**: <https://educativo.insor.gov.co/diccionario/>
filtrar por categoría "Animales", "Familia" y "Personas".

| Archivo | Palabra | Buscar literal en INSOR | ✓ |
|---|---|---|---|
| `perro.mp4` | perro | "perro" | ☐ |
| `gato.mp4` | gato | "gato" | ☐ |
| `mama.mp4` | mamá / mama | "mamá" o usar la misma seña de "madre" | ☐ |
| `papa.mp4` | papá / papa | "papá" o usar la misma seña de "padre" | ☐ |
| `nino.mp4` | niño | "niño" | ☐ |
| `nina.mp4` | niña | "niña" | ☐ |
| `bebe.mp4` | bebé / bebe | "bebé" | ☐ |
| `amigo.mp4` | amigo | "amigo" | ☐ |
| `amiga.mp4` | amiga | "amiga" | ☐ |
| `familia.mp4` | familia | "familia" | ☐ |

⚠️ **Nombres SIN tilde y SIN ñ en disco** porque Windows + algunos
servidores web confunden caracteres no-ASCII en rutas. La BD guarda
`palabra='niño'` (con ñ) para que el match funcione tras
`normalizar()`, pero el `gif_url` en BD ya apunta a
`/static/gifs/palabras/nino.gif` (sin ñ). No hay mapeo en runtime:
el resolver solo cambia la extensión `.gif↔.mp4`, no el nombre.
