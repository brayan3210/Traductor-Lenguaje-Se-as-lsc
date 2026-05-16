-- ============================================================
-- Señas Co — Datos iniciales del diccionario LSC
-- Cobertura: 27 letras + 11 números + palabras + frases
--            218 entradas previas + 31 lugares/transporte/frases
--            añadidas el 2026-05-14 (sección 18 al final, archivos .m4v)
-- ============================================================

USE traductor_lsc;

-- Limpia cualquier dato previo antes de reinsertar
TRUNCATE TABLE senas;

-- ---------- 1. LETRAS (alfabeto dactilológico LSC) ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('a', '/static/gifs/letras/a.gif', 'letra', 'letras', 'Letra A del alfabeto dactilológico'),
('b', '/static/gifs/letras/b.gif', 'letra', 'letras', 'Letra B del alfabeto dactilológico'),
('c', '/static/gifs/letras/c.gif', 'letra', 'letras', 'Letra C del alfabeto dactilológico'),
('d', '/static/gifs/letras/d.gif', 'letra', 'letras', 'Letra D del alfabeto dactilológico'),
('e', '/static/gifs/letras/e.gif', 'letra', 'letras', 'Letra E del alfabeto dactilológico'),
('f', '/static/gifs/letras/f.gif', 'letra', 'letras', 'Letra F del alfabeto dactilológico'),
('g', '/static/gifs/letras/g.gif', 'letra', 'letras', 'Letra G del alfabeto dactilológico'),
('h', '/static/gifs/letras/h.gif', 'letra', 'letras', 'Letra H del alfabeto dactilológico'),
('i', '/static/gifs/letras/i.gif', 'letra', 'letras', 'Letra I del alfabeto dactilológico'),
('j', '/static/gifs/letras/j.gif', 'letra', 'letras', 'Letra J del alfabeto dactilológico'),
('k', '/static/gifs/letras/k.gif', 'letra', 'letras', 'Letra K del alfabeto dactilológico'),
('l', '/static/gifs/letras/l.gif', 'letra', 'letras', 'Letra L del alfabeto dactilológico'),
('m', '/static/gifs/letras/m.gif', 'letra', 'letras', 'Letra M del alfabeto dactilológico'),
('n', '/static/gifs/letras/n.gif', 'letra', 'letras', 'Letra N del alfabeto dactilológico'),
('ñ', '/static/gifs/letras/n_enye.gif', 'letra', 'letras', 'Letra Ñ del alfabeto dactilológico'),
('o', '/static/gifs/letras/o.gif', 'letra', 'letras', 'Letra O del alfabeto dactilológico'),
('p', '/static/gifs/letras/p.gif', 'letra', 'letras', 'Letra P del alfabeto dactilológico'),
('q', '/static/gifs/letras/q.gif', 'letra', 'letras', 'Letra Q del alfabeto dactilológico'),
('r', '/static/gifs/letras/r.gif', 'letra', 'letras', 'Letra R del alfabeto dactilológico'),
('s', '/static/gifs/letras/s.gif', 'letra', 'letras', 'Letra S del alfabeto dactilológico'),
('t', '/static/gifs/letras/t.gif', 'letra', 'letras', 'Letra T del alfabeto dactilológico'),
('u', '/static/gifs/letras/u.gif', 'letra', 'letras', 'Letra U del alfabeto dactilológico'),
('v', '/static/gifs/letras/v.gif', 'letra', 'letras', 'Letra V del alfabeto dactilológico'),
('w', '/static/gifs/letras/w.gif', 'letra', 'letras', 'Letra W del alfabeto dactilológico'),
('x', '/static/gifs/letras/x.gif', 'letra', 'letras', 'Letra X del alfabeto dactilológico'),
('y', '/static/gifs/letras/y.gif', 'letra', 'letras', 'Letra Y del alfabeto dactilológico'),
('z', '/static/gifs/letras/z.gif', 'letra', 'letras', 'Letra Z del alfabeto dactilológico');

