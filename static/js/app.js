/*
 * SMARTBOX - Dashboard JavaScript v4.0
 */

// ===========================================
//  VARIABLES GLOBALES
// ===========================================

let selectedDuration  = null;
let customMode        = false;
let activeCode        = null;
let codeExpiresAt     = null;
let codeTotalDuration = null;
let timerInterval     = null;
let refreshInterval   = null;

const MAX_DURATION_SEC = 86400;
const VAPID_PUBLIC_KEY = 'BHNCv4H7AyiPI6tHTSIani6sgYkFMu7isFE0bBAKJKoXktQzG92HFdQxDGJ7Lz41_DS7eYTZnBqHk9LvItl06xY';

const EVENT_ICONS = {
    mail:           { icon: '📬' },
    code:           { icon: '🔑' },
    access_granted: { icon: '✅' },
    access_denied:  { icon: '❌' },
    door:           { icon: '🚪' },
    parcel:         { icon: '📦' },
    email:          { icon: '📧' },
    system:         { icon: '⚙️' },
};

// ===========================================
//  INITIALISATION
// ===========================================

document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !document.getElementById('loginPage').classList.contains('hidden')) {
            doLogin();
        }
    });
});

// Enregistre le service worker
if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
        try {
            const reg = await navigator.serviceWorker.register('/sw.js');
            console.log('SW enregistré:', reg.scope);
            window._swReg = reg;
        } catch (e) {
            console.error('SW erreur:', e);
        }
    });
}

function initDashboard() {
    refreshStatus();
    refreshInterval = setInterval(refreshStatus, 3000);
}

// ===========================================
//  AUTHENTIFICATION
// ===========================================

async function doLogin() {
    const user  = document.getElementById('loginUser').value.trim();
    const pass  = document.getElementById('loginPass').value;
    const error = document.getElementById('loginError');

    if (!user || !pass) {
        error.textContent = 'Veuillez remplir tous les champs';
        return;
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        const data = await response.json();
        if (data.success) {
            showDashboard();
        } else {
            error.textContent = data.error || 'Identifiants incorrects';
        }
    } catch (e) {
        error.textContent = 'Erreur de connexion au serveur';
    }
}

async function doLogout() {
    try { await fetch('/api/logout', { method: 'POST' }); } catch (e) {}
    clearInterval(refreshInterval);
    clearInterval(timerInterval);
    const login = document.getElementById('loginPage');
    login.style.display = 'flex';
    setTimeout(() => {
        login.style.opacity = '1';
        login.style.pointerEvents = 'all';
    }, 50);
    document.getElementById('dashboardApp').style.display = 'none';
    document.getElementById('bottomBar').classList.remove('visible');
    document.getElementById('loginPass').value = '';
    document.getElementById('loginError').textContent = '';
}

function showDashboard() {
    const login = document.getElementById('loginPage');
    login.style.opacity = '0';
    login.style.pointerEvents = 'none';
    setTimeout(() => { login.style.display = 'none'; }, 500);
    document.getElementById('dashboardApp').style.display = 'block';
    document.getElementById('bottomBar').classList.add('visible');
    initDashboard();
}

// ===========================================
//  RAFRAICHISSEMENT
// ===========================================

async function refreshStatus() {
    try {
        const response = await fetch('/api/status');

        if (response.status === 401) { doLogout(); return; }

        const data = await response.json();

        updateConnection(data.box.arduino_connected);
        updateStatusCards(data.box);

        if (data.active_code) {
            activeCode    = data.active_code.code;
            codeExpiresAt = new Date(data.active_code.expires_at.replace(' ', 'T'));
            displayCode(activeCode);
            document.getElementById('btnRevoke').disabled = false;
            if (!timerInterval) startTimer();
        }

        renderEvents(data.events);

        if (data.events && data.events.length > 0) {
            const last     = data.events[0];
            const lastTime = last.time.split(' ')[1] || last.time;
            document.getElementById('lastActivityText').textContent =
                `Dernière activité : ${lastTime} — ${last.description}`;
        }

        document.getElementById('emailToggle').checked = data.email.enabled;
        document.getElementById('emailAddress').value  = data.email.address || '';
        document.getElementById('emailInputRow').classList.toggle('enabled', data.email.enabled);

    } catch (e) {
        console.error('Erreur refresh:', e);
    }
}

