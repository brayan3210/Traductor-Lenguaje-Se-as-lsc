/* ============================================================
   Señas Co — Auth (login, registro, 2FA, recovery, reset)
   Validación cliente + llamadas reales al backend.
   ============================================================ */

(() => {
    document.addEventListener('DOMContentLoaded', () => {
        initPasswordToggles();
        initStrengthMeter();
        initLoginForm();
        initRegisterForm();
        initOtpInputs();
        init2FAForms();
        initSetup2FA();
        initRecoverForm();
        initResetForm();
        initTabs();
        initDropzone();
    });

    /* ====================================================
       UI helpers
       ==================================================== */
    function initPasswordToggles() {
        document.querySelectorAll('[data-toggle-pass]').forEach((btn) => {
            btn.addEventListener('click', () => {
                const wrap  = btn.closest('.field__wrap');
                const input = wrap?.querySelector('input');
                if (!input) return;
                const showing = input.type === 'text';
                input.type = showing ? 'password' : 'text';
                renderEye(btn, !showing);
            });
        });
    }

    function renderEye(btn, open) {
        const svg = btn.querySelector('[data-eye]');
        if (!svg) return;
        svg.innerHTML = open
            ? '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>'
            : '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
    }

    function initStrengthMeter() {
        const input = document.getElementById('password');
        const bar   = document.getElementById('strengthBar');
        const label = document.getElementById('strengthLabel');
        if (!input || !bar) return;
        const labels = ['Muy débil', 'Débil', 'Aceptable', 'Buena', 'Excelente'];
        input.addEventListener('input', () => {
            const level = computeStrength(input.value);
            bar.dataset.level = String(level);
            if (label) label.textContent = input.value ? labels[level] : 'Mínimo 8 caracteres con letras y números';
        });
    }

    function computeStrength(pass) {
        if (!pass) return 0;
        let score = 0;
        if (pass.length >= 8)  score++;
        if (/[A-Z]/.test(pass) && /[a-z]/.test(pass)) score++;
        if (/\d/.test(pass))   score++;
        if (/[^A-Za-z0-9]/.test(pass) && pass.length >= 12) score++;
        return Math.min(score, 4);
    }

    /* ====================================================
       LOGIN (email + password)
       ==================================================== */
    function initLoginForm() {
        const form = document.getElementById('loginForm');
        if (!form) return;
        const btn = document.getElementById('loginSubmit');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearErrors(form);
            const email = form.email.value.trim();
            const pass  = form.password.value;
            let ok = true;
            if (!isEmail(email)) { setError(form, 'email', 'Correo no válido.');       ok = false; }
            if (pass.length < 6) { setError(form, 'password', 'Mínimo 6 caracteres.'); ok = false; }
            if (!ok) return;

            setLoading(btn, true);
            try {
                const data = await postJSON('/api/login', { email, password: pass });
                if (!data.success) {
                    if (data.campo) setError(form, data.campo, data.error);
                    showToast(data.error || 'Credenciales incorrectas.', 'error');
                    return;
                }
                showToast(data.requiere_2fa ? 'Verifica tu código 2FA' : '¡Bienvenido!', 'success');
                setTimeout(() => { window.location.href = data.next || '/'; }, 600);
            } catch (err) {
                showToast(err.message || 'Error de red.', 'error');
            } finally {
                setLoading(btn, false);
            }
        });

        ['email', 'password'].forEach((name) => {
            form[name]?.addEventListener('input', () => clearError(form, name));
        });
    }

    /* ====================================================
       REGISTRO
       ==================================================== */
    function initRegisterForm() {
        const form = document.getElementById('registerForm');
        if (!form) return;
        const btn = document.getElementById('registerSubmit');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearErrors(form);
            const nombres   = form.nombres.value.trim();
            const apellidos = form.apellidos.value.trim();
            const email     = form.email.value.trim();
            const pass      = form.password.value;
            const confirm   = form.confirm.value;
            const terms     = form.terms.checked;

            let ok = true;
            if (nombres.length   < 2)      { setError(form, 'nombres',   'Ingresa tu nombre.');         ok = false; }
            if (apellidos.length < 2)      { setError(form, 'apellidos', 'Ingresa tus apellidos.');     ok = false; }
            if (!isEmail(email))           { setError(form, 'email',     'Correo no válido.');          ok = false; }
            if (computeStrength(pass) < 2) { setError(form, 'password',  'Contraseña demasiado débil.'); ok = false; }
            if (pass !== confirm)          { setError(form, 'confirm',   'Las contraseñas no coinciden.'); ok = false; }
            if (!terms) {
                showToast('Debes aceptar los términos y la política de privacidad.', 'error');
                ok = false;
            }
            if (!ok) return;

            setLoading(btn, true);
            try {
                const data = await postJSON('/api/registro', {
                    nombres, apellidos, email, password: pass,
                });
                if (!data.success) {
                    if (data.campo) setError(form, data.campo, data.error);
                    showToast(data.error || 'No se pudo crear la cuenta.', 'error');
                    return;
                }
                showToast('Cuenta creada · revisa tu correo', 'success');
                form.reset();
                setTimeout(() => { window.location.href = data.next || '/setup-2fa'; }, 1300);
            } catch (err) {
                showToast(err.message || 'Error de red.', 'error');
            } finally {
                setLoading(btn, false);
            }
        });

        Array.from(form.elements).forEach((el) => {
            if (el.name) el.addEventListener('input', () => clearError(form, el.name));
        });
    }

    /* ====================================================
       OTP / TOTP — input agrupado de 6 dígitos
       ==================================================== */
    function initOtpInputs() {
        const row = document.getElementById('otpRow');
        if (!row) return;
        const inputs = Array.from(row.querySelectorAll('input'));

        inputs.forEach((input, idx) => {
            input.addEventListener('input', () => {
                input.value = input.value.replace(/\D/g, '').slice(0, 1);
                if (input.value && idx < inputs.length - 1) inputs[idx + 1].focus();
            });
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Backspace' && !input.value && idx > 0) inputs[idx - 1].focus();
            });
            input.addEventListener('paste', (e) => {
                const pasted = (e.clipboardData?.getData('text') || '').replace(/\D/g, '');
                if (!pasted) return;
                e.preventDefault();
                inputs.forEach((inp, i) => { inp.value = pasted[i] || ''; });
                inputs[Math.min(pasted.length, inputs.length) - 1]?.focus();
            });
        });
    }

    function leerCodigoOtp() {
        const row = document.getElementById('otpRow');
        if (!row) return '';
        return Array.from(row.querySelectorAll('input')).map(i => i.value).join('');
    }

    /* ====================================================
       LOGIN — paso 2FA (TOTP, recovery code, recovery file)
       ==================================================== */
    function init2FAForms() {
        // TOTP
        const form = document.getElementById('form2fa');
        if (form) {
            const btn = document.getElementById('btn2fa');
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const codigo = leerCodigoOtp();
                if (codigo.length !== 6) { showToast('Ingresa los 6 dígitos.', 'error'); return; }
                setLoading(btn, true);
                try {
                    const data = await postJSON('/api/login/2fa', { codigo });
                    if (!data.success) { showToast(data.error || 'Código incorrecto.', 'error'); return; }
                    showToast('Acceso concedido', 'success');
                    setTimeout(() => { window.location.href = data.next || '/'; }, 500);
                } finally { setLoading(btn, false); }
            });
        }

        // Recovery code
        const fc = document.getElementById('formRecCode');
        if (fc) {
            const btn = document.getElementById('btnRecCode');
            fc.addEventListener('submit', async (e) => {
                e.preventDefault();
                const codigo = (fc.recCode.value || '').trim();
                if (!codigo) { showToast('Ingresa el código.', 'error'); return; }
                setLoading(btn, true);
                try {
                    const data = await postJSON('/api/login/recovery-code', { codigo });
                    if (!data.success) { showToast(data.error, 'error'); return; }
                    showToast('Código aceptado', 'success');
                    setTimeout(() => { window.location.href = data.next || '/'; }, 500);
                } finally { setLoading(btn, false); }
            });
        }

        // Recovery file
        const ff = document.getElementById('formRecFile');
        if (ff) {
            const btn = document.getElementById('btnRecFile');
            ff.addEventListener('submit', async (e) => {
                e.preventDefault();
                const file = document.getElementById('fileInput').files[0];
                if (!file) { showToast('Selecciona el archivo.', 'error'); return; }
                setLoading(btn, true);
                try {
                    const fd = new FormData();
                    fd.append('archivo', file);
                    const res = await fetch('/api/login/recovery-file', { method: 'POST', body: fd });
                    const data = await res.json();
                    if (!data.success) { showToast(data.error || 'Archivo inválido.', 'error'); return; }
                    showToast('Archivo aceptado', 'success');
                    setTimeout(() => { window.location.href = data.next || '/'; }, 500);
                } finally { setLoading(btn, false); }
            });
        }
    }

    /* ====================================================
       SETUP 2FA (post-registro)
       ==================================================== */
    async function initSetup2FA() {
        const loader = document.getElementById('setupLoader');
        const cont   = document.getElementById('setupContent');
        if (!loader || !cont) return;

        try {
            const res = await fetch('/api/2fa/setup');
            const data = await res.json();
            if (!data.success) {
                loader.className = 'alert alert--warn';
                loader.textContent = data.error || 'No se pudo iniciar la configuración.';
                return;
            }
            document.getElementById('qrImg').src = data.qr_data_url;
            document.getElementById('totpSecret').textContent = data.secret;
            loader.style.display = 'none';
            cont.style.display = 'block';
        } catch {
            loader.className = 'alert alert--warn';
            loader.textContent = 'Error de red al cargar el QR.';
        }

        const form = document.getElementById('formActivar');
        const btn  = document.getElementById('btnActivar');
        form?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const codigo = leerCodigoOtp();
            if (codigo.length !== 6) { showToast('Ingresa los 6 dígitos.', 'error'); return; }
            setLoading(btn, true);
            try {
                const data = await postJSON('/api/2fa/activar', { codigo });
                if (!data.success) { showToast(data.error || 'Código incorrecto.', 'error'); return; }
                showToast('2FA activado correctamente', 'success');
                setTimeout(() => { window.location.href = '/'; }, 900);
            } finally { setLoading(btn, false); }
        });
    }

    /* ====================================================
       RECOVER (solicitar reset por email)
       ==================================================== */
    function initRecoverForm() {
        const form = document.getElementById('formRecover');
        if (!form) return;
        const btn = document.getElementById('btnRecover');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = form.email.value.trim();
            if (!isEmail(email)) { setError(form, 'email', 'Correo no válido.'); return; }
            setLoading(btn, true);
            try {
                const data = await postJSON('/api/forgot-password', { email });
                showToast(data.mensaje || 'Si existe la cuenta, te enviamos el enlace.', 'success');
                form.reset();
            } catch (err) {
                showToast(err.message || 'Error de red.', 'error');
            } finally { setLoading(btn, false); }
        });
    }

    /* ====================================================
       RESET (definir nueva contraseña)
       ==================================================== */
    function initResetForm() {
        const form = document.getElementById('formReset');
        if (!form) return;
        const btn = document.getElementById('btnReset');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearErrors(form);
            const token   = form.token.value;
            const pass    = form.password.value;
            const confirm = form.confirm.value;
            let ok = true;
            if (computeStrength(pass) < 2) { setError(form, 'password', 'Contraseña demasiado débil.');  ok = false; }
            if (pass !== confirm)          { setError(form, 'confirm',  'Las contraseñas no coinciden.'); ok = false; }
            if (!ok) return;
            setLoading(btn, true);
            try {
                const data = await postJSON('/api/reset-password', { token, password: pass });
                if (!data.success) { showToast(data.error || 'No se pudo actualizar.', 'error'); return; }
                showToast('Contraseña actualizada', 'success');
                setTimeout(() => { window.location.href = '/login'; }, 1200);
            } finally { setLoading(btn, false); }
        });
    }

    /* ====================================================
       Tabs (login_2fa.html)
       ==================================================== */
    function initTabs() {
        const tabs    = document.querySelectorAll('.tab');
        const panels  = document.querySelectorAll('.tab-panel');
        if (!tabs.length) return;
        tabs.forEach((tab) => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('is-active'));
                panels.forEach(p => p.classList.remove('is-active'));
                tab.classList.add('is-active');
                document.querySelector(`[data-panel="${tab.dataset.tab}"]`)?.classList.add('is-active');
            });
        });
    }

    /* ====================================================
       Dropzone (recovery file upload)
       ==================================================== */
    function initDropzone() {
        const dz    = document.getElementById('dropzone');
        const input = document.getElementById('fileInput');
        const lbl   = document.getElementById('dzLabel');
        if (!dz || !input) return;

        ['dragover', 'dragenter'].forEach(evt => dz.addEventListener(evt, (e) => {
            e.preventDefault(); dz.classList.add('is-drag');
        }));
        ['dragleave', 'drop'].forEach(evt => dz.addEventListener(evt, (e) => {
            e.preventDefault(); dz.classList.remove('is-drag');
        }));
        dz.addEventListener('drop', (e) => {
            const f = e.dataTransfer?.files?.[0];
            if (f) { input.files = e.dataTransfer.files; if (lbl) lbl.textContent = f.name; }
        });
        input.addEventListener('change', () => {
            if (input.files[0] && lbl) lbl.textContent = input.files[0].name;
        });
    }

    /* ====================================================
       Helpers
       ==================================================== */
    function isEmail(s) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(s); }

    function setError(form, name, msg) {
        const span = form.querySelector(`[data-error-for="${name}"]`);
        if (span) span.textContent = msg;
        const input = form.querySelector(`[name="${name}"]`);
        if (input) input.style.borderColor = 'rgba(248, 113, 113, 0.55)';
    }
    function clearError(form, name) {
        const span = form.querySelector(`[data-error-for="${name}"]`);
        if (span) span.textContent = '';
        const input = form.querySelector(`[name="${name}"]`);
        if (input) input.style.borderColor = '';
    }
    function clearErrors(form) {
        form.querySelectorAll('[data-error-for]').forEach(s => s.textContent = '');
        form.querySelectorAll('input').forEach(i => i.style.borderColor = '');
    }

    function setLoading(btn, on) {
        if (!btn) return;
        btn.classList.toggle('is-loading', !!on);
        btn.disabled = !!on;
    }

    async function postJSON(url, body) {
        const res = await fetch(url, {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body:    JSON.stringify(body),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok && !data.error) {
            throw new Error(`HTTP ${res.status}`);
        }
        return data;
    }

    let toastTimer;
    function showToast(message, kind = 'success') {
        const el = document.getElementById('toast');
        if (!el) return;
        el.textContent = message;
        el.className = `toast is-visible toast--${kind}`;
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => { el.classList.remove('is-visible'); }, 3200);
    }
})();
