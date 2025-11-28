from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .db import Base, engine
from .routers import schedule, tasks


# Ensure tables are created on startup (simple dev-time approach)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Assistant Dashboard")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    # NOTE: keep this inline for now to avoid template complexity during early phases.
    return """<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Personal Assistant Dashboard</title>
    <style>
        :root {
            color-scheme: dark;
        }
        * {
            box-sizing: border-box;
        }
        body {
            margin: 0;
            min-height: 100vh;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: radial-gradient(circle at top, #111827 0, #020617 55%, #000 100%);
            color: #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .shell {
            width: min(1100px, 100%);
            background: linear-gradient(135deg, rgba(15,23,42,0.96), rgba(15,23,42,0.9));
            border-radius: 1.5rem;
            border: 1px solid rgba(148,163,184,0.4);
            box-shadow: 0 22px 50px rgba(15,23,42,0.9);
            padding: 1.5rem 1.75rem 1.6rem;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            margin-bottom: 1.25rem;
        }
        .title {
            font-size: 1.6rem;
            font-weight: 600;
        }
        .subtitle {
            font-size: 0.85rem;
            color: #9ca3af;
            margin-top: 0.15rem;
        }
        .pill {
            font-size: 0.75rem;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            border: 1px solid rgba(52,211,153,0.7);
            color: #6ee7b7;
            background: rgba(16,185,129,0.08);
            white-space: nowrap;
        }
        .grid {
            display: grid;
            grid-template-columns: 1.1fr 1.3fr;
            gap: 1.25rem;
        }
        .card {
            border-radius: 1rem;
            padding: 1rem 1.1rem 1.1rem;
            background: radial-gradient(circle at top left, rgba(56,189,248,0.09), rgba(15,23,42,0.98));
            border: 1px solid rgba(31,41,55,0.9);
        }
        .card h2 {
            font-size: 0.98rem;
            margin: 0 0 0.4rem;
        }
        .hint {
            font-size: 0.78rem;
            color: #9ca3af;
            margin-bottom: 0.6rem;
        }
        form {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.6rem 0.75rem;
            font-size: 0.82rem;
        }
        label {
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
        }
        input[type=\"text\"],
        input[type=\"number\"],
        select {
            border-radius: 0.5rem;
            border: 1px solid rgba(55,65,81,0.9);
            background: rgba(15,23,42,0.9);
            color: #e5e7eb;
            padding: 0.4rem 0.5rem;
            font-size: 0.82rem;
        }
        input[type=\"number\"] {
            font-variant-numeric: tabular-nums;
        }
        input[type=\"checkbox\"] {
            width: 0.95rem;
            height: 0.95rem;
            accent-color: #22c55e;
        }
        .full-row {
            grid-column: 1 / -1;
        }
        .row-inline {
            display: flex;
            align-items: center;
            gap: 0.45rem;
            font-size: 0.78rem;
            color: #9ca3af;
        }
        button[type=\"submit\"] {
            margin-top: 0.35rem;
            padding: 0.5rem 0.9rem;
            font-size: 0.82rem;
            border-radius: 0.7rem;
            border: none;
            cursor: pointer;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: #022c22;
            font-weight: 600;
            box-shadow: 0 10px 25px rgba(22,163,74,0.45);
        }
        button[type=\"submit\"]:disabled {
            opacity: 0.6;
            box-shadow: none;
            cursor: default;
        }
        .status-text {
            margin-top: 0.35rem;
            font-size: 0.78rem;
            min-height: 1.1rem;
        }
        .status-text.ok {
            color: #6ee7b7;
        }
        .status-text.error {
            color: #fca5a5;
        }
        .tasks-list {
            margin-top: 0.4rem;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
            max-height: 315px;
            overflow-y: auto;
        }
        .task-item {
            border-radius: 0.7rem;
            padding: 0.4rem 0.55rem;
            background: rgba(15,23,42,0.96);
            border: 1px solid rgba(31,41,55,0.9);
            display: flex;
            flex-direction: column;
            gap: 0.12rem;
            font-size: 0.8rem;
        }
        .task-item-header {
            display: flex;
            justify-content: space-between;
            gap: 0.4rem;
        }
        .task-name {
            font-weight: 500;
        }
        .badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
        }
        .badge {
            padding: 0.1rem 0.45rem;
            border-radius: 999px;
            border: 1px solid rgba(75,85,99,0.9);
            background: rgba(15,23,42,0.95);
            font-size: 0.7rem;
            color: #9ca3af;
        }
        .actions-row {
            margin-top: 0.35rem;
            display: flex;
            gap: 0.35rem;
            font-size: 0.75rem;
        }
        .action-btn {
            padding: 0.28rem 0.6rem;
            border-radius: 999px;
            border: 1px solid rgba(75,85,99,0.9);
            background: rgba(15,23,42,0.95);
            color: #e5e7eb;
            cursor: pointer;
        }
        .action-btn.edit {
            border-color: rgba(59,130,246,0.9);
            color: #bfdbfe;
        }
        .action-btn.delete {
            border-color: rgba(248,113,113,0.9);
            color: #fecaca;
        }
        .divider {
            margin: 0.75rem 0 0.65rem;
            border: none;
            border-top: 1px solid rgba(30,64,175,0.7);
        }
        .active-banner {
            margin-bottom: 0.4rem;
            font-size: 0.8rem;
            padding: 0.35rem 0.6rem;
            border-radius: 0.75rem;
            border: 1px solid rgba(34,197,94,0.55);
            background: radial-gradient(circle at left, rgba(34,197,94,0.25), transparent 65%);
            color: #bbf7d0;
        }
        .active-banner.empty {
            border-color: rgba(75,85,99,0.85);
            background: rgba(15,23,42,0.96);
            color: #9ca3af;
        }
        .schedule-section-title {
            font-size: 0.95rem;
            margin: 0 0 0.35rem;
        }
        .schedule-list {
            margin-top: 0.35rem;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
            max-height: 260px;
            overflow-y: auto;
        }
        .alarm-settings {
            margin-top: 0.6rem;
            padding: 0.55rem 0.6rem;
            border-radius: 0.75rem;
            background: rgba(15,23,42,0.96);
            border: 1px solid rgba(55,65,81,0.9);
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
            font-size: 0.8rem;
        }
        .alarm-settings-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
        }
        .alarm-label {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            flex: 1;
        }
        .alarm-select {
            border-radius: 0.5rem;
            border: 1px solid rgba(55,65,81,0.9);
            background: rgba(15,23,42,0.9);
            color: #e5e7eb;
            padding: 0.3rem 0.4rem;
            font-size: 0.8rem;
        }
        .alarm-volume {
            width: 100%;
        }
        .alarm-settings-actions {
            justify-content: flex-end;
        }
        .schedule-item {
            border-radius: 0.7rem;
            padding: 0.4rem 0.5rem;
            background: rgba(15,23,42,0.96);
            border: 1px solid rgba(30,64,175,0.75);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.6rem;
            font-size: 0.8rem;
        }
        .schedule-item-cancelled {
            opacity: 0.65;
        }
        .schedule-item-active {
            border-color: rgba(34,197,94,0.9);
            box-shadow: 0 0 0 1px rgba(34,197,94,0.5);
        }
        .schedule-item-paused {
            border-color: rgba(245,158,11,0.95);
            box-shadow: 0 0 0 1px rgba(245,158,11,0.55);
        }
        .schedule-main {
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
        }
        .schedule-name {
            font-weight: 500;
        }
        .schedule-meta {
            font-size: 0.75rem;
            color: #9ca3af;
        }
        .schedule-controls {
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }
        .schedule-controls input[type="time"] {
            border-radius: 0.4rem;
            border: 1px solid rgba(55,65,81,0.9);
            background: rgba(15,23,42,0.9);
            color: #e5e7eb;
            padding: 0.22rem 0.35rem;
            font-size: 0.78rem;
        }
        .footer {
            margin-top: 1.15rem;
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            font-size: 0.75rem;
            color: #9ca3af;
        }
        .alert-overlay {
            position: fixed;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(0,0,0,0.1);
            z-index: 40;
            pointer-events: auto;
            animation: alert-flicker 0.7s infinite alternate;
        }
        .alert-overlay.hidden {
            display: none;
            animation: none;
        }
        .alert-content {
            padding: 1.25rem 1.5rem;
            border-radius: 0.9rem;
            background: rgba(15,23,42,0.98);
            border: 1px solid rgba(248,250,252,0.9);
            box-shadow: 0 18px 40px rgba(0,0,0,0.8);
            text-align: center;
            max-width: 420px;
        }
        .alert-title {
            font-size: 1.05rem;
            font-weight: 600;
            margin-bottom: 0.4rem;
        }
        .alert-body {
            font-size: 0.9rem;
            margin-bottom: 0.8rem;
            color: #e5e7eb;
        }
        .alert-task-name {
            font-weight: 600;
        }
        .alert-dismiss-btn {
            padding: 0.45rem 0.9rem;
            border-radius: 999px;
            border: none;
            cursor: pointer;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: #022c22;
            font-weight: 600;
            font-size: 0.85rem;
        }
        @keyframes alert-flicker {
            0% {
                background-color: rgba(239,68,68,0.82);
            }
            50% {
                background-color: rgba(234,179,8,0.85);
            }
            100% {
                background-color: rgba(56,189,248,0.8);
            }
        }
        @media (max-width: 900px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <main class="shell">
        <div id="alert-overlay" class="alert-overlay hidden">
            <div class="alert-content">
                <div class="alert-title">Time to switch</div>
                <div class="alert-body">
                    <span class="alert-task-name" id="alert-task-name"></span>
                    <span id="alert-task-window"></span>
                </div>
                <button id="alert-dismiss" type="button" class="alert-dismiss-btn">Acknowledge</button>
            </div>
        </div>
        <header class="header">
            <div>
                <div class="title">Personal Assistant Dashboard</div>
                <div class="subtitle">Phase 1 – Task templates (PA-001) wired to the FastAPI backend.</div>
            </div>
            <div class="pill">Task templates · PA-001</div>
        </header>
        <section class="grid">
            <section class="card">
                <h2>New Task Template</h2>
                <p class="hint">Fill this form to add recurring blocks like work, coding, gym, dog walks, and more.</p>
                <form id="task-form" autocomplete="off">
                    <label>
                        Name
                        <input id="name" name="name" type="text" required />
                    </label>
                    <label>
                        Category
                        <input id="category" name="category" type="text" placeholder="work / coding / gym / dog / chore / sleep / supplements" required />
                    </label>
                    <label>
                        Default duration (minutes)
                        <input id="default_duration_minutes" name="default_duration_minutes" type="number" min="1" step="1" required />
                    </label>
                    <label>
                        Recurrence
                        <input id="recurrence_pattern" name="recurrence_pattern" type="text" placeholder="daily / weekdays / custom JSON" />
                    </label>
                    <label class="full-row">
                        Preferred time window
                        <input id="preferred_time_window" name="preferred_time_window" type="text" placeholder="e.g. 07:00-09:00 or evenings" />
                    </label>
                    <label>
                        Alert style
                        <select id="default_alert_style" name="default_alert_style">
                            <option value="visual_then_alarm" selected>visual_then_alarm</option>
                            <option value="visual_only">visual_only</option>
                            <option value="alarm_only">alarm_only</option>
                        </select>
                    </label>
                    <div class="row-inline">
                        <input id="enabled" name="enabled" type="checkbox" checked />
                        <label for="enabled">Enabled</label>
                    </div>
                    <div class="full-row">
                        <button id="submit-btn" type="submit">Save template</button>
                        <div id="status" class="status-text"></div>
                    </div>
                </form>
            </section>
            <section class="card">
                <h2>Existing Templates</h2>
                <p class="hint">Templates are stored in SQLite via SQLAlchemy and persist across restarts.</p>
                <div id="tasks-list" class="tasks-list"></div>
                <hr class="divider" />
                <h2 class="schedule-section-title">Today's Schedule</h2>
                <p class="hint">Auto-generated from enabled templates, ordered by start time.</p>
                <div id="active-task-banner" class="active-banner"></div>
                <div id="schedule-status" class="status-text"></div>
                <div id="schedule-list" class="schedule-list"></div>
                <hr class="divider" />
                <h2 class="schedule-section-title">Alarm Settings</h2>
                <p class="hint">Choose alarm sound and volume. These settings are saved and used for alerts.</p>
                <div id="alarm-settings" class="alarm-settings">
                    <div class="alarm-settings-row">
                        <label class="alarm-label">
                            Sound
                            <select id="alarm-sound" class="alarm-select">
                                <option value="beep">Beep</option>
                                <option value="chime">Chime</option>
                            </select>
                        </label>
                    </div>
                    <div class="alarm-settings-row">
                        <label class="alarm-label">
                            <span id="alarm-volume-label">Volume: 12%</span>
                            <input
                                id="alarm-volume"
                                class="alarm-volume"
                                type="range"
                                min="0"
                                max="100"
                                step="1"
                                value="12"
                            />
                        </label>
                    </div>
                    <div class="alarm-settings-row alarm-settings-actions">
                        <button id="alarm-save" type="button" class="action-btn edit">Save</button>
                        <button id="alarm-test" type="button" class="action-btn">Test</button>
                    </div>
                </div>
            </section>
        </section>
        <footer class="footer">
            <span>Backend: FastAPI · SQLite · SQLAlchemy</span>
            <span>Epics: Task & schedule management first, then scheduler & alerts.</span>
        </footer>
    </main>
    <script>
        const form = document.getElementById('task-form');
        const statusEl = document.getElementById('status');
        const tasksListEl = document.getElementById('tasks-list');
        const activeBannerEl = document.getElementById('active-task-banner');
        const scheduleStatusEl = document.getElementById('schedule-status');
        const scheduleListEl = document.getElementById('schedule-list');
        const submitBtn = document.getElementById('submit-btn');
        const alertOverlay = document.getElementById('alert-overlay');
        const alertTaskNameEl = document.getElementById('alert-task-name');
        const alertTaskWindowEl = document.getElementById('alert-task-window');
        const alertDismissBtn = document.getElementById('alert-dismiss');
        const alarmSoundSelect = document.getElementById('alarm-sound');
        const alarmVolumeInput = document.getElementById('alarm-volume');
        const alarmVolumeLabel = document.getElementById('alarm-volume-label');
        const alarmSaveBtn = document.getElementById('alarm-save');
        const alarmTestBtn = document.getElementById('alarm-test');
        let editingTaskId = null;
        let activeRemainingSeconds = null;
        let activeBannerBase = null;
        let countdownIntervalId = null;
        let lastAlertedInstanceId = null;
        let alarmConfig = { sound: 'beep', volume_percent: 12 };
        // PA-010: audio alarm escalation after visual alert
        const ALERT_ESCALATION_DELAY_MS = 5000; // configurable (e.g. 60-120s)
        let alarmEscalationTimeoutId = null;
        let alarmAudioContext = null;
        let alarmOscillator = null;
        let alarmContextReady = false;

        function clearCountdown() {
            if (countdownIntervalId !== null) {
                clearInterval(countdownIntervalId);
                countdownIntervalId = null;
            }
            activeRemainingSeconds = null;
            activeBannerBase = null;
        }

        function formatRemaining(seconds) {
            if (seconds == null || Number.isNaN(seconds)) return '';
            const clamped = Math.max(0, seconds);
            const h = Math.floor(clamped / 3600);
            const m = Math.floor((clamped % 3600) / 60);
            const s = clamped % 60;
            const hh = h > 0 ? String(h).padStart(2, '0') + ':' : '';
            const mm = String(m).padStart(2, '0');
            const ss = String(s).padStart(2, '0');
            return `${hh}${mm}:${ss}`;
        }

        function updateActiveBannerText() {
            if (!activeBannerEl || !activeBannerBase) return;
            const suffix =
                activeRemainingSeconds != null
                    ? ` · ${formatRemaining(activeRemainingSeconds)}`
                    : '';
            activeBannerEl.textContent = `${activeBannerBase}${suffix}`;
        }

        function stopAlarm() {
            if (alarmEscalationTimeoutId !== null) {
                clearTimeout(alarmEscalationTimeoutId);
                alarmEscalationTimeoutId = null;
            }
            if (alarmOscillator) {
                try {
                    alarmOscillator.stop();
                } catch (e) {}
                alarmOscillator.disconnect();
                alarmOscillator = null;
            }
        }

        function startAlarmAfterDelay() {
            if (!alertOverlay) return;
            if (alarmEscalationTimeoutId !== null) {
                clearTimeout(alarmEscalationTimeoutId);
            }
            alarmEscalationTimeoutId = setTimeout(() => {
                // Start simple continuous beep using Web Audio API
                try {
                    if (!alarmContextReady || !alarmAudioContext) return;
                    const osc = alarmAudioContext.createOscillator();
                    const gain = alarmAudioContext.createGain();
                    const sound = alarmConfig && alarmConfig.sound ? alarmConfig.sound : 'beep';
                    const volVal =
                        alarmConfig && typeof alarmConfig.volume_percent === 'number'
                            ? alarmConfig.volume_percent
                            : 12;
                    const volNorm = Math.max(0, Math.min(100, volVal)) / 100;
                    if (sound === 'chime') {
                        osc.type = 'sine';
                        osc.frequency.value = 660; // Hz
                    } else {
                        osc.type = 'square';
                        osc.frequency.value = 880; // Hz
                    }
                    gain.gain.value = volNorm;
                    osc.connect(gain);
                    gain.connect(alarmAudioContext.destination);
                    osc.start();
                    alarmOscillator = osc;
                } catch (e) {
                    console.error('Failed to start alarm audio', e);
                }
            }, ALERT_ESCALATION_DELAY_MS);
        }

        function unlockAlarmAudio() {
            try {
                const AudioCtx = window.AudioContext || window.webkitAudioContext;
                if (!AudioCtx) return;
                if (!alarmAudioContext) {
                    alarmAudioContext = new AudioCtx();
                }
                if (alarmAudioContext.state === 'suspended') {
                    alarmAudioContext.resume();
                }
                alarmContextReady = true;
            } catch (e) {
                console.error('Failed to unlock alarm audio', e);
            } finally {
                document.removeEventListener('click', unlockAlarmAudio);
            }
        }

        document.addEventListener('click', unlockAlarmAudio);

        function hideAlert() {
            if (!alertOverlay) return;
            alertOverlay.classList.add('hidden');
            stopAlarm();
        }

        function showAlertForItem(item) {
            if (!alertOverlay) return;
            lastAlertedInstanceId = item.id;
            const start = (item.planned_start_time || '').slice(0, 5);
            const end = (item.planned_end_time || '').slice(0, 5);
            if (alertTaskNameEl) {
                alertTaskNameEl.textContent = item.task_name || '';
            }
            if (alertTaskWindowEl) {
                alertTaskWindowEl.textContent = start && end ? ` ${start}–${end}` : '';
            }
            alertOverlay.classList.remove('hidden');
            // PA-013: log that an alert interaction started
            try {
                fetch(`/schedule/instances/${item.id}/interactions/start`, {
                    method: 'POST',
                }).catch((err) => {
                    console.error('Failed to start interaction log', err);
                });
            } catch (e) {
                console.error('Failed to start interaction log', e);
            }
            startAlarmAfterDelay();
        }

        if (alertDismissBtn) {
            alertDismissBtn.addEventListener('click', () => {
                // PA-011: Acknowledge alert, log event, then hide
                const instanceId = lastAlertedInstanceId;
                const stage = alarmOscillator ? 'alarm' : 'visual';
                if (instanceId != null) {
                    const url = `/schedule/instances/${instanceId}/acknowledge?stage=${encodeURIComponent(
                        stage,
                    )}`;
                    fetch(url, {
                        method: 'POST',
                    }).catch((err) => {
                        console.error('Failed to acknowledge alert', err);
                    });
                }
                hideAlert();
            });
        }

        function updateAlarmVolumeLabel() {
            if (!alarmVolumeLabel || !alarmVolumeInput) return;
            alarmVolumeLabel.textContent = `Volume: ${alarmVolumeInput.value || '0'}%`;
        }

        async function loadAlarmConfig() {
            if (!alarmSoundSelect || !alarmVolumeInput) return;
            try {
                const res = await fetch('/schedule/alarm-config');
                if (!res.ok) throw new Error('Failed to load alarm config');
                const data = await res.json();
                alarmConfig = data;
                if (data.sound) {
                    alarmSoundSelect.value = data.sound;
                }
                const vol = typeof data.volume_percent === 'number' ? data.volume_percent : 12;
                alarmVolumeInput.value = String(vol);
                updateAlarmVolumeLabel();
            } catch (err) {
                console.error('Failed to load alarm config', err);
            }
        }

        async function saveAlarmConfig() {
            if (!alarmSoundSelect || !alarmVolumeInput) return;
            const payload = {
                sound: alarmSoundSelect.value || 'beep',
                volume_percent: parseInt(alarmVolumeInput.value || '12', 10),
            };
            try {
                const res = await fetch('/schedule/alarm-config', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (!res.ok) {
                    const text = await res.text();
                    throw new Error(text || 'Failed to save alarm config');
                }
                const data = await res.json();
                alarmConfig = data;
                alarmVolumeInput.value = String(data.volume_percent ?? 12);
                updateAlarmVolumeLabel();
                scheduleStatusEl.textContent = 'Alarm settings saved.';
                scheduleStatusEl.className = 'status-text ok';
            } catch (err) {
                console.error(err);
                scheduleStatusEl.textContent = 'Error saving alarm settings.';
                scheduleStatusEl.className = 'status-text error';
            }
        }

        function playTestAlarm() {
            if (!alarmContextReady || !alarmAudioContext) return;
            try {
                const osc = alarmAudioContext.createOscillator();
                const gain = alarmAudioContext.createGain();
                const sound =
                    (alarmSoundSelect && alarmSoundSelect.value) || alarmConfig.sound || 'beep';
                const volValRaw = alarmVolumeInput
                    ? parseInt(alarmVolumeInput.value || '12', 10)
                    : alarmConfig.volume_percent ?? 12;
                const volVal = Number.isFinite(volValRaw) ? volValRaw : 12;
                const volNorm = Math.max(0, Math.min(100, volVal)) / 100;
                if (sound === 'chime') {
                    osc.type = 'sine';
                    osc.frequency.value = 660;
                } else {
                    osc.type = 'square';
                    osc.frequency.value = 880;
                }
                gain.gain.value = volNorm;
                osc.connect(gain);
                gain.connect(alarmAudioContext.destination);
                osc.start();
                setTimeout(() => {
                    try {
                        osc.stop();
                    } catch (e) {}
                    osc.disconnect();
                }, 700);
            } catch (e) {
                console.error('Failed to play test alarm', e);
            }
        }

        if (alarmVolumeInput) {
            alarmVolumeInput.addEventListener('input', updateAlarmVolumeLabel);
        }
        if (alarmSaveBtn) {
            alarmSaveBtn.addEventListener('click', async () => {
                await saveAlarmConfig();
            });
        }
        if (alarmTestBtn) {
            alarmTestBtn.addEventListener('click', () => {
                playTestAlarm();
            });
        }

        async function loadTasks() {
            try {
                const res = await fetch('/tasks/');
                if (!res.ok) throw new Error('Failed to load tasks');
                const data = await res.json();
                renderTasks(data);
            } catch (err) {
                console.error(err);
                tasksListEl.innerHTML = '<div class="hint">Could not load templates. Check that the backend is running.</div>';
            }
        }

        function renderTasks(tasks) {
            if (!tasks.length) {
                tasksListEl.innerHTML = '<div class="hint">No templates yet. Use the form on the left to create your first one.</div>';
                return;
            }
            tasksListEl.innerHTML = '';
            for (const t of tasks) {
                const item = document.createElement('article');
                item.className = 'task-item';

                const header = document.createElement('div');
                header.className = 'task-item-header';

                const nameSpan = document.createElement('span');
                nameSpan.className = 'task-name';
                nameSpan.textContent = t.name;

                const durationSpan = document.createElement('span');
                durationSpan.textContent = `${t.default_duration_minutes} min`;
                durationSpan.style.fontVariantNumeric = 'tabular-nums';
                durationSpan.style.color = '#9ca3af';

                header.appendChild(nameSpan);
                header.appendChild(durationSpan);

                const badges = document.createElement('div');
                badges.className = 'badge-row';

                const cat = document.createElement('span');
                cat.className = 'badge';
                cat.textContent = `category: ${t.category}`;
                badges.appendChild(cat);

                if (t.recurrence_pattern) {
                    const rec = document.createElement('span');
                    rec.className = 'badge';
                    rec.textContent = `recurrence: ${t.recurrence_pattern}`;
                    badges.appendChild(rec);
                }

                if (t.preferred_time_window) {
                    const win = document.createElement('span');
                    win.className = 'badge';
                    win.textContent = `window: ${t.preferred_time_window}`;
                    badges.appendChild(win);
                }

                const alert = document.createElement('span');
                alert.className = 'badge';
                alert.textContent = `alert: ${t.default_alert_style}`;
                badges.appendChild(alert);

                const enabled = document.createElement('span');
                enabled.className = 'badge';
                enabled.textContent = t.enabled ? 'enabled' : 'disabled';
                badges.appendChild(enabled);

                const actions = document.createElement('div');
                actions.className = 'actions-row';

                const editBtn = document.createElement('button');
                editBtn.type = 'button';
                editBtn.className = 'action-btn edit';
                editBtn.textContent = 'Edit';
                editBtn.addEventListener('click', () => {
                    editingTaskId = t.id;
                    document.getElementById('name').value = t.name;
                    document.getElementById('category').value = t.category;
                    document.getElementById('default_duration_minutes').value = String(t.default_duration_minutes ?? '');
                    document.getElementById('recurrence_pattern').value = t.recurrence_pattern ?? '';
                    document.getElementById('preferred_time_window').value = t.preferred_time_window ?? '';
                    document.getElementById('default_alert_style').value = t.default_alert_style || 'visual_then_alarm';
                    document.getElementById('enabled').checked = !!t.enabled;
                    submitBtn.textContent = 'Update template';
                    statusEl.textContent = 'Editing existing template…';
                    statusEl.className = 'status-text';
                });

                const deleteBtn = document.createElement('button');
                deleteBtn.type = 'button';
                deleteBtn.className = 'action-btn delete';
                deleteBtn.textContent = 'Delete';
                deleteBtn.addEventListener('click', async () => {
                    const ok = window.confirm('Delete this template? This will remove it from future schedules.');
                    if (!ok) return;
                    try {
                        const res = await fetch(`/tasks/${t.id}`, { method: 'DELETE' });
                        if (!res.ok) {
                            const text = await res.text();
                            throw new Error(text || 'Failed to delete');
                        }
                        if (editingTaskId === t.id) {
                            editingTaskId = null;
                            form.reset();
                            document.getElementById('enabled').checked = true;
                            document.getElementById('default_alert_style').value = 'visual_then_alarm';
                            submitBtn.textContent = 'Save template';
                        }
                        await loadTasks();
                    } catch (err) {
                        console.error(err);
                        statusEl.textContent = 'Error deleting template.';
                        statusEl.className = 'status-text error';
                    }
                });

                actions.appendChild(editBtn);
                actions.appendChild(deleteBtn);

                item.appendChild(header);
                item.appendChild(badges);
                item.appendChild(actions);
                tasksListEl.appendChild(item);
            }
        }

        async function loadSchedule() {
            if (!scheduleListEl) return;
            try {
                const res = await fetch('/schedule/today');
                if (!res.ok) throw new Error('Failed to load schedule');
                const data = await res.json();
                renderSchedule(data);
            } catch (err) {
                console.error(err);
                scheduleStatusEl.textContent = "Could not load today's schedule.";
                scheduleStatusEl.className = 'status-text error';
            }
        }

        function renderSchedule(items) {
            if (!scheduleListEl) return;
            clearCountdown();
            scheduleStatusEl.className = 'status-text';
            if (activeBannerEl) {
                activeBannerEl.className = 'active-banner empty';
                activeBannerEl.textContent = 'No active task right now.';
            }
            if (!items.length) {
                scheduleListEl.innerHTML = '<div class="hint">No schedule for today yet. Add some templates to get started.</div>';
                scheduleStatusEl.textContent = '';
                return;
            }
            if (activeBannerEl) {
                const pausedItem = items.find((item) => item.status === 'paused');
                const activeItem = items.find((item) => item.status === 'active');
                const bannerItem = pausedItem || activeItem;
                if (bannerItem) {
                    const start = (bannerItem.planned_start_time || '').slice(0, 5);
                    const end = (bannerItem.planned_end_time || '').slice(0, 5);
                    const prefix = bannerItem.status === 'paused' ? 'Paused: ' : 'Active now: ';
                    activeBannerBase = `${prefix}${bannerItem.task_name} (${start}–${end})`;
                    activeRemainingSeconds =
                        typeof bannerItem.remaining_seconds === 'number'
                            ? bannerItem.remaining_seconds
                            : null;
                    activeBannerEl.className = 'active-banner';
                    updateActiveBannerText();

                    // Visual alert when a task becomes active (PA-009)
                    if (activeItem && activeItem.id !== lastAlertedInstanceId) {
                        showAlertForItem(activeItem);
                    }

                    if (bannerItem.status === 'active' && activeRemainingSeconds != null) {
                        countdownIntervalId = setInterval(() => {
                            if (activeRemainingSeconds == null) return;
                            activeRemainingSeconds -= 1;
                            if (activeRemainingSeconds < 0) {
                                activeRemainingSeconds = 0;
                            }
                            updateActiveBannerText();
                        }, 1000);
                    }
                } else {
                    hideAlert();
                }
            }
            scheduleListEl.innerHTML = '';
            for (const item of items) {
                const row = document.createElement('div');
                row.className = 'schedule-item';
                if (item.status === 'cancelled') {
                    row.classList.add('schedule-item-cancelled');
                }
                if (item.status === 'active') {
                    row.classList.add('schedule-item-active');
                }
                if (item.status === 'paused') {
                    row.classList.add('schedule-item-paused');
                }

                const main = document.createElement('div');
                main.className = 'schedule-main';

                const title = document.createElement('div');
                title.className = 'schedule-name';
                title.textContent = item.task_name;

                const meta = document.createElement('div');
                meta.className = 'schedule-meta';
                meta.textContent = `${item.category} · ${item.status}`;

                main.appendChild(title);
                main.appendChild(meta);

                const controls = document.createElement('div');
                controls.className = 'schedule-controls';

                const timeInput = document.createElement('input');
                timeInput.type = 'time';
                const start = (item.planned_start_time || '').slice(0, 5);
                if (start) {
                    timeInput.value = start;
                }

                const saveBtn = document.createElement('button');
                saveBtn.type = 'button';
                saveBtn.className = 'action-btn edit';
                saveBtn.textContent = 'Save';

                const disableBtn = document.createElement('button');
                disableBtn.type = 'button';
                disableBtn.className = 'action-btn delete';
                if (item.status === 'cancelled') {
                    disableBtn.textContent = 'Cancelled';
                    disableBtn.disabled = true;
                } else {
                    disableBtn.textContent = 'Disable today';
                }

                const pauseResumeBtn = document.createElement('button');
                pauseResumeBtn.type = 'button';
                pauseResumeBtn.className = 'action-btn';
                let pauseResumeMode = null;
                if (item.status === 'active') {
                    pauseResumeMode = 'pause';
                    pauseResumeBtn.textContent = 'Pause';
                } else if (item.status === 'paused') {
                    pauseResumeMode = 'resume';
                    pauseResumeBtn.textContent = 'Resume';
                }

                controls.appendChild(timeInput);
                controls.appendChild(saveBtn);
                if (pauseResumeMode !== null) {
                    controls.appendChild(pauseResumeBtn);
                }
                // Snooze options for active/paused task: extend end time only (Option A)
                if (item.status === 'active' || item.status === 'paused') {
                    const snoozeContainer = document.createElement('div');
                    snoozeContainer.style.display = 'flex';
                    snoozeContainer.style.gap = '0.25rem';
                    const snoozeOptions = [5, 10, 15];
                    for (const minutes of snoozeOptions) {
                        const snoozeBtn = document.createElement('button');
                        snoozeBtn.type = 'button';
                        snoozeBtn.className = 'action-btn';
                        snoozeBtn.textContent = `+${minutes}m`;
                        snoozeBtn.addEventListener('click', async () => {
                            const payload = { minutes };
                            const stage = alarmOscillator ? 'alarm' : 'visual';
                            try {
                                const url = `/schedule/instances/${item.id}/snooze?stage=${encodeURIComponent(
                                    stage,
                                )}`;
                                const res = await fetch(url, {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify(payload),
                                });
                                if (!res.ok) {
                                    const text = await res.text();
                                    throw new Error(text || 'Failed to snooze task');
                                }
                                hideAlert();
                                scheduleStatusEl.textContent = `Task snoozed by +${minutes} minutes.`;
                                scheduleStatusEl.className = 'status-text ok';
                                await loadSchedule();
                            } catch (err) {
                                console.error(err);
                                scheduleStatusEl.textContent = 'Error snoozing task.';
                                scheduleStatusEl.className = 'status-text error';
                            }
                        });
                        snoozeContainer.appendChild(snoozeBtn);
                    }
                    controls.appendChild(snoozeContainer);
                }
                controls.appendChild(disableBtn);

                row.appendChild(main);
                row.appendChild(controls);
                scheduleListEl.appendChild(row);

                saveBtn.addEventListener('click', async () => {
                    const newTime = timeInput.value;
                    if (!newTime) {
                        scheduleStatusEl.textContent = 'Please choose a start time before saving.';
                        scheduleStatusEl.className = 'status-text error';
                        return;
                    }
                    const payload = { planned_start_time: `${newTime}:00` };
                    try {
                        const res = await fetch(`/schedule/instances/${item.id}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload),
                        });
                        if (!res.ok) {
                            const text = await res.text();
                            throw new Error(text || 'Failed to update schedule');
                        }
                        scheduleStatusEl.textContent = 'Schedule updated.';
                        scheduleStatusEl.className = 'status-text ok';
                        await loadSchedule();
                    } catch (err) {
                        console.error(err);
                        scheduleStatusEl.textContent = 'Error updating schedule.';
                        scheduleStatusEl.className = 'status-text error';
                    }
                });

                disableBtn.addEventListener('click', async () => {
                    if (item.status === 'cancelled') return;
                    const ok = window.confirm('Disable this task for today?');
                    if (!ok) return;
                    const payload = { status: 'cancelled' };
                    try {
                        const res = await fetch(`/schedule/instances/${item.id}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload),
                        });
                        if (!res.ok) {
                            const text = await res.text();
                            throw new Error(text || 'Failed to disable for today');
                        }
                        scheduleStatusEl.textContent = 'Task disabled for today.';
                        scheduleStatusEl.className = 'status-text ok';
                        await loadSchedule();
                    } catch (err) {
                        console.error(err);
                        scheduleStatusEl.textContent = 'Error disabling task for today.';
                        scheduleStatusEl.className = 'status-text error';
                    }
                });

                if (pauseResumeMode !== null) {
                    pauseResumeBtn.addEventListener('click', async () => {
                        const newStatus = pauseResumeMode === 'pause' ? 'paused' : 'active';
                        const payload = { status: newStatus };
                        try {
                            const res = await fetch(`/schedule/instances/${item.id}`, {
                                method: 'PUT',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(payload),
                            });
                            if (!res.ok) {
                                const text = await res.text();
                                throw new Error(text || 'Failed to update status');
                            }
                            scheduleStatusEl.textContent =
                                newStatus === 'paused' ? 'Task paused.' : 'Task resumed.';
                            scheduleStatusEl.className = 'status-text ok';
                            if (newStatus === 'paused') {
                                hideAlert();
                            }
                            await loadSchedule();
                        } catch (err) {
                            console.error(err);
                            scheduleStatusEl.textContent = 'Error updating task status.';
                            scheduleStatusEl.className = 'status-text error';
                        }
                    });
                }
            }
        }

        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            statusEl.textContent = '';
            statusEl.className = 'status-text';

            const name = (document.getElementById('name').value || '').trim();
            const category = (document.getElementById('category').value || '').trim();
            const durationStr = document.getElementById('default_duration_minutes').value;
            const recurrence = (document.getElementById('recurrence_pattern').value || '').trim() || null;
            const windowPref = (document.getElementById('preferred_time_window').value || '').trim() || null;
            const alertStyle = document.getElementById('default_alert_style').value;
            const enabled = document.getElementById('enabled').checked;

            const duration = parseInt(durationStr, 10);
            if (!name || !category || !Number.isFinite(duration) || duration <= 0) {
                statusEl.textContent = 'Please provide name, category, and a positive duration.';
                statusEl.classList.add('error');
                return;
            }

            const payload = {
                name,
                category,
                default_duration_minutes: duration,
                recurrence_pattern: recurrence,
                preferred_time_window: windowPref,
                default_alert_style: alertStyle,
                enabled,
            };

            submitBtn.disabled = true;
            try {
                const url = editingTaskId === null ? '/tasks/' : `/tasks/${editingTaskId}`;
                const method = editingTaskId === null ? 'POST' : 'PUT';
                const res = await fetch(url, {
                    method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (!res.ok) {
                    const text = await res.text();
                    throw new Error(text || 'Failed to save template');
                }
                form.reset();
                document.getElementById('enabled').checked = true;
                document.getElementById('default_alert_style').value = 'visual_then_alarm';
                if (editingTaskId === null) {
                    statusEl.textContent = 'Template saved.';
                } else {
                    statusEl.textContent = 'Template updated.';
                }
                statusEl.classList.add('ok');
                editingTaskId = null;
                submitBtn.textContent = 'Save template';
                await loadTasks();
            } catch (err) {
                console.error(err);
                statusEl.textContent = 'Error saving template. See console for details.';
                statusEl.classList.add('error');
            } finally {
                submitBtn.disabled = false;
            }
        });

        loadTasks();
        loadSchedule();
        loadAlarmConfig();
        // Simple polling loop so the active task updates as time passes (PA-005)
        setInterval(loadSchedule, 30000);
    </script>
</body>
</html>"""


app.include_router(tasks.router)
app.include_router(schedule.router)