function updateConnection(connected) {
    const dot  = document.getElementById('connDot');
    const text = document.getElementById('connText');
    if (connected) {
        dot.classList.add('connected');
        text.textContent = 'Arduino connecté';
    } else {
        dot.classList.remove('connected');
        text.textContent = 'Mode démo';
    }
}

function updateStatusCards(box) {
    const lockCard   = document.querySelector('.status-row .status-card:nth-child(1)');
    const parcelCard = document.querySelector('.status-row .status-card:nth-child(2)');
    const mailCard   = document.querySelector('.status-row .status-card:nth-child(3)');

    const lockIcon = document.getElementById('lockIcon');
    const lockText = document.getElementById('lockText');
    if (box.door_open) {
        lockIcon.className   = 'status-icon unlocked';
        lockIcon.textContent = '🔓';
        lockText.textContent = 'Ouverte';
        lockCard.className   = 'status-card card-alert';
    } else if (box.door_locked) {
        lockIcon.className   = 'status-icon locked';
        lockIcon.textContent = '🔒';
        lockText.textContent = 'Verrouillée';
        lockCard.className   = 'status-card card-ok';
    } else {
        lockIcon.className   = 'status-icon unlocked';
        lockIcon.textContent = '🔓';
        lockText.textContent = 'Déverrouillée';
        lockCard.className   = 'status-card card-alert';
    }

    const parcelIcon = document.getElementById('parcelIcon');
    const parcelText = document.getElementById('parcelText');
    if (box.parcel_present) {
        parcelIcon.className   = 'status-icon parcel-yes';
        parcelText.textContent = 'Colis détecté !';
        parcelText.style.color = 'var(--orange)';
        parcelCard.className   = 'status-card card-alert';
    } else {
        parcelIcon.className   = 'status-icon parcel-no';
        parcelText.textContent = 'Vide';
        parcelText.style.color = '';
        parcelCard.className   = 'status-card card-ok';
    }

    const mailIcon = document.getElementById('mailIcon');
    const mailText = document.getElementById('mailText');
    if (box.mail_present) {
        mailIcon.className   = 'status-icon mail-yes';
        mailText.textContent = 'Courrier reçu !';
        mailText.style.color = 'var(--purple)';
        mailCard.className   = 'status-card card-alert';
    } else {
        mailIcon.className   = 'status-icon mail-no';
        mailText.textContent = 'Aucun';
        mailText.style.color = '';
        mailCard.className   = 'status-card card-ok';
    }
}

// ===========================================
//  GESTION DES CODES
// ===========================================

