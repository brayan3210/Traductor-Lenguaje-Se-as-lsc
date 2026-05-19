-- ============================================================
-- Señas Co — Patch P0: sustantivos comunes faltantes
-- Fecha: 2026-05-14
-- Propósito: añadir las 10 entradas críticas a la BD VIVA sin
-- truncar el resto del diccionario. Usa INSERT IGNORE para que
-- correr el script varias veces sea seguro (idempotente).
--
-- Aplicar desde phpMyAdmin → BD `traductor_lsc` → pestaña SQL,
-- o desde la terminal con:
--     mysql -u root traductor_lsc < database/seed_sustantivos_p0.sql
--
-- Las 10 entradas ya están también en seed_data.sql (sección 17)
-- para que sobrevivan a un init_db completo en el futuro.
-- ============================================================

USE traductor_lsc;

INSERT IGNORE INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('perro',    '/static/gifs/palabras/perro.gif',    'palabra', 'animales', 'Animal doméstico — mano simulando orejas caídas + lengua'),
('gato',     '/static/gifs/palabras/gato.gif',     'palabra', 'animales', 'Animal doméstico felino — dedos imitando bigotes'),
('mama',     '/static/gifs/palabras/madre.gif',    'palabra', 'familia',  'Madre (informal). Reusa el video de MADRE'),
('papa',     '/static/gifs/palabras/padre.gif',    'palabra', 'familia',  'Padre (informal). Reusa el video de PADRE'),
('niño',     '/static/gifs/palabras/nino.gif',     'palabra', 'personas', 'Persona joven varón'),
('niña',     '/static/gifs/palabras/nina.gif',     'palabra', 'personas', 'Persona joven mujer'),
('bebe',     '/static/gifs/palabras/bebe.gif',     'palabra', 'personas', 'Niño muy pequeño / bebé'),
('amigo',    '/static/gifs/palabras/amigo.gif',    'palabra', 'personas', 'Persona con quien se tiene amistad (m.)'),
('amiga',    '/static/gifs/palabras/amiga.gif',    'palabra', 'personas', 'Persona con quien se tiene amistad (f.)'),
('familia',  '/static/gifs/palabras/familia.gif',  'palabra', 'familia',  'Conjunto de parientes — manos formando círculo');

-- Verificación rápida (descomentar para correr):
-- SELECT palabra, tipo, categoria FROM senas
--  WHERE palabra IN ('perro','gato','mama','papa','niño','niña','bebe','amigo','amiga','familia')
--  ORDER BY categoria, palabra;
