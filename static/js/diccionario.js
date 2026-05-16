/* ============================================================
   Señas Co — Lógica del explorador del diccionario
   Con lazy-loading de videos para no saturar el navegador.
   ============================================================ */

(() => {
    'use strict';

    const state = {
        entradas: [],
        categoriaActiva: '',
        busqueda: '',
        // IntersectionObserver compartido para todos los videos de las cards.
        // Cuando una card entra en el viewport, se le inyecta el src y arranca;
        // cuando sale, se pausa para liberar CPU/decoder.
        observer: null,
    };

    const $ = (id) => document.getElementById(id);

    const dom = {
        grid: $('dicGrid'),
        stats: $('dicStats'),
        buscar: $('dicBuscar'),
        filtros: document.querySelectorAll('.dic-filter'),
        loading: $('dicLoading'),
    };

    document.addEventListener('DOMContentLoaded', () => {
        construirObserver();
        cargarDiccionario();

        dom.buscar.addEventListener('input', debounce((ev) => {
            state.busqueda = ev.target.value.trim().toLowerCase();
            renderizar();
        }, 180));

        dom.filtros.forEach((btn) => {
            btn.addEventListener('click', () => {
                dom.filtros.forEach((b) => b.classList.remove('is-active'));
                btn.classList.add('is-active');
                state.categoriaActiva = btn.dataset.categoria || '';
                renderizar();
            });
        });
    });

    async function cargarDiccionario() {
        try {
            const resp = await fetch('/api/diccionario');
            const data = await resp.json();
            if (!data.success) throw new Error(data.error || 'Error al cargar');
            state.entradas = data.entradas || [];
            renderizar();
        } catch (err) {
            console.error(err);
            dom.grid.innerHTML = `
                <div class="dic-empty">
                    <p>⚠️ No se pudo cargar el diccionario.<br>
                    Asegúrate de haber ejecutado <code>python -m database.init_db</code>.</p>
                </div>
            `;
        }
    }

    function renderizar() {
        const filtradas = filtrar(state.entradas);
        actualizarStats(filtradas);

        // Antes de re-renderizar: detener cualquier video activo y limpiar el
        // observer para no acumular referencias a elementos viejos.
        if (state.observer) {
            dom.grid.querySelectorAll('video').forEach((v) => state.observer.unobserve(v));
        }

        if (!filtradas.length) {
            dom.grid.innerHTML = `
                <div class="dic-empty">
                    <p>No hay resultados para los filtros seleccionados.</p>
                </div>
            `;
            return;
        }

        const fragment = document.createDocumentFragment();
        filtradas.forEach((entrada) => fragment.appendChild(crearCard(entrada)));
        dom.grid.innerHTML = '';
        dom.grid.appendChild(fragment);
    }

    // ---------- Lazy loading de videos ----------

    function construirObserver() {
        if (!('IntersectionObserver' in window)) {
            // Fallback: navegador sin IO → cargamos todo de una vez (UX previa).
            state.observer = null;
            return;
        }
        state.observer = new IntersectionObserver(
            (entries) => entries.forEach(manejarInterseccion),
            {
                root: null,
                rootMargin: '300px 0px',  // precarga un poquito antes de aparecer
                threshold: 0.01,
            }
        );
    }

    function manejarInterseccion(entry) {
        const v = entry.target;
        if (!(v instanceof HTMLVideoElement)) return;

        if (entry.isIntersecting) {
            // Visible: inyecta el src si no se ha cargado y arranca.
            if (!v.src && v.dataset.src) {
                v.src = v.dataset.src;
                v.load();
            }
            const promesa = v.play();
            if (promesa && typeof promesa.catch === 'function') promesa.catch(() => {});
        } else {
            // Fuera de pantalla: pausa para liberar CPU/decoder.
            // Mantenemos `src` puesto para que reanude rápido al volver.
            if (!v.paused) v.pause();
        }
    }

    function filtrar(entradas) {
        return entradas.filter((e) => {
            if (state.categoriaActiva && e.categoria !== state.categoriaActiva) return false;
            if (state.busqueda && !e.palabra.toLowerCase().includes(state.busqueda)) return false;
            return true;
        });
    }

    function actualizarStats(filtradas) {
        const total = state.entradas.length;
        const mostradas = filtradas.length;
        dom.stats.innerHTML = mostradas === total
            ? `Mostrando <strong>${total}</strong> entradas del diccionario.`
            : `Mostrando <strong>${mostradas}</strong> de <strong>${total}</strong> entradas.`;
    }

    function crearCard(entrada) {
        const card = document.createElement('article');
        card.className = 'dic-card';

        const media = document.createElement('div');
        media.className = 'dic-card__media';

        const fallback = document.createElement('div');
        fallback.className = 'dic-card__fallback';
        fallback.innerHTML = `
            <span class="dic-card__fallback-tag">Recurso pendiente</span>
            <p style="margin:0;font-weight:700;color:#dce5f1">${formatoPalabra(entrada.palabra)}</p>
        `;
        fallback.hidden = true;

        // Si el resolver del backend no encontró archivo, vamos directo al fallback.
        if (entrada.existe === false) {
            fallback.hidden = false;
            media.appendChild(fallback);
        } else if (entrada.media_type === 'video') {
            // Lazy: NO seteamos `src` aún. Lo guardamos en `data-src` y el
            // IntersectionObserver lo inyecta cuando la card entra al viewport.
            const video = document.createElement('video');
            video.className = 'dic-card__video';
            video.dataset.src = entrada.gif_url;
            video.muted = true;
            video.loop = true;
            video.playsInline = true;
            video.preload = 'none';            // crítico: evita el HTTP request hasta visibilidad
            video.setAttribute('aria-label', `Seña: ${entrada.palabra}`);
            video.addEventListener('error', () => {
                video.remove();
                fallback.hidden = false;
            });
            media.appendChild(video);
            media.appendChild(fallback);
            if (state.observer) state.observer.observe(video);
        } else {
            const img = document.createElement('img');
            img.loading = 'lazy';
            img.alt = `Seña: ${entrada.palabra}`;
            img.src = entrada.gif_url;
            img.addEventListener('error', () => {
                img.remove();
                fallback.hidden = false;
            });
            media.appendChild(img);
            media.appendChild(fallback);
        }

        const body = document.createElement('div');
        body.className = 'dic-card__body';
        body.innerHTML = `
            <h3 class="dic-card__word">${formatoPalabra(entrada.palabra)}</h3>
            ${entrada.descripcion ? `<p class="dic-card__desc">${entrada.descripcion}</p>` : ''}
            <div class="dic-card__meta">
                <span class="dic-badge dic-badge--${entrada.tipo}">${entrada.tipo}</span>
                <span class="dic-card__category">${entrada.categoria}</span>
            </div>
        `;

        card.appendChild(media);
        card.appendChild(body);
        return card;
    }

    function formatoPalabra(p) {
        if (!p) return '';
        return p.replace(/_/g, ' ');
    }

    function debounce(fn, ms) {
        let t;
        return (...args) => {
            clearTimeout(t);
            t = setTimeout(() => fn.apply(null, args), ms);
        };
    }
})();