-- ---------- 2. NÚMEROS (0 al 10) ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('cero',   '/static/gifs/palabras/cero.gif',   'numero', 'numeros', 'Número 0'),
('uno',    '/static/gifs/palabras/uno.gif',    'numero', 'numeros', 'Número 1'),
('dos',    '/static/gifs/palabras/dos.gif',    'numero', 'numeros', 'Número 2'),
('tres',   '/static/gifs/palabras/tres.gif',   'numero', 'numeros', 'Número 3'),
('cuatro', '/static/gifs/palabras/cuatro.gif', 'numero', 'numeros', 'Número 4'),
('cinco',  '/static/gifs/palabras/cinco.gif',  'numero', 'numeros', 'Número 5'),
('seis',   '/static/gifs/palabras/seis.gif',   'numero', 'numeros', 'Número 6'),
('siete',  '/static/gifs/palabras/siete.gif',  'numero', 'numeros', 'Número 7'),
('ocho',   '/static/gifs/palabras/ocho.gif',   'numero', 'numeros', 'Número 8'),
('nueve',  '/static/gifs/palabras/nueve.gif',  'numero', 'numeros', 'Número 9'),
('diez',   '/static/gifs/palabras/diez.gif',   'numero', 'numeros', 'Número 10');

-- ---------- 3. SALUDOS Y CORTESÍA ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('hola',           '/static/gifs/palabras/hola.gif',           'palabra', 'saludos', 'Saludo de bienvenida'),
('adios',          '/static/gifs/palabras/adios.gif',          'palabra', 'saludos', 'Despedida'),
('gracias',        '/static/gifs/palabras/gracias.gif',        'palabra', 'saludos', 'Expresión de gratitud'),
('por_favor',      '/static/gifs/palabras/por_favor.gif',      'frase',   'saludos', 'Fórmula de cortesía'),
('perdon',         '/static/gifs/palabras/perdon.gif',         'palabra', 'saludos', 'Disculpa'),
('buenos_dias',    '/static/gifs/palabras/buenos_dias.gif',    'frase',   'saludos', 'Saludo matutino'),
('buenas_tardes',  '/static/gifs/palabras/buenas_tardes.gif',  'frase',   'saludos', 'Saludo vespertino'),
('buenas_noches',  '/static/gifs/palabras/buenas_noches.gif',  'frase',   'saludos', 'Saludo nocturno'),
('bienvenido',     '/static/gifs/palabras/bienvenido.gif',     'palabra', 'saludos', 'Recibimiento'),
('como_estas',     '/static/gifs/palabras/como_estas.gif',     'frase',   'saludos', 'Pregunta de bienestar'),
('bien',           '/static/gifs/palabras/bien.gif',           'palabra', 'saludos', 'Estado positivo'),
('mal',            '/static/gifs/palabras/mal.gif',            'palabra', 'saludos', 'Estado negativo'),
('mas_o_menos',    '/static/gifs/palabras/mas_o_menos.gif',    'frase',   'saludos', 'Estado intermedio'),
('mucho_gusto',    '/static/gifs/palabras/mucho_gusto.gif',    'frase',   'saludos', 'Presentación cordial'),
('hasta_luego',    '/static/gifs/palabras/hasta_luego.gif',    'frase',   'saludos', 'Despedida temporal'),
('con_gusto',      '/static/gifs/palabras/con_gusto.gif',      'frase',   'saludos', 'Expresión cortés con gusto');

-- ---------- 4. FAMILIA ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('madre',    '/static/gifs/palabras/madre.gif',    'palabra', 'familia', 'Madre'),
('padre',    '/static/gifs/palabras/padre.gif',    'palabra', 'familia', 'Padre'),
('hermano',  '/static/gifs/palabras/hermano.gif',  'palabra', 'familia', 'Hermano'),
('hermana',  '/static/gifs/palabras/hermana.gif',  'palabra', 'familia', 'Hermana'),
('hijo',     '/static/gifs/palabras/hijo.gif',     'palabra', 'familia', 'Hijo'),
('hija',     '/static/gifs/palabras/hija.gif',     'palabra', 'familia', 'Hija'),
('abuelo',   '/static/gifs/palabras/abuelo.gif',   'palabra', 'familia', 'Abuelo'),
('abuela',   '/static/gifs/palabras/abuela.gif',   'palabra', 'familia', 'Abuela'),
('esposo',   '/static/gifs/palabras/esposo.gif',   'palabra', 'familia', 'Esposo'),
('esposa',   '/static/gifs/palabras/esposa.gif',   'palabra', 'familia', 'Esposa');

-- ---------- 5. VERBOS BÁSICOS ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('ser',       '/static/gifs/palabras/ser.gif',       'palabra', 'verbos', 'Verbo ser'),
('estar',     '/static/gifs/palabras/estar.gif',     'palabra', 'verbos', 'Verbo estar'),
('tener',     '/static/gifs/palabras/tener.gif',     'palabra', 'verbos', 'Verbo tener'),
('querer',    '/static/gifs/palabras/querer.gif',    'palabra', 'verbos', 'Verbo querer'),
('poder',     '/static/gifs/palabras/poder.gif',     'palabra', 'verbos', 'Verbo poder'),
('ir',        '/static/gifs/palabras/ir.gif',        'palabra', 'verbos', 'Verbo ir'),
('venir',     '/static/gifs/palabras/venir.gif',     'palabra', 'verbos', 'Verbo venir'),
('comer',     '/static/gifs/palabras/comer.gif',     'palabra', 'verbos', 'Verbo comer'),
('beber',     '/static/gifs/palabras/beber.gif',     'palabra', 'verbos', 'Verbo beber'),
('dormir',    '/static/gifs/palabras/dormir.gif',    'palabra', 'verbos', 'Verbo dormir'),
('trabajar',  '/static/gifs/palabras/trabajar.gif',  'palabra', 'verbos', 'Verbo trabajar'),
('estudiar',  '/static/gifs/palabras/estudiar.gif',  'palabra', 'verbos', 'Verbo estudiar'),
('hablar',    '/static/gifs/palabras/hablar.gif',    'palabra', 'verbos', 'Verbo hablar'),
('escuchar',  '/static/gifs/palabras/escuchar.gif',  'palabra', 'verbos', 'Verbo escuchar'),
('ver',       '/static/gifs/palabras/ver.gif',       'palabra', 'verbos', 'Verbo ver'),
('llamar',    '/static/gifs/palabras/llamar.gif',    'palabra', 'verbos', 'Verbo llamar'),
('ayudar',    '/static/gifs/palabras/ayudar.gif',    'palabra', 'verbos', 'Verbo ayudar'),
('necesitar', '/static/gifs/palabras/necesitar.gif', 'palabra', 'verbos', 'Verbo necesitar'),
('saber',     '/static/gifs/palabras/saber.gif',     'palabra', 'verbos', 'Verbo saber'),
('vivir',     '/static/gifs/palabras/vivir.gif',     'palabra', 'verbos', 'Verbo vivir'),
('cantar',    '/static/gifs/palabras/cantar.gif',    'palabra', 'verbos', 'Verbo cantar'),
('dar',       '/static/gifs/palabras/dar.gif',       'palabra', 'verbos', 'Verbo dar (direccional)'),
('decir',     '/static/gifs/palabras/decir.gif',     'palabra', 'verbos', 'Verbo decir (direccional)'),
('traer',     '/static/gifs/palabras/traer.gif',     'palabra', 'verbos', 'Verbo traer (direccional)'),
('llevar',    '/static/gifs/palabras/llevar.gif',    'palabra', 'verbos', 'Verbo llevar (direccional)'),
('jugar',     '/static/gifs/palabras/jugar.gif',     'palabra', 'verbos', 'Verbo jugar'),
('leer',      '/static/gifs/palabras/leer.gif',      'palabra', 'verbos', 'Verbo leer'),
('escribir',  '/static/gifs/palabras/escribir.gif',  'palabra', 'verbos', 'Verbo escribir'),
('correr',    '/static/gifs/palabras/correr.gif',    'palabra', 'verbos', 'Verbo correr'),
('caminar',   '/static/gifs/palabras/caminar.gif',   'palabra', 'verbos', 'Verbo caminar'),
('bailar',    '/static/gifs/palabras/bailar.gif',    'palabra', 'verbos', 'Verbo bailar'),
('cocinar',   '/static/gifs/palabras/cocinar.gif',   'palabra', 'verbos', 'Verbo cocinar'),
('mirar',     '/static/gifs/palabras/mirar.gif',     'palabra', 'verbos', 'Verbo mirar'),
('sentir',    '/static/gifs/palabras/sentir.gif',    'palabra', 'verbos', 'Verbo sentir'),
('pensar',    '/static/gifs/palabras/pensar.gif',    'palabra', 'verbos', 'Verbo pensar');

-- ---------- 6. COLORES ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('rojo',      '/static/gifs/palabras/rojo.gif',      'palabra', 'colores', 'Color rojo'),
('azul',      '/static/gifs/palabras/azul.gif',      'palabra', 'colores', 'Color azul'),
('verde',     '/static/gifs/palabras/verde.gif',     'palabra', 'colores', 'Color verde'),
('amarillo',  '/static/gifs/palabras/amarillo.gif',  'palabra', 'colores', 'Color amarillo'),
('blanco',    '/static/gifs/palabras/blanco.gif',    'palabra', 'colores', 'Color blanco'),
('negro',     '/static/gifs/palabras/negro.gif',     'palabra', 'colores', 'Color negro'),
('naranja',   '/static/gifs/palabras/naranja.gif',   'palabra', 'colores', 'Color naranja'),
('morado',    '/static/gifs/palabras/morado.gif',    'palabra', 'colores', 'Color morado'),
('rosado',    '/static/gifs/palabras/rosado.gif',    'palabra', 'colores', 'Color rosado');

-- ---------- 7. PALABRAS INTERROGATIVAS ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('que',     '/static/gifs/palabras/que.gif',     'palabra', 'preguntas', 'Interrogativo qué'),
('quien',   '/static/gifs/palabras/quien.gif',   'palabra', 'preguntas', 'Interrogativo quién'),
('donde',   '/static/gifs/palabras/donde.gif',   'palabra', 'preguntas', 'Interrogativo dónde'),
('cuando',  '/static/gifs/palabras/cuando.gif',  'palabra', 'preguntas', 'Interrogativo cuándo'),
('como',    '/static/gifs/palabras/como.gif',    'palabra', 'preguntas', 'Interrogativo cómo'),
('cuanto',  '/static/gifs/palabras/cuanto.gif',  'palabra', 'preguntas', 'Interrogativo cuánto'),
('por_que', '/static/gifs/palabras/por_que.gif', 'frase',   'preguntas', 'Interrogativo por qué');

-- ---------- 8. LUGARES ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('casa',          '/static/gifs/palabras/casa.gif',          'palabra', 'lugares', 'Vivienda'),
('colegio',       '/static/gifs/palabras/colegio.gif',       'palabra', 'lugares', 'Institución educativa'),
('hospital',      '/static/gifs/palabras/hospital.gif',      'palabra', 'lugares', 'Centro médico'),
('tienda',        '/static/gifs/palabras/tienda.gif',        'palabra', 'lugares', 'Establecimiento comercial'),
('parque',        '/static/gifs/palabras/parque.gif',        'palabra', 'lugares', 'Área recreativa'),
('iglesia',       '/static/gifs/palabras/iglesia.gif',       'palabra', 'lugares', 'Templo religioso'),
('banco',         '/static/gifs/palabras/banco.gif',         'palabra', 'lugares', 'Institución bancaria'),
('restaurante',   '/static/gifs/palabras/restaurante.gif',   'palabra', 'lugares', 'Establecimiento de comida'),
('calle',         '/static/gifs/palabras/calle.gif',         'palabra', 'lugares', 'Vía pública'),
('ciudad',        '/static/gifs/palabras/ciudad.gif',        'palabra', 'lugares', 'Centro urbano'),
('oficina',       '/static/gifs/palabras/oficina.gif',       'palabra', 'lugares', 'Espacio de trabajo'),
('supermercado',  '/static/gifs/palabras/supermercado.gif',  'palabra', 'lugares', 'Mercado grande'),
('farmacia',      '/static/gifs/palabras/farmacia.gif',      'palabra', 'lugares', 'Droguería'),
('trabajo',       '/static/gifs/palabras/trabajo.gif',       'palabra', 'lugares', 'Lugar de empleo');

-- ---------- 9. ADJETIVOS BÁSICOS ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('grande',    '/static/gifs/palabras/grande.gif',    'palabra', 'adjetivos', 'De gran tamaño'),
('pequeño',   '/static/gifs/palabras/pequeno.gif',   'palabra', 'adjetivos', 'De poco tamaño'),
('bueno',     '/static/gifs/palabras/bueno.gif',     'palabra', 'adjetivos', 'De calidad positiva'),
('malo',      '/static/gifs/palabras/malo.gif',      'palabra', 'adjetivos', 'De calidad negativa'),
('rapido',    '/static/gifs/palabras/rapido.gif',    'palabra', 'adjetivos', 'De alta velocidad'),
('lento',     '/static/gifs/palabras/lento.gif',     'palabra', 'adjetivos', 'De baja velocidad'),
('bonito',    '/static/gifs/palabras/bonito.gif',    'palabra', 'adjetivos', 'Estéticamente agradable'),
('feo',       '/static/gifs/palabras/feo.gif',       'palabra', 'adjetivos', 'Estéticamente desagradable'),
('caliente',  '/static/gifs/palabras/caliente.gif',  'palabra', 'adjetivos', 'De alta temperatura'),
('frio',      '/static/gifs/palabras/frio.gif',      'palabra', 'adjetivos', 'De baja temperatura'),
('alto',      '/static/gifs/palabras/alto.gif',      'palabra', 'adjetivos', 'De gran estatura'),
('bajo',      '/static/gifs/palabras/bajo.gif',      'palabra', 'adjetivos', 'De poca estatura'),
('joven',     '/static/gifs/palabras/joven.gif',     'palabra', 'adjetivos', 'De poca edad'),
('viejo',     '/static/gifs/palabras/viejo.gif',     'palabra', 'adjetivos', 'De mucha edad'),
('nuevo',     '/static/gifs/palabras/nuevo.gif',     'palabra', 'adjetivos', 'De reciente creación'),
('limpio',    '/static/gifs/palabras/limpio.gif',    'palabra', 'adjetivos', 'Sin suciedad'),
('sucio',     '/static/gifs/palabras/sucio.gif',     'palabra', 'adjetivos', 'Con suciedad');

-- ---------- 10. CONECTORES ----------
-- Nota: 'y', 'o', 'n' coinciden con letras del alfabeto; cuando el usuario los escribe
-- se traducen usando la seña dactilológica (deletreo) que ya está cargada.
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('pero',      '/static/gifs/palabras/pero.gif',      'palabra', 'conectores', 'Conjunción adversativa'),
('porque',    '/static/gifs/palabras/porque.gif',    'palabra', 'conectores', 'Conjunción causal'),
('si',        '/static/gifs/palabras/si.gif',        'palabra', 'conectores', 'Afirmación'),
('no',        '/static/gifs/palabras/no.gif',        'palabra', 'conectores', 'Negación'),
('tambien',   '/static/gifs/palabras/tambien.gif',   'palabra', 'conectores', 'Adición'),
('muy',       '/static/gifs/palabras/muy.gif',       'palabra', 'conectores', 'Intensificador'),
('mas',       '/static/gifs/palabras/mas.gif',       'palabra', 'conectores', 'Cantidad adicional');

-- ---------- 11. PARTES DEL CUERPO ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('cabeza',    '/static/gifs/palabras/cabeza.gif',    'palabra', 'cuerpo', 'Cabeza'),
('mano',      '/static/gifs/palabras/mano.gif',      'palabra', 'cuerpo', 'Mano'),
('ojo',       '/static/gifs/palabras/ojo.gif',       'palabra', 'cuerpo', 'Ojo'),
('boca',      '/static/gifs/palabras/boca.gif',      'palabra', 'cuerpo', 'Boca'),
('pie',       '/static/gifs/palabras/pie.gif',       'palabra', 'cuerpo', 'Pie'),
('corazon',   '/static/gifs/palabras/corazon.gif',   'palabra', 'cuerpo', 'Corazón'),
('brazo',     '/static/gifs/palabras/brazo.gif',     'palabra', 'cuerpo', 'Brazo'),
('pierna',    '/static/gifs/palabras/pierna.gif',    'palabra', 'cuerpo', 'Pierna');

-- ---------- 12. TIEMPO ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('hoy',      '/static/gifs/palabras/hoy.gif',      'palabra', 'tiempo', 'Día actual'),
('mañana',   '/static/gifs/palabras/manana.gif',   'palabra', 'tiempo', 'Día siguiente'),
('ayer',     '/static/gifs/palabras/ayer.gif',     'palabra', 'tiempo', 'Día anterior'),
('ahora',    '/static/gifs/palabras/ahora.gif',    'palabra', 'tiempo', 'Momento presente'),
('tarde',    '/static/gifs/palabras/tarde.gif',    'palabra', 'tiempo', 'Parte del día'),
('noche',    '/static/gifs/palabras/noche.gif',    'palabra', 'tiempo', 'Parte del día'),
('dia',      '/static/gifs/palabras/dia.gif',      'palabra', 'tiempo', 'Período de 24 horas'),
('semana',   '/static/gifs/palabras/semana.gif',   'palabra', 'tiempo', 'Período de 7 días'),
('mes',      '/static/gifs/palabras/mes.gif',      'palabra', 'tiempo', 'Período mensual'),
('año',      '/static/gifs/palabras/ano.gif',      'palabra', 'tiempo', 'Período anual'),
('hora',     '/static/gifs/palabras/hora.gif',     'palabra', 'tiempo', 'Unidad de tiempo'),
('minuto',   '/static/gifs/palabras/minuto.gif',   'palabra', 'tiempo', 'Unidad de tiempo');

-- ---------- 13. COMIDA Y BEBIDA ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('agua',     '/static/gifs/palabras/agua.gif',     'palabra', 'comida', 'Bebida principal'),
('pan',      '/static/gifs/palabras/pan.gif',      'palabra', 'comida', 'Alimento de harina'),
('leche',    '/static/gifs/palabras/leche.gif',    'palabra', 'comida', 'Bebida láctea'),
('cafe',     '/static/gifs/palabras/cafe.gif',     'palabra', 'comida', 'Bebida caliente'),
('fruta',    '/static/gifs/palabras/fruta.gif',    'palabra', 'comida', 'Alimento vegetal'),
('manzana',  '/static/gifs/palabras/manzana.gif',  'palabra', 'comida', 'Fruta'),
('banana',   '/static/gifs/palabras/banana.gif',   'palabra', 'comida', 'Fruta'),
('arroz',    '/static/gifs/palabras/arroz.gif',    'palabra', 'comida', 'Cereal'),
('pollo',    '/static/gifs/palabras/pollo.gif',    'palabra', 'comida', 'Carne de ave'),
('carne',    '/static/gifs/palabras/carne.gif',    'palabra', 'comida', 'Alimento proteico'),
('pescado',  '/static/gifs/palabras/pescado.gif',  'palabra', 'comida', 'Alimento del mar'),
('huevo',    '/static/gifs/palabras/huevo.gif',    'palabra', 'comida', 'Alimento proteico'),
('queso',    '/static/gifs/palabras/queso.gif',    'palabra', 'comida', 'Derivado lácteo');

-- ---------- 14. EMOCIONES ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('feliz',         '/static/gifs/palabras/feliz.gif',         'palabra', 'emociones', 'Emoción positiva'),
('triste',        '/static/gifs/palabras/triste.gif',        'palabra', 'emociones', 'Emoción negativa'),
('enojado',       '/static/gifs/palabras/enojado.gif',       'palabra', 'emociones', 'Estado de ira'),
('sorprendido',   '/static/gifs/palabras/sorprendido.gif',   'palabra', 'emociones', 'Reacción a lo inesperado'),
('cansado',       '/static/gifs/palabras/cansado.gif',       'palabra', 'emociones', 'Estado de fatiga');

-- ---------- 15. DÍAS DE LA SEMANA ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('lunes',      '/static/gifs/palabras/lunes.gif',      'palabra', 'dias', 'Primer día de la semana'),
('martes',     '/static/gifs/palabras/martes.gif',     'palabra', 'dias', 'Segundo día de la semana'),
('miercoles',  '/static/gifs/palabras/miercoles.gif',  'palabra', 'dias', 'Tercer día de la semana'),
('jueves',     '/static/gifs/palabras/jueves.gif',     'palabra', 'dias', 'Cuarto día de la semana'),
('viernes',    '/static/gifs/palabras/viernes.gif',    'palabra', 'dias', 'Quinto día de la semana'),
('sabado',     '/static/gifs/palabras/sabado.gif',     'palabra', 'dias', 'Sexto día de la semana'),
('domingo',    '/static/gifs/palabras/domingo.gif',    'palabra', 'dias', 'Séptimo día de la semana');

-- ---------- 16. FRASES COMUNES ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('como_te_llamas',      '/static/gifs/palabras/como_te_llamas.gif',      'frase', 'frases', 'Pregunta por el nombre'),
('me_llamo',            '/static/gifs/palabras/me_llamo.gif',            'frase', 'frases', 'Presentación del nombre'),
('cuantos_años_tienes', '/static/gifs/palabras/cuantos_anos_tienes.gif', 'frase', 'frases', 'Pregunta por la edad'),
('tengo_años',          '/static/gifs/palabras/tengo_anos.gif',          'frase', 'frases', 'Declaración de edad'),
('donde_vives',         '/static/gifs/palabras/donde_vives.gif',         'frase', 'frases', 'Pregunta por residencia'),
('vivo_en',             '/static/gifs/palabras/vivo_en.gif',             'frase', 'frases', 'Declaración de residencia'),
('necesito_ayuda',      '/static/gifs/palabras/necesito_ayuda.gif',      'frase', 'frases', 'Solicitud de asistencia'),
('no_entiendo',         '/static/gifs/palabras/no_entiendo.gif',         'frase', 'frases', 'Expresión de incomprensión'),
('repite_por_favor',    '/static/gifs/palabras/repite_por_favor.gif',    'frase', 'frases', 'Solicitud de repetición'),
('te_quiero',           '/static/gifs/palabras/te_quiero.gif',           'frase', 'frases', 'Declaración de afecto');

-- ---------- 17. SUSTANTIVOS COMUNES P0 (2026-05-14) ----------
-- Cobertura crítica para uso cotidiano: animales, familia informal y
-- personas. Resuelve el caso "perro" deletreado y otros sustantivos
-- básicos que aparecían como NO_DISPONIBLE. Claves sin tilde por
-- compatibilidad con normalizar() (conserva ñ, quita tildes).
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('perro',    '/static/gifs/palabras/perro.gif',    'palabra', 'animales', 'Animal doméstico — mano simulando orejas caídas + lengua'),
('gato',     '/static/gifs/palabras/gato.gif',     'palabra', 'animales', 'Animal doméstico felino — dedos imitando bigotes'),
('mama',     '/static/gifs/palabras/madre.gif',    'palabra', 'familia',  'Madre (informal). Misma seña base que MADRE — reusa el video de madre.'),
('papa',     '/static/gifs/palabras/padre.gif',    'palabra', 'familia',  'Padre (informal). Misma seña base que PADRE — reusa el video de padre.'),
('niño',     '/static/gifs/palabras/nino.gif',     'palabra', 'personas', 'Persona joven varón'),
('niña',     '/static/gifs/palabras/nina.gif',     'palabra', 'personas', 'Persona joven mujer'),
('bebe',     '/static/gifs/palabras/bebe.gif',     'palabra', 'personas', 'Niño muy pequeño / bebé'),
('amigo',    '/static/gifs/palabras/amigo.gif',    'palabra', 'personas', 'Persona con quien se tiene amistad (m.)'),
('amiga',    '/static/gifs/palabras/amiga.gif',    'palabra', 'personas', 'Persona con quien se tiene amistad (f.)'),
('familia',  '/static/gifs/palabras/familia.gif',  'palabra', 'familia',  'Conjunto de parientes — manos formando círculo');