function selectDuration(value, btn) {
    document.querySelectorAll('.dur-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const customRow = document.getElementById('customDurationRow');
    if (value === 'custom') {
        customMode = true; selectedDuration = null;
        customRow.classList.add('visible');
    } else {
        customMode = false; selectedDuration = value;
        customRow.classList.remove('visible');
    }
}

function validateCustomDuration() {
    if (document.getElementById('customH').value < 0)  document.getElementById('customH').value = 0;
    if (document.getElementById('customM').value < 0)  document.getElementById('customM').value = 0;
    if (document.getElementById('customS').value < 0)  document.getElementById('customS').value = 0;
    if (document.getElementById('customM').value > 59) document.getElementById('customM').value = 59;
    if (document.getElementById('customS').value > 59) document.getElementById('customS').value = 59;
    if (document.getElementById('customH').value > 24) document.getElementById('customH').value = 24;

    const total = getSelectedDurationSeconds();
    if (total > MAX_DURATION_SEC) {
        document.getElementById('customH').value = 24;
        document.getElementById('customM').value = 0;
        document.getElementById('customS').value = 0;
        showToast('⚠️ Durée max : 24h — valeur ajustée');
    }
}

function getSelectedDurationSeconds() {
    if (customMode) {
        const h = parseInt(document.getElementById('customH').value) || 0;
        const m = parseInt(document.getElementById('customM').value) || 0;
        const s = parseInt(document.getElementById('customS').value) || 0;
        return Math.min(Math.max(0, h * 3600 + m * 60 + s), MAX_DURATION_SEC);
    }
    return selectedDuration ? selectedDuration * 60 : 3600;
}

async function generateCode() {
    if (!selectedDuration && !customMode) {
        showToast("⚠️ Choisissez une durée d'abord"); return;
    }
    if (customMode && getSelectedDurationSeconds() < 1) {
        showToast("⚠️ Veuillez entrer une durée"); return;
    }
    if (activeCode && codeExpiresAt && new Date() < codeExpiresAt) {
        showModal(); return;
    }
    await doGenerateCode();
}

async function confirmNewCode() {
    closeModal();
    await doGenerateCode();
}

async function doGenerateCode() {
    const btn = document.getElementById('btnGenerate');
    btn.disabled  = true;
    btn.innerHTML = '⏳ Génération...';

    const durationSec = getSelectedDurationSeconds();

    try {
        const response = await fetch('/api/generate-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ duration_seconds: durationSec })
        });
        const data = await response.json();

        if (data.success) {
            activeCode        = data.code;
            codeExpiresAt     = new Date(data.expires_at.replace(' ', 'T'));
            codeTotalDuration = durationSec * 1000;

            displayCode(activeCode);
            startTimer();
            document.getElementById('btnRevoke').disabled = false;

            try {
                await navigator.clipboard.writeText(activeCode);
                const hint = document.getElementById('copyHint');
                hint.classList.add('visible');
                setTimeout(() => hint.classList.remove('visible'), 3000);
            } catch (e) {}

            showToast(`🔑 Code ${activeCode} généré`);
        } else {
            showToast('❌ ' + (data.error || 'Erreur'));
        }
    } catch (e) {
        showToast('❌ Erreur de connexion');
    }

    btn.disabled  = false;
    btn.innerHTML = '🔑 Générer un code';
}

async function revokeCode() {
    if (!activeCode) return;
    try { await fetch('/api/revoke-code', { method: 'POST' }); } catch (e) {}

    activeCode = null; codeExpiresAt = null; codeTotalDuration = null;
    clearInterval(timerInterval);
    timerInterval = null;

    document.getElementById('codeDisplay').className   = 'code-placeholder';
    document.getElementById('codeDisplay').textContent = '• • • •';
    document.getElementById('codeTimer').textContent   = '';
    document.getElementById('codeProgressWrap').style.display = 'none';
    document.getElementById('btnRevoke').disabled = true;

    showToast('🚫 Code révoqué');
}

// ===========================================
//  AFFICHAGE CODE & TIMER
// ===========================================

function displayCode(code) {
    const el = document.getElementById('codeDisplay');
    el.className = 'code-digits';
    el.innerHTML = code.split('').map(d =>
        `<span class="code-digit">${d}</span>`
    ).join('');
}

function startTimer() {
    clearInterval(timerInterval);
    updateTimer();
    timerInterval = setInterval(updateTimer, 1000);
}

