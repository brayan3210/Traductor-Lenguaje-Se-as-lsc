/* ============================================================
   Señas Co — Lógica del traductor
   Gestión del estado, llamadas a la API y reproductor de señas
   ============================================================ */

(() => {
    'use strict';

    const API = {
        traducir: '/api/traducir',
    };

    const BASE_DURATION_MS = 2200;
    const MAX_LEN = 2000;

    // ---------- Estado central ----------
    const state = {
        senas: [],
        indice: 0,
        reproduciendo: false,
        velocidad: 1,
        timerId: null,
        ultimaConsulta: '',
    };

    // ---------- Referencias DOM ----------
    const $ = (id) => document.getElementById(id);

    const dom = {
        textarea: $('textoEntrada'),
        charCount: $('charCount'),
        btnTraducir: $('btnTraducir'),
        btnLimpiar: $('btnLimpiar'),
        ejemplos: document.querySelectorAll('.tx-chip[data-ejemplo]'),
        player: $('txPlayer'),
        gif: $('txGif'),
        video: $('txVideo'),
        nmm: $('txNmm'),
        nmmIcon: $('txNmmIcon'),
        nmmLabel: $('txNmmLabel'),
        direccion: $('txDireccion'),
        direccionArrow: $('txDireccionArrow'),
        placeholder: $('txPlaceholder'),
        fallback: $('txFallback'),
        fallbackWord: $('txFallbackWord'),
        loader: $('txLoader'),
        statusHint: $('txStatusHint'),
        status: $('txStatus'),
        currentWord: $('txCurrentWord'),
        progressText: $('txProgressText'),
        progressFill: $('txProgressFill'),
        btnPrev: $('btnAnterior'),
        btnPlay: $('btnPlay'),
        btnNext: $('btnSiguiente'),
        btnRestart: $('btnReiniciar'),
        iconPlay: document.querySelector('.tx-ctrl__icon-play'),
        iconPause: document.querySelector('.tx-ctrl__icon-pause'),
        speedBtns: document.querySelectorAll('.tx-speed__btn'),
        sequence: $('txSequence'),
        legend: $('txLegend'),
        glosaBlock: $('txGlosaBlock'),
        glosaText: $('txGlosaText'),
        glosaBadges: $('txGlosaBadges'),
        disclaimer: $('txDisclaimer'),
        insights: $('txInsights'),
        tokens: $('txTokens'),
        dactilo: $('txDactilo'),
        noDisponibles: $('txNoDisponibles'),
        sumTotalSenas: $('sumTotalSenas'),
        sumTokens: $('sumTokens'),
        sumDactilo: $('sumDactilo'),
        sumNoEnc: $('sumNoEnc'),
        alert: $('txAlert'),
        alertText: $('txAlertText'),
    };

    // ---------- Inicialización ----------
    document.addEventListener('DOMContentLoaded', () => {
        registrarEventos();
        actualizarContador();
        actualizarBotonTraducir();
    });

    function registrarEventos() {
        dom.textarea.addEventListener('input', () => {
            actualizarContador();
            actualizarBotonTraducir();
        });
        dom.textarea.addEventListener('keydown', (ev) => {
            if ((ev.ctrlKey || ev.metaKey) && ev.key === 'Enter') {
                ev.preventDefault();
                traducir();
            }
        });

        dom.btnTraducir.addEventListener('click', traducir);
        dom.btnLimpiar.addEventListener('click', limpiarEntrada);

        dom.ejemplos.forEach((chip) => {
            chip.addEventListener('click', () => {
                dom.textarea.value = chip.dataset.ejemplo || '';
                dom.textarea.focus();
                actualizarContador();
                actualizarBotonTraducir();
            });
        });

        dom.btnPrev.addEventListener('click', irAnterior);
        dom.btnNext.addEventListener('click', irSiguiente);
        dom.btnPlay.addEventListener('click', togglePlay);
        dom.btnRestart.addEventListener('click', reiniciar);

        dom.speedBtns.forEach((btn) => {
            btn.addEventListener('click', () => cambiarVelocidad(parseFloat(btn.dataset.speed)));
        });

        document.addEventListener('keydown', (ev) => {
            if (document.activeElement === dom.textarea) return;
            if (ev.key === ' ' && state.senas.length) {
                ev.preventDefault();
                togglePlay();
            } else if (ev.key === 'ArrowRight' && state.senas.length) {
                ev.preventDefault();
                irSiguiente();
            } else if (ev.key === 'ArrowLeft' && state.senas.length) {
                ev.preventDefault();
                irAnterior();
            }
        });

        dom.gif.addEventListener('error', manejarErrorMedia);
        dom.gif.addEventListener('load', marcarMediaCargada);

        if (dom.video) {
            dom.video.addEventListener('error', manejarErrorMedia);
            dom.video.addEventListener('loadeddata', marcarMediaCargada);
        }
    }

    function marcarMediaCargada() {
        if (dom.player.dataset.state === 'loading-gif') {
            dom.player.dataset.state = state.reproduciendo ? 'playing' : 'paused';
        }
    }

    // ---------- UI Helpers ----------
    function actualizarContador() {
        const largo = dom.textarea.value.length;
        dom.charCount.textContent = largo;
        dom.charCount.style.color = largo > MAX_LEN * 0.9 ? '#e6c277' : '';
    }

    function actualizarBotonTraducir() {
        const vacio = !dom.textarea.value.trim();
        dom.btnTraducir.disabled = vacio;
        dom.btnTraducir.style.opacity = vacio ? '.6' : '1';
    }

    function limpiarEntrada() {
        dom.textarea.value = '';
        actualizarContador();
        actualizarBotonTraducir();
        resetearSalida();
        dom.textarea.focus();
    }

    function mostrarStatus(texto, clase = '') {
        dom.status.textContent = texto;
        dom.status.className = 'tx-status' + (clase ? ' ' + clase : '');
    }

    function mostrarAlerta(mensaje) {
        dom.alertText.textContent = mensaje;
        dom.alert.hidden = false;
    }

    function ocultarAlerta() {
        dom.alert.hidden = true;
        dom.alertText.textContent = '';
    }

    function resetearSalida() {
        detenerReproduccion();
        state.senas = [];
        state.indice = 0;
        dom.player.dataset.state = 'empty';
        dom.gif.src = '';
        dom.gif.alt = '';
        dom.gif.hidden = true;
        if (dom.video) {
            dom.video.pause();
            dom.video.removeAttribute('src');
            dom.video.load();
            dom.video.hidden = true;
        }
        dom.fallback.hidden = true;
        if (dom.nmm) dom.nmm.hidden = true;
        if (dom.direccion) dom.direccion.hidden = true;
        dom.sequence.innerHTML = '';
        dom.tokens.innerHTML = '';
        if (dom.dactilo)       dom.dactilo.innerHTML = '';
        if (dom.noDisponibles) dom.noDisponibles.innerHTML = '';
        if (dom.glosaBlock) dom.glosaBlock.hidden = true;
        if (dom.glosaText)  dom.glosaText.textContent = '';
        if (dom.glosaBadges) dom.glosaBadges.innerHTML = '';
        if (dom.disclaimer) dom.disclaimer.hidden = true;
        if (dom.legend) dom.legend.hidden = true;
        dom.insights.hidden = true;
        dom.currentWord.textContent = '—';
        dom.progressText.textContent = '0 / 0';
        dom.progressFill.style.width = '0%';
        dom.statusHint.textContent = 'Esperando traducción…';
        actualizarControles();
        mostrarStatus('', '');
        ocultarAlerta();
    }

    // ---------- Traducción ----------
    async function traducir() {
        const texto = dom.textarea.value.trim();
        if (!texto) return;
        if (texto === state.ultimaConsulta && state.senas.length) {
            reiniciar();
            return;
        }

        ocultarAlerta();
        dom.loader.hidden = false;
        dom.player.dataset.state = 'loading';
        dom.btnTraducir.disabled = true;
        mostrarStatus('Procesando', '');

        try {
            const resp = await fetch(API.traducir, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ texto }),
            });
            const data = await resp.json().catch(() => ({}));
            if (!resp.ok || !data.success) {
                throw new Error(data.error || `Error ${resp.status}`);
            }

            state.ultimaConsulta = texto;
            cargarResultado(data);
        } catch (err) {
            console.error(err);
            mostrarAlerta(err.message || 'No se pudo conectar con el servidor.');
            mostrarStatus('Error', 'is-error');
            dom.player.dataset.state = 'empty';
        } finally {
            dom.loader.hidden = true;
            actualizarBotonTraducir();
        }
    }

    function cargarResultado(data) {
        state.senas = Array.isArray(data.senas) ? data.senas : [];
        state.indice = 0;

        renderizarGlosa(data);
        renderizarTokens(data);
        renderizarResumen(data);
        renderizarSecuencia();
        dom.insights.hidden = false;
        if (dom.legend) dom.legend.hidden = !state.senas.length;
        if (dom.disclaimer) dom.disclaimer.hidden = !state.senas.length;

        if (!state.senas.length) {
            dom.player.dataset.state = 'empty';
            dom.statusHint.textContent = 'No hay señas para mostrar.';
            mostrarStatus('Sin resultados', 'is-warn');
            return;
        }

        dom.statusHint.textContent = `${state.senas.length} seña${state.senas.length === 1 ? '' : 's'} listas`;
        mostrarStatus('Listo', 'is-ok');
        actualizarControles();
        mostrarSenaActual();
        iniciarReproduccion();
    }

    function renderizarGlosa(data) {
        if (!dom.glosaBlock) return;
        const glosa = (data.glosa || '').trim();
        dom.glosaBlock.hidden = !glosa;
        dom.glosaText.textContent = glosa || '—';

        const badges = [];
        if (data.es_pregunta) {
            badges.push(`<span class="tx-badge tx-badge--pregunta" title="Cejas levantadas o fruncidas según el tipo de pregunta">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                Pregunta
            </span>`);
        }
        if (data.tiene_negacion) {
            badges.push(`<span class="tx-badge tx-badge--negacion" title="Marcador no manual: cabeza moviéndose">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                Negación
            </span>`);
        }
        dom.glosaBadges.innerHTML = badges.join('');
    }

    function renderizarTokens(data) {
        dom.tokens.innerHTML = '';
        (data.tokens || []).forEach((tok) => {
            const el = document.createElement('span');
            el.className = 'tx-token';
            el.textContent = tok;
            dom.tokens.appendChild(el);
        });

        if (dom.dactilo) {
            dom.dactilo.innerHTML = '';
            (data.palabras_deletreadas || []).forEach((tok) => {
                const el = document.createElement('span');
                el.className = 'tx-token tx-token--dactilo';
                el.textContent = tok;
                dom.dactilo.appendChild(el);
            });
        }

        if (dom.noDisponibles) {
            dom.noDisponibles.innerHTML = '';
            (data.palabras_no_disponibles || []).forEach((tok) => {
                const el = document.createElement('span');
                el.className = 'tx-token tx-token--no-disp';
                el.textContent = tok;
                dom.noDisponibles.appendChild(el);
            });
        }
    }

    function renderizarResumen(data) {
        dom.sumTotalSenas.textContent = data.total_senas || 0;
        dom.sumTokens.textContent     = (data.tokens || []).length;
        if (dom.sumDactilo) dom.sumDactilo.textContent = (data.palabras_deletreadas || []).length;
        dom.sumNoEnc.textContent      = (data.palabras_no_disponibles || []).length;
    }

    function renderizarSecuencia() {
        dom.sequence.innerHTML = '';
        state.senas.forEach((sena, i) => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'tx-seq-item';
            if (sena.fuente === 'deletreo') item.classList.add('tx-seq-item--deletreo');
            if (sena.fuente === 'no_disponible') item.classList.add('tx-seq-item--no-disp');
            if (!sena.encontrado && sena.fuente !== 'no_disponible') item.classList.add('tx-seq-item--missing');
            if (sena.rol && sena.rol !== 'otro') item.classList.add(`tx-seq-item--rol-${sena.rol}`);
            item.innerHTML = `
                <span class="tx-seq-item__index">${i + 1}</span>
                <span>${prettyWord(sena.palabra)}</span>
            `;
            item.title = sena.rol && sena.rol !== 'otro' ? `Rol: ${sena.rol}` : '';
            item.addEventListener('click', () => {
                state.indice = i;
                mostrarSenaActual();
                if (state.reproduciendo) reprogramarTimer();
            });
            dom.sequence.appendChild(item);
        });
    }

    // ---------- Reproductor ----------
    function mostrarSenaActual() {
        const sena = state.senas[state.indice];
        if (!sena) return;

        dom.currentWord.textContent = prettyWord(sena.palabra);
        dom.progressText.textContent = `${state.indice + 1} / ${state.senas.length}`;
        const porcentaje = ((state.indice + 1) / state.senas.length) * 100;
        dom.progressFill.style.width = `${porcentaje}%`;

        // Resaltar item activo en la tira
        dom.sequence.querySelectorAll('.tx-seq-item').forEach((el, i) => {
            el.classList.toggle('is-active', i === state.indice);
        });
        const activo = dom.sequence.querySelector('.tx-seq-item.is-active');
        if (activo) activo.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });

        if (sena.encontrado && sena.gif_url) {
            mostrarMedia(sena);
        } else {
            mostrarFallback(sena.palabra);
        }

        // Overlays gramaticales (marcador no manual + dirección espacial)
        actualizarOverlaysGramaticales(sena);
    }

    function actualizarOverlaysGramaticales(sena) {
        // Marcador no manual: emoji/símbolo + label
        if (sena.marcador_codigo && dom.nmm) {
            dom.nmmIcon.textContent  = sena.marcador_icono || '';
            dom.nmmLabel.textContent = sena.marcador_label || '';
            dom.nmm.dataset.codigo   = sena.marcador_codigo;
            dom.nmm.title            = sena.marcador_label || '';
            dom.nmm.hidden = false;
        } else if (dom.nmm) {
            dom.nmm.hidden = true;
        }

        // Dirección espacial (verbos como "yo te ayudo")
        if (sena.direccion && dom.direccion) {
            dom.direccionArrow.textContent = sena.direccion;
            dom.direccion.title           = sena.direccion_label || '';
            dom.direccion.hidden          = false;
        } else if (dom.direccion) {
            dom.direccion.hidden = true;
        }
    }

    function mostrarMedia(sena) {
        dom.fallback.hidden = true;
        dom.player.dataset.state = 'loading-gif';

        if (sena.media_type === 'video' && dom.video) {
            // Oculta el <img>, muestra el <video> y reproduce.
            dom.gif.hidden = true;
            dom.gif.removeAttribute('src');
            dom.video.hidden = false;
            dom.video.setAttribute('aria-label', `Seña de "${sena.palabra}"`);
            // Forzar recarga limpia del video.
            dom.video.pause();
            dom.video.src = sena.gif_url;
            dom.video.playbackRate = state.velocidad || 1;
            dom.video.load();
            const promesa = dom.video.play();
            if (promesa && typeof promesa.catch === 'function') promesa.catch(() => {});
        } else {
            // Modo imagen (.gif). Oculta el <video>, muestra el <img>.
            if (dom.video) {
                dom.video.pause();
                dom.video.removeAttribute('src');
                dom.video.load();
                dom.video.hidden = true;
            }
            dom.gif.hidden = false;
            dom.gif.alt = `Seña de "${sena.palabra}"`;
            dom.gif.src = '';
            requestAnimationFrame(() => { dom.gif.src = sena.gif_url; });
        }
    }

    function mostrarFallback(palabra) {
        const sena = state.senas[state.indice];
        const noDisp = sena && sena.fuente === 'no_disponible';
        dom.fallbackWord.textContent = prettyWord(palabra);
        const tag = dom.fallback.querySelector('.tx-player__fallback-tag');
        const hint = dom.fallback.querySelector('.tx-player__fallback-hint');
        if (tag)  tag.textContent  = noDisp ? 'Sin seña LSC' : 'Recurso pendiente';
        if (hint) hint.innerHTML   = noDisp
            ? 'Esta palabra no tiene una seña en nuestro diccionario. Considera deletrearla manualmente.'
            : 'Añade el archivo (.mp4 o .gif) a <code>static/gifs/</code>.';
        dom.fallback.classList.toggle('tx-player__fallback--info', !!noDisp);
        dom.fallback.hidden = false;

        // Limpia ambos elementos para no mostrar el último frame cargado.
        dom.gif.removeAttribute('src');
        dom.gif.hidden = true;
        if (dom.video) {
            dom.video.pause();
            dom.video.removeAttribute('src');
            dom.video.load();
            dom.video.hidden = true;
        }
        dom.player.dataset.state = 'fallback';
    }

    function manejarErrorMedia() {
        const sena = state.senas[state.indice];
        if (sena) mostrarFallback(sena.palabra);
    }

    function iniciarReproduccion() {
        state.reproduciendo = true;
        actualizarIconoPlay();
        reprogramarTimer();
    }

    function detenerReproduccion() {
        state.reproduciendo = false;
        if (state.timerId) {
            clearTimeout(state.timerId);
            state.timerId = null;
        }
        actualizarIconoPlay();
    }

    function togglePlay() {
        if (!state.senas.length) return;
        if (state.reproduciendo) {
            detenerReproduccion();
            if (dom.player.dataset.state === 'playing') dom.player.dataset.state = 'paused';
        } else {
            if (state.indice >= state.senas.length - 1) state.indice = 0;
            mostrarSenaActual();
            iniciarReproduccion();
        }
    }

    function reprogramarTimer() {
        if (state.timerId) clearTimeout(state.timerId);
        const duracion = BASE_DURATION_MS / state.velocidad;
        state.timerId = setTimeout(avanzar, duracion);
    }

    function avanzar() {
        if (state.indice >= state.senas.length - 1) {
            detenerReproduccion();
            dom.player.dataset.state = 'paused';
            mostrarStatus('Reproducción finalizada', 'is-ok');
            return;
        }
        state.indice += 1;
        mostrarSenaActual();
        if (state.reproduciendo) reprogramarTimer();
    }

    function irSiguiente() {
        if (!state.senas.length) return;
        if (state.indice >= state.senas.length - 1) return;
        state.indice += 1;
        mostrarSenaActual();
        if (state.reproduciendo) reprogramarTimer();
    }

    function irAnterior() {
        if (!state.senas.length) return;
        if (state.indice <= 0) return;
        state.indice -= 1;
        mostrarSenaActual();
        if (state.reproduciendo) reprogramarTimer();
    }

    function reiniciar() {
        if (!state.senas.length) return;
        state.indice = 0;
        mostrarSenaActual();
        iniciarReproduccion();
    }

    function cambiarVelocidad(velocidad) {
        if (!velocidad || isNaN(velocidad)) return;
        state.velocidad = velocidad;
        dom.speedBtns.forEach((btn) => {
            btn.classList.toggle('is-active', parseFloat(btn.dataset.speed) === velocidad);
        });
        if (dom.video && !dom.video.hidden) dom.video.playbackRate = velocidad;
        if (state.reproduciendo) reprogramarTimer();
    }

    function actualizarControles() {
        const tiene = state.senas.length > 0;
        dom.btnPlay.disabled = !tiene;
        dom.btnPrev.disabled = !tiene || state.indice <= 0;
        dom.btnNext.disabled = !tiene || state.indice >= state.senas.length - 1;
        dom.btnRestart.disabled = !tiene;
    }

    function actualizarIconoPlay() {
        if (state.reproduciendo) {
            dom.iconPlay.hidden = true;
            dom.iconPause.hidden = false;
            dom.btnPlay.setAttribute('aria-label', 'Pausar');
        } else {
            dom.iconPlay.hidden = false;
            dom.iconPause.hidden = true;
            dom.btnPlay.setAttribute('aria-label', 'Reproducir');
        }
        actualizarControles();
    }

    function prettyWord(w) {
        if (!w) return '—';
        return w.replace(/_/g, ' ');
    }

    // Exponer una pequeña API para pruebas manuales desde la consola
    window.__traductor = { state, traducir, reiniciar };
})();
