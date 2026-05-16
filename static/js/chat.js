/* ============================================================
   Señas Co — Chat con modelo local (GPT4All)
   ============================================================ */

(() => {
    const form    = document.getElementById('chatForm');
    const input   = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSend');
    const win     = document.getElementById('chatWindow');

    if (!form || !input || !win) return;

    // Hora del primer mensaje (bienvenida)
    const firstTime = win.querySelector('.msg__time');
    if (firstTime) firstTime.textContent = formatTime();

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const texto = input.value.trim();
        if (!texto) return;

        addMessage(texto, 'user');
        input.value = '';
        setBusy(true);
        const typing = addTyping();

        try {
            const res = await fetch('/api/chat', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ mensaje: texto }),
            });
            const data = await res.json();
            typing.remove();

            if (!res.ok || !data.success) {
                addMessage(data.error || 'No se pudo obtener respuesta.', 'error');
            } else {
                addMessage(data.respuesta || '(respuesta vacía)', 'bot');
            }
        } catch (err) {
            typing.remove();
            addMessage('Error de red. Verifica que el servidor esté activo.', 'error');
        } finally {
            setBusy(false);
            input.focus();
        }
    });

    // ---------- helpers ----------
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

    function addTyping() {
        const article = document.createElement('article');
        article.className = 'msg msg--bot msg--typing';
        article.innerHTML = `
            <div class="msg__avatar" aria-hidden="true">SC</div>
            <div class="msg__bubble">
                <span class="typing-dots" aria-label="Escribiendo">
                    <span></span><span></span><span></span>
                </span>
            </div>`;
        win.appendChild(article);
        scrollToBottom();
        return article;
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
