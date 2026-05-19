/* ============================================================
   Señas Co — Chat con modelo local (GPT4All) — versión streaming
   ============================================================ */

(() => {
    const form    = document.getElementById('chatForm');
    const input   = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSend');
    const win     = document.getElementById('chatWindow');

    if (!form || !input || !win) return;

    const firstTime = win.querySelector('.msg__time');
    if (firstTime) firstTime.textContent = formatTime();

    let aborter = null;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const texto = input.value.trim();
        if (!texto) return;

        addMessage(texto, 'user');
        input.value = '';
        setBusy(true);

        // Burbuja del bot con indicador "typing" — la reutilizamos para
        // ir escribiendo los tokens conforme llegan.
        const botBubble = addStreamingMessage();

        // Permitimos cancelar la generación si el usuario cierra/cambia.
        aborter = new AbortController();

        try {
            await streamRespuesta(texto, botBubble, aborter.signal);
        } catch (err) {
            if (err.name !== 'AbortError') {
                botBubble.setError('Error de red. Verifica que el servidor esté activo.');
            }
        } finally {
            aborter = null;
            setBusy(false);
            input.focus();
        }
    });

    // ============================================================
    // Streaming
    // ============================================================

    /**
     * Llama a /api/chat/stream y va escribiendo los tokens en `bubble`.
     * Parsea Server-Sent Events: cada evento es "data: {json}\n\n".
     */
    async function streamRespuesta(mensaje, bubble, signal) {
        const res = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mensaje }),
            signal,
        });

        if (!res.ok) {
            // El servidor respondió con error antes de empezar el stream.
            let mensaje = 'No se pudo obtener respuesta.';
            try {
                const data = await res.json();
                if (data && data.error) mensaje = data.error;
            } catch (_) { /* ignore */ }
            bubble.setError(mensaje);
            return;
        }

        if (!res.body || !res.body.getReader) {
            // Navegador sin ReadableStream → fallback no-streaming.
            return fallbackNoStreaming(mensaje, bubble);
        }

        const reader  = res.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let recibioAlgo = false;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // SSE delimita eventos con doble salto de línea.
            let idx;
            while ((idx = buffer.indexOf('\n\n')) !== -1) {
                const evento = buffer.slice(0, idx);
                buffer = buffer.slice(idx + 2);

                for (const linea of evento.split('\n')) {
                    if (!linea.startsWith('data: ')) continue;
                    const payload = linea.slice(6);
                    if (payload === '[DONE]') return;

                    try {
                        const obj = JSON.parse(payload);
                        if (obj.error) {
                            bubble.setError(obj.error);
                            return;
                        }
                        if (obj.token !== undefined) {
                            if (!recibioAlgo) {
                                bubble.startWriting();
                                recibioAlgo = true;
                            }
                            bubble.appendToken(obj.token);
                        }
                    } catch (_) {
                        // payload malformado: lo ignoramos
                    }
                }
            }
        }
    }

    /**
     * Fallback: usa el endpoint no-streaming si el navegador no soporta
     * fetch streams (muy raro hoy día, pero por si acaso).
     */
    async function fallbackNoStreaming(mensaje, bubble) {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mensaje }),
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
            bubble.setError(data.error || 'No se pudo obtener respuesta.');
        } else {
            bubble.startWriting();
            bubble.appendToken(data.respuesta || '(respuesta vacía)');
        }
    }

    // ============================================================
    // DOM helpers
    // ============================================================

    function addMessage(text, kind) {
        const article = document.createElement('article');
        article.className = `msg msg--${kind === 'user' ? 'user' : kind === 'error' ? 'bot msg--error' : 'bot'}`;

        const avatar = document.createElement('div');
        avatar.className = 'msg__avatar';
        avatar.setAttribute('aria-hidden', 'true');
        avatar.textContent = kind === 'user' ? 'Tú' : 'SC';

        const bubble = document.createElement('div');
        bubble.className = 'msg__bubble';

        const p = document.createElement('p');
        p.textContent = text;

        const time = document.createElement('span');
        time.className = 'msg__time';
        time.textContent = formatTime();

        bubble.appendChild(p);
        bubble.appendChild(time);
        article.appendChild(avatar);
        article.appendChild(bubble);
        win.appendChild(article);
        scrollToBottom();
        return article;
    }

    /**
     * Crea una burbuja del bot lista para recibir tokens en streaming.
     * Devuelve un controlador con métodos: startWriting, appendToken, setError.
     */
    function addStreamingMessage() {
        const article = document.createElement('article');
        article.className = 'msg msg--bot msg--typing';

        const avatar = document.createElement('div');
        avatar.className = 'msg__avatar';
        avatar.setAttribute('aria-hidden', 'true');
        avatar.textContent = 'SC';

        const bubble = document.createElement('div');
        bubble.className = 'msg__bubble';

        // Estado inicial: dots de "escribiendo".
        const dots = document.createElement('span');
        dots.className = 'typing-dots';
        dots.setAttribute('aria-label', 'Escribiendo');
        dots.innerHTML = '<span></span><span></span><span></span>';
        bubble.appendChild(dots);

        article.appendChild(avatar);
        article.appendChild(bubble);
        win.appendChild(article);
        scrollToBottom();

        let p = null;
        let time = null;

        return {
            startWriting() {
                if (p) return;
                article.classList.remove('msg--typing');
                bubble.innerHTML = '';
                p = document.createElement('p');
                bubble.appendChild(p);
                time = document.createElement('span');
                time.className = 'msg__time';
                time.textContent = formatTime();
                bubble.appendChild(time);
            },
            appendToken(token) {
                if (!p) this.startWriting();
                p.textContent += token;
                scrollToBottom();
            },
            setError(mensaje) {
                article.classList.remove('msg--typing');
                article.classList.add('msg--error');
                bubble.innerHTML = '';
                const errP = document.createElement('p');
                errP.textContent = mensaje;
                bubble.appendChild(errP);
                const t = document.createElement('span');
                t.className = 'msg__time';
                t.textContent = formatTime();
                bubble.appendChild(t);
                scrollToBottom();
            },
        };
    }

    function setBusy(busy) {
        sendBtn.disabled = busy;
        input.disabled   = busy;
    }

    function scrollToBottom() {
        win.scrollTop = win.scrollHeight;
    }

    function formatTime() {
        const d = new Date();
        return d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
    }
})();