-- ---------- 18. LUGARES URBANOS (2026-05-14, archivos .m4v) ----------
-- Vocabulario de ciudad/Bogotá. Los archivos físicos son .m4v;
-- el media_resolver los detecta automáticamente en disco aunque la
-- gif_url declarada use extensión .gif (compatibilidad histórica).
-- INSERT IGNORE evita duplicados si la palabra ya existía (banco, casa,
-- calle, restaurante, supermercado vienen de la sección 8).
INSERT IGNORE INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('aeropuerto',             '/static/gifs/palabras/aeropuerto.gif',             'palabra', 'lugares',    'Terminal aérea'),
('almacen',                '/static/gifs/palabras/almacen.gif',                'palabra', 'lugares',    'Establecimiento comercial grande'),
('avenida',                '/static/gifs/palabras/avenida.gif',                'palabra', 'lugares',    'Vía amplia de la ciudad'),
('barrio',                 '/static/gifs/palabras/barrio.gif',                 'palabra', 'lugares',    'Sector residencial'),
('basura',                 '/static/gifs/palabras/basura.gif',                 'palabra', 'lugares',    'Residuos urbanos'),
('cafeteria',              '/static/gifs/palabras/cafeteria.gif',              'palabra', 'lugares',    'Establecimiento de café'),
('carcel',                 '/static/gifs/palabras/carcel.gif',                 'palabra', 'lugares',    'Centro penitenciario'),
('carniceria',             '/static/gifs/palabras/carniceria.gif',             'palabra', 'lugares',    'Negocio de carnes'),
('carrera',                '/static/gifs/palabras/carrera.gif',                'palabra', 'lugares',    'Vía urbana (terminología de Bogotá)'),
('cementerio',             '/static/gifs/palabras/cementerio.gif',             'palabra', 'lugares',    'Lugar de sepulturas'),
('centro_comercial',       '/static/gifs/palabras/centro_comercial.gif',       'frase',   'lugares',    'Mall — conjunto de tiendas'),
('direccion',              '/static/gifs/palabras/direccion.gif',              'palabra', 'lugares',    'Ubicación postal'),
('drogueria',              '/static/gifs/palabras/drogueria.gif',              'palabra', 'lugares',    'Farmacia'),
('edificio',               '/static/gifs/palabras/edificio.gif',               'palabra', 'lugares',    'Construcción urbana'),
('esquina',                '/static/gifs/palabras/esquina.gif',                'palabra', 'lugares',    'Intersección de vías'),
('parqueadero',            '/static/gifs/palabras/parqueadero.gif',            'palabra', 'lugares',    'Estacionamiento'),
('peluqueria',             '/static/gifs/palabras/peluqueria.gif',             'palabra', 'lugares',    'Negocio de cortes de cabello'),
('plaza_de_mercado',       '/static/gifs/palabras/plaza_de_mercado.gif',       'frase',   'lugares',    'Mercado tradicional'),
('puente',                 '/static/gifs/palabras/puente.gif',                 'palabra', 'lugares',    'Estructura sobre obstáculo'),
('semaforo',               '/static/gifs/palabras/semaforo.gif',               'palabra', 'lugares',    'Señal de tráfico'),
('terminal_de_transporte', '/static/gifs/palabras/terminal_de_transporte.gif', 'frase',   'lugares',    'Terminal de buses interurbanos');

-- ---------- 19. TRANSPORTE (2026-05-14, archivos .m4v) ----------
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('ambulancia',  '/static/gifs/palabras/ambulancia.gif',  'palabra', 'transporte', 'Vehículo de emergencias médicas'),
('avion',       '/static/gifs/palabras/avion.gif',       'palabra', 'transporte', 'Vehículo aéreo'),
('bicicleta',   '/static/gifs/palabras/bicicleta.gif',   'palabra', 'transporte', 'Vehículo de dos ruedas a pedal'),
('carro',       '/static/gifs/palabras/carro.gif',       'palabra', 'transporte', 'Automóvil'),
('helicoptero', '/static/gifs/palabras/helicoptero.gif', 'palabra', 'transporte', 'Aeronave de rotor'),
('moto',        '/static/gifs/palabras/moto.gif',        'palabra', 'transporte', 'Motocicleta'),
('taxi',        '/static/gifs/palabras/taxi.gif',        'palabra', 'transporte', 'Vehículo de servicio público'),
('tren',        '/static/gifs/palabras/tren.gif',        'palabra', 'transporte', 'Vehículo ferroviario');

-- ---------- 20. FRASES DE EJEMPLO (2026-05-14, archivos .m4v) ----------
-- Frases largas que se almacenan como referencia visual completa en el
-- diccionario. NO se detectan automáticamente en traducción porque exceden
-- _MAX_PHRASE_LEN (4 tokens), pero son consultables desde la vista del
-- diccionario para mostrar cómo se signa una oración compleja completa.
INSERT INTO senas (palabra, gif_url, tipo, categoria, descripcion) VALUES
('edificio_ejemplo', '/static/gifs/palabras/edificio_ejemplo.gif', 'frase', 'ejemplos',
 'Aquí en el centro de Bogotá están construyendo un edificio nuevo, grandísimo y altísimo. Las personas se asombran al verlo.');