function updateTimer() {
    if (!codeExpiresAt) return;

    const diff = codeExpiresAt - new Date();

    if (diff <= 0) {
        clearInterval(timerInterval);
        timerInterval = null;
        document.getElementById('codeDisplay').className = 'code-digits expired';
        document.getElementById('codeTimer').innerHTML   = '⏰ <strong class="critical">Code expiré</strong>';
        document.getElementById('codeProgressWrap').style.display = 'none';
        document.getElementById('btnRevoke').disabled = true;
        activeCode = null;
        showToast('⏰ Le code a expiré');
        return;
    }

    const wrap = document.getElementById('codeProgressWrap');
    const bar  = document.getElementById('codeProgressBar');
    wrap.style.display = 'block';
    const pct = codeTotalDuration ? Math.max(0, (diff / codeTotalDuration) * 100) : 100;
    bar.style.width = pct + '%';
    bar.className   = 'code-progress-bar' +
        (diff < 10000 ? ' critical' : diff < 60000 ? ' warning' : '');

    const totalSec = Math.floor(diff / 1000);
    const h = Math.floor(totalSec / 3600);
    const m = Math.floor((totalSec % 3600) / 60);
    const s = totalSec % 60;

    let timeStr;
    if (h > 0)      timeStr = `${h}h ${String(m).padStart(2,'0')}min ${String(s).padStart(2,'0')}s`;
    else if (m > 0) timeStr = `${m}min ${String(s).padStart(2,'0')}s`;
    else            timeStr = `${s}s`;

    const cls = diff < 10000 ? 'critical' : diff < 60000 ? 'warning' : '';
    document.getElementById('codeTimer').innerHTML =
        `⏱️ Expire dans <strong class="${cls}">${timeStr}</strong>`;
}

// ===========================================
//  EMAIL
// ===========================================

function toggleEmail() {
    const enabled = document.getElementById('emailToggle').checked;
    document.getElementById('emailInputRow').classList.toggle('enabled', enabled);
    if (!enabled) saveEmailConfig(false, '');
}

async function saveEmail() {
    const email      = document.getElementById('emailAddress').value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
    if (!email || !emailRegex.test(email)) {
        showToast('❌ Adresse email invalide'); return;
    }
    await saveEmailConfig(true, email);
}

async function saveEmailConfig(enabled, address) {
    try {
        const response = await fetch('/api/email-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled, address })
        });
        const data = await response.json();
        if (data.success && enabled && address) {
            const st = document.getElementById('emailStatus');
            st.classList.add('visible');
            setTimeout(() => st.classList.remove('visible'), 3000);
            showToast(`📧 Notifications → ${address}`);
        } else if (!data.success) {
            showToast('❌ ' + (data.error || 'Erreur'));
        }
    } catch (e) {
        showToast('❌ Erreur de connexion');
    }
}

// ===========================================
//  EVENEMENTS
// ===========================================

function renderEvents(events) {
    const container = document.getElementById('eventsList');

    if (!events || !events.length) {
        container.innerHTML = '<div class="no-events">Aucun événement pour le moment</div>';
        return;
    }

    container.innerHTML = events.map(e => {
        const time = e.time.split(' ')[1] || e.time;
        const ev   = EVENT_ICONS[e.type] || EVENT_ICONS.system;
        return `
            <div class="event-item">
                <span class="event-time">${time}</span>
                <span class="event-icon ${e.type}">${ev.icon}</span>
                <span class="event-desc">${e.description}</span>
            </div>
        `;
    }).join('');
}

// ===========================================
//  MODAL
// ===========================================

function showModal() {
    document.getElementById('modalCurrentCode').textContent = activeCode;
    document.getElementById('modalOverlay').classList.add('show');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('show');
}

// ===========================================
//  TOAST
// ===========================================

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3500);
}

// ===========================================
//  PWA — NOTIFICATIONS PUSH
// ===========================================

async function subscribeToPush() {
    if (!('Notification' in window) || !('serviceWorker' in navigator)) {
        showToast('❌ Notifications non supportées');
        return;
    }

    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
        showToast('⚠️ Permission notifications refusée');
        return;
    }

    try {
        const reg = await navigator.serviceWorker.ready;
        const sub = await reg.pushManager.subscribe({
            userVisibleOnly:      true,
            applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
        });

        await fetch('/api/push-subscribe', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(sub)
        });

        showToast('🔔 Notifications activées !');
        const btn = document.getElementById('btnPush');
        if (btn) {
            btn.innerHTML = '<span class="push-icon">🔔</span><span class="push-label">Notifications activées</span>';
            btn.classList.add('push-active');
        }
    } catch (e) {
        console.error('Push erreur:', e);
        showToast('❌ Erreur activation notifications');
    }
}

function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64  = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const raw     = atob(base64);
    return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
}