window.initTodayView = function initTodayView() {
        const form = document.getElementById('task-form');
        const statusEl = document.getElementById('status');
        const tasksListEl = document.getElementById('tasks-list');
        const templateSearchInput = document.getElementById('template-search');
        const aiTemplateFreeText = document.getElementById('ai-template-free-text');
        const aiTemplateSuggestBtn = document.getElementById('ai-template-suggest-btn');
        const aiTemplateStatus = document.getElementById('ai-template-status');
        const activeBannerEl = document.getElementById('active-task-banner');
        const scheduleStatusEl = document.getElementById('schedule-status');
        const scheduleListEl = document.getElementById('schedule-list');
        const historyListEl = document.getElementById('history-list');
        const historyFromInput = document.getElementById('history-from');
        const historyToInput = document.getElementById('history-to');
        const historyCategorySelect = document.getElementById('history-category');
        const aiHistoryBtn = document.getElementById('ai-history-btn');
        const aiHistoryStatusEl = document.getElementById('ai-history-status');
        const aiHistoryInsightsEl = document.getElementById('ai-history-insights');
        const aiHistoryRecsEl = document.getElementById('ai-history-recs');
        const aiHistoryPlayBtn = document.getElementById('ai-history-play-btn');
        const aiNotesBtn = document.getElementById('ai-notes-btn');
        const aiNotesStatusEl = document.getElementById('ai-notes-status');
        const aiNotesPatternsEl = document.getElementById('ai-notes-patterns');
        const aiNotesRecsEl = document.getElementById('ai-notes-recs');
        const aiNotesPlayBtn = document.getElementById('ai-notes-play-btn');
        const alertWordingCategorySelect = document.getElementById('alert-wording-category');
        const alertWordingToneInput = document.getElementById('alert-wording-tone');
        const alertWordingMaxLengthInput = document.getElementById('alert-wording-max-length');
        const alertWordingCountInput = document.getElementById('alert-wording-count');
        const aiAlertWordingBtn = document.getElementById('ai-alert-wording-btn');
        const aiAlertWordingStatusEl = document.getElementById('ai-alert-wording-status');
        const alertWordingCurrentEl = document.getElementById('alert-wording-current');
        const aiAlertWordingOptionsEl = document.getElementById('ai-alert-wording-options');
        const addTodayNameInput = document.getElementById('add-today-name');
        const addTodayCategoryInput = document.getElementById('add-today-category');
        const addTodayDurationInput = document.getElementById('add-today-duration');
        const addTodayStartInput = document.getElementById('add-today-start');
        const addTodayBtn = document.getElementById('add-today-btn');
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
        const overlayEnabledInput = document.getElementById('overlay-enabled');
        const overlayModeSelect = document.getElementById('overlay-mode');
        const hudClockEl = document.getElementById('hud-clock');
        const topNowStripEl = document.getElementById('top-now-strip');
        const tabButtons = document.querySelectorAll('.tab-button');
        const viewToday = document.getElementById('view-today');
        const viewPlanner = document.getElementById('view-planner');
        const viewHistory = document.getElementById('view-history');
        const aiNowBtn = document.getElementById('ai-now-btn');
        const aiNowSuggestionEl = document.getElementById('ai-now-suggestion');
        const microJournalEl = document.getElementById('micro-journal');
        const microJournalLabelEl = document.getElementById('micro-journal-label');
        const microJournalInput = document.getElementById('micro-journal-input');
        const microJournalSaveBtn = document.getElementById('micro-journal-save');
        const microJournalSkipBtn = document.getElementById('micro-journal-skip');
        const microJournalStatusEl = document.getElementById('micro-journal-status');
        const microJournalState = {
            instanceId: null,
            noteType: null,
        };
        let microJournalSaving = false;
        let editingTaskId = null;
        let activeRemainingSeconds = null;
        let activeBannerBase = null;
        let countdownIntervalId = null;
        let nowNextCountdownId = null;
        let nowNextHasContent = false;
        let nowNextOverlayEnabled = true;
        let nowNextDisplayMode = 'auto';
        const NOW_NEXT_IDLE_MS = 5000;
        let lastInteractionAt = Date.now();
        let lastAlertedInstanceId = null;
        let alarmConfig = { sound: 'beep', volume_percent: 12 };
        // PA-010: audio alarm escalation after visual alert
        const ALERT_ESCALATION_DELAY_MS = 60000; // configurable (e.g. 60-120s)
        const ALERT_TTS_MAX_REPEATS = 10;
        const ALERT_TTS_INTERVAL_MS = Math.max(
            3000,
            Math.floor(ALERT_ESCALATION_DELAY_MS / ALERT_TTS_MAX_REPEATS),
        );
        let alertTtsIntervalId = null;
        let alertTtsRepeatCount = 0;
        let alarmEscalationTimeoutId = null;
        let alarmAudioContext = null;
        let alarmOscillator = null;
        let alarmContextReady = false;
        const snoozeRealertTimeouts = {};
        let templateTasksAll = [];

        function hideMicroJournal() {
            if (!microJournalEl) return;
            microJournalState.instanceId = null;
            microJournalState.noteType = null;
            microJournalEl.classList.add('micro-journal-hidden');
            if (microJournalStatusEl) {
                microJournalStatusEl.textContent = '';
                microJournalStatusEl.className = 'status-text';
            }
        }

        async function submitMicroJournalNote() {
            if (!microJournalEl || !microJournalInput) return;
            const instanceId = microJournalState.instanceId;
            const noteType = microJournalState.noteType || 'other';
            if (!instanceId) {
                hideMicroJournal();
                return;
            }

            const raw = microJournalInput.value || '';
            const text = raw.trim();
            if (!text) {
                hideMicroJournal();
                return;
            }

            if (microJournalSaving) {
                return;
            }
            microJournalSaving = true;

            if (microJournalStatusEl) {
                microJournalStatusEl.textContent = 'Saving note...';
                microJournalStatusEl.className = 'status-text';
            }
            if (microJournalSaveBtn) microJournalSaveBtn.disabled = true;
            if (microJournalSkipBtn) microJournalSkipBtn.disabled = true;

            try {
                const res = await fetch(`/schedule/instances/${instanceId}/notes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ note_type: noteType, text }),
                });
                if (!res.ok) {
                    const msg = await res.text();
                    throw new Error(msg || 'Failed to save note');
                }
                if (microJournalStatusEl) {
                    microJournalStatusEl.textContent = 'Note saved.';
                    microJournalStatusEl.className = 'status-text ok';
                }
            } catch (err) {
                console.error('Failed to save interaction note', err);
                if (microJournalStatusEl) {
                    microJournalStatusEl.textContent = 'Error saving note (optional).';
                    microJournalStatusEl.className = 'status-text error';
                }
            } finally {
                if (microJournalSaveBtn) microJournalSaveBtn.disabled = false;
                if (microJournalSkipBtn) microJournalSkipBtn.disabled = false;
                microJournalSaving = false;
                setTimeout(() => {
                    hideMicroJournal();
                }, 1500);
            }
        }

        async function maybePromptForInteractionNote(instanceId, noteType, promptText) {
            if (!instanceId) return;
            if (!microJournalEl || !microJournalInput) return;

            microJournalState.instanceId = instanceId;
            microJournalState.noteType = noteType || 'other';

            microJournalInput.value = '';
            if (microJournalStatusEl) {
                microJournalStatusEl.textContent = '';
                microJournalStatusEl.className = 'status-text';
            }
            if (microJournalLabelEl) {
                microJournalLabelEl.textContent =
                    promptText ||
                    'Why did you snooze or skip this task? (1 short sentence, optional)';
            }

            microJournalEl.classList.remove('micro-journal-hidden');
            try {
                microJournalInput.focus();
            } catch (e) {}
        }

        if (microJournalSaveBtn) {
            microJournalSaveBtn.addEventListener('click', async () => {
                await submitMicroJournalNote();
            });
        }
        if (microJournalSkipBtn) {
            microJournalSkipBtn.addEventListener('click', () => {
                hideMicroJournal();
            });
        }

        if (microJournalInput) {
            microJournalInput.addEventListener('keydown', async (event) => {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    await submitMicroJournalNote();
                } else if (event.key === 'Escape') {
                    event.preventDefault();
                    hideMicroJournal();
                }
            });
        }

        function updateHudClock() {
            if (!hudClockEl) return;
            const now = new Date();
            const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const day = days[now.getDay()];
            const month = months[now.getMonth()];
            const date = String(now.getDate()).padStart(2, '0');
            let hours = now.getHours();
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const ampm = hours >= 12 ? 'PM' : 'AM';
            hours = hours % 12;
            if (hours === 0) hours = 12;
            const timePart = `${hours}:${minutes} ${ampm}`;
            hudClockEl.textContent = `${day} · ${month} ${date} · ${timePart}`;
        }

        function switchView(target) {
            const mapping = {
                today: viewToday,
                planner: viewPlanner,
                history: viewHistory,
            };

            Object.entries(mapping).forEach(([key, section]) => {
                if (!section) return;
                if (key === target) {
                    section.classList.remove('view-hidden');
                } else {
                    section.classList.add('view-hidden');
                }
            });

            if (tabButtons && tabButtons.length) {
                tabButtons.forEach((btn) => {
                    const v = btn.getAttribute('data-view');
                    if (v === target) {
                        btn.classList.add('tab-active');
                    } else {
                        btn.classList.remove('tab-active');
                    }
                });
            }
        }

        function clearCountdown() {
            if (countdownIntervalId !== null) {
                clearInterval(countdownIntervalId);
                countdownIntervalId = null;
            }
            activeRemainingSeconds = null;
            activeBannerBase = null;
            if (nowNextCountdownId !== null) {
                clearInterval(nowNextCountdownId);
                nowNextCountdownId = null;
            }
        }

        function clearSnoozeRealert(instanceId) {
            if (!instanceId) return;
            const existing = snoozeRealertTimeouts[instanceId];
            if (existing) {
                clearTimeout(existing);
                delete snoozeRealertTimeouts[instanceId];
            }
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
            if (!activeBannerBase) return;
            const suffix =
                activeRemainingSeconds != null
                    ? ` · ${formatRemaining(activeRemainingSeconds)}`
                    : '';
            const text = `${activeBannerBase}${suffix}`;
            if (activeBannerEl) {
                activeBannerEl.textContent = text;
            }
            if (topNowStripEl) {
                topNowStripEl.textContent = text;
            }
        }

        function renderNowNextOverlay(items) {
            const container = document.getElementById('now-next-content');
            const wrapper = document.getElementById('now-next');
            if (!container || !wrapper) return;

            if (!items || !items.length) {
                container.className = 'now-next-empty';
                container.textContent = 'No schedule for today.';
                nowNextHasContent = true;
                updateNowNextVisibility();
                return;
            }

            const active = items.find((it) => it.status === 'active');
            // Next = first future task (start time > current server_now time) sorted by planned_start_time
            let next = null;
            const sampleNow = items[0].server_now || null;
            const currentTimeStr = sampleNow ? sampleNow.slice(11, 16) : null;

            const future = items.filter((it) => {
                if (!currentTimeStr) return false;
                const start = (it.planned_start_time || '').slice(0, 5);
                return start > currentTimeStr;
            });
            if (future.length) {
                future.sort((a, b) => {
                    const sa = (a.planned_start_time || '').slice(0, 5);
                    const sb = (b.planned_start_time || '').slice(0, 5);
                    return sa.localeCompare(sb);
                });
                next = future[0];
            }

            if (!active && !next) {
                container.className = 'now-next-empty';
                container.textContent = 'No active or upcoming tasks right now.';
                nowNextHasContent = true;
                updateNowNextVisibility();
                return;
            }

            container.className = '';
            container.innerHTML = '';

            nowNextHasContent = true;

            if (active) {
                const nowBlock = document.createElement('div');
                nowBlock.className = 'now-block';

                const nowName = document.createElement('div');
                nowName.className = 'now-name';
                nowName.textContent = active.task_name || '';

                const nowMeta = document.createElement('div');
                nowMeta.className = 'now-meta-row';
                const start = (active.planned_start_time || '').slice(0, 5);
                const end = (active.planned_end_time || '').slice(0, 5);
                const windowSpan = document.createElement('span');
                windowSpan.textContent = `${start}–${end}`;
                const countdownSpan = document.createElement('span');
                countdownSpan.id = 'now-next-countdown';
                const rem =
                    typeof active.remaining_seconds === 'number'
                        ? active.remaining_seconds
                        : null;
                countdownSpan.textContent = rem != null ? formatRemaining(rem) : '';

                nowMeta.appendChild(windowSpan);
                nowMeta.appendChild(countdownSpan);

                nowBlock.appendChild(nowName);
                nowBlock.appendChild(nowMeta);
                container.appendChild(nowBlock);

                if (rem != null && nowNextCountdownId === null) {
                    let localRem = rem;
                    nowNextCountdownId = setInterval(() => {
                        const span = document.getElementById('now-next-countdown');
                        if (!span) return;
                        localRem = Math.max(0, localRem - 1);
                        span.textContent = formatRemaining(localRem);
                        if (localRem <= 0) {
                            clearInterval(nowNextCountdownId);
                            nowNextCountdownId = null;
                        }
                    }, 1000);
                }
            }

            if (next) {
                const nextBlock = document.createElement('div');
                nextBlock.className = 'next-block';

                const label = document.createElement('div');
                label.className = 'next-label';
                label.textContent = 'Next';

                const name = document.createElement('div');
                name.className = 'next-name';
                name.textContent = next.task_name || '';

                const time = document.createElement('div');
                time.className = 'next-time';
                const nStart = (next.planned_start_time || '').slice(0, 5);
                const nEnd = (next.planned_end_time || '').slice(0, 5);
                time.textContent = nStart && nEnd ? `${nStart}–${nEnd}` : nStart || '';

                nextBlock.appendChild(label);
                nextBlock.appendChild(name);
                nextBlock.appendChild(time);
                container.appendChild(nextBlock);
            }
            updateNowNextVisibility();
        }

        function markUserInteraction() {
            lastInteractionAt = Date.now();
            const wrapper = document.getElementById('now-next');
            if (!wrapper) return;
            if (!nowNextOverlayEnabled) {
                wrapper.classList.add('now-next-hidden');
                return;
            }
            if (nowNextDisplayMode === 'corner') {
                return;
            }
            wrapper.classList.add('now-next-hidden');
        }

        function updateNowNextVisibility() {
            const wrapper = document.getElementById('now-next');
            if (!wrapper) return;
            if (!nowNextOverlayEnabled || !nowNextHasContent) {
                wrapper.classList.add('now-next-hidden');
                return;
            }
            if (nowNextDisplayMode === 'corner') {
                wrapper.classList.remove('now-next-hidden');
                return;
            }
            const idleFor = Date.now() - lastInteractionAt;
            if (idleFor >= NOW_NEXT_IDLE_MS) {
                wrapper.classList.remove('now-next-hidden');
            } else {
                wrapper.classList.add('now-next-hidden');
            }
        }

        function stopAlertTtsLoop() {
            if (alertTtsIntervalId !== null) {
                clearInterval(alertTtsIntervalId);
                alertTtsIntervalId = null;
            }
            alertTtsRepeatCount = 0;
        }

        function stopAlarm() {
            stopAlertTtsLoop();
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

        function buildAlertTtsText(item) {
            if (!item) return '';
            const name = item.task_name || 'your task';
            const start = (item.planned_start_time || '').slice(0, 5);
            const end = (item.planned_end_time || '').slice(0, 5);
            if (start && end) {
                return `Time to switch: ${name}, ${start} to ${end}.`;
            }
            if (start) {
                return `Time to switch: ${name}, starting at ${start}.`;
            }
            return `Time to switch: ${name}.`;
        }

        async function announceAlertItem(item) {
            const text = buildAlertTtsText(item);
            if (!text) return;
            try {
                await fetch('/ai/tts/play', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text }),
                });
            } catch (err) {
                console.error('TTS alert announcement failed', err);
            }
        }

        function startAlertTtsLoop(item) {
            if (!item) return;
            stopAlertTtsLoop();
            alertTtsRepeatCount = 0;

            const interval =
                typeof ALERT_TTS_INTERVAL_MS === 'number' && ALERT_TTS_INTERVAL_MS > 0
                    ? ALERT_TTS_INTERVAL_MS
                    : 5000;

            const playOnce = () => {
                alertTtsRepeatCount += 1;
                announceAlertItem(item);
                if (alertTtsRepeatCount >= ALERT_TTS_MAX_REPEATS) {
                    stopAlertTtsLoop();
                }
            };

            playOnce();
            alertTtsIntervalId = setInterval(playOnce, interval);
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
            startAlertTtsLoop(item);
            startAlarmAfterDelay();
        }

        if (alertDismissBtn) {
            alertDismissBtn.addEventListener('click', () => {
                // PA-011: Acknowledge alert, log event, then hide
                const instanceId = lastAlertedInstanceId;
                const stage = alarmOscillator ? 'alarm' : 'visual';
                if (instanceId != null) {
                    clearSnoozeRealert(instanceId);
                    const url = `/schedule/instances/${instanceId}/acknowledge?stage=${encodeURIComponent(
                        stage,
                    )}`;
                    fetch(url, {
                        method: 'POST',
                    })
                        .then(() => {
                            if (typeof window.loadHistory === 'function') {
                                window.loadHistory();
                            }
                        })
                        .catch((err) => {
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
                    : typeof alarmConfig.volume_percent === 'number'
                        ? alarmConfig.volume_percent
                        : 12;
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

        if (topNowStripEl && scheduleListEl) {
            topNowStripEl.addEventListener('click', () => {
                const targetRow =
                    scheduleListEl.querySelector('.schedule-item-active') ||
                    scheduleListEl.querySelector('.schedule-item-paused');
                if (targetRow && typeof targetRow.scrollIntoView === 'function') {
                    try {
                        targetRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    } catch (e) {
                        targetRow.scrollIntoView();
                    }
                }
            });
        }

        if (tabButtons && tabButtons.length) {
            tabButtons.forEach((btn) => {
                btn.addEventListener('click', () => {
                    const target = btn.getAttribute('data-view') || 'today';
                    switchView(target);
                });
            });
            // Ensure initial view is Today
            switchView('today');
        }

        if (aiNowBtn && aiNowSuggestionEl) {
            // AI "What should I do now?" is wired in ai.js (initAIHelpers).
            // This block is kept only to ensure the elements are queried here.
        }

        async function addAdhocTodayTask() {
            if (!scheduleStatusEl || !addTodayNameInput || !addTodayStartInput) return;

            const name = (addTodayNameInput.value || '').trim();
            const rawCategory = addTodayCategoryInput ? addTodayCategoryInput.value : '';
            const category = (rawCategory || '').trim() || 'misc';
            const durationStr = addTodayDurationInput ? addTodayDurationInput.value : '';
            const start = addTodayStartInput.value;

            const duration = parseInt(durationStr || '0', 10);

            if (!name || !start) {
                scheduleStatusEl.textContent =
                    'Please provide a name and start time to add a task for today.';
                scheduleStatusEl.className = 'status-text error';
                return;
            }

            const safeDuration = Number.isFinite(duration) && duration > 0 ? duration : 60;

            const payload = {
                name,
                category,
                duration_minutes: safeDuration,
                start_time: `${start}:00`,
            };

            try {
                const res = await fetch('/schedule/adhoc-today', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (!res.ok) {
                    const text = await res.text();
                    throw new Error(text || 'Failed to add task for today');
                }

                addTodayNameInput.value = '';
                if (addTodayCategoryInput) addTodayCategoryInput.value = '';
                if (addTodayDurationInput) addTodayDurationInput.value = '';
                if (addTodayStartInput) addTodayStartInput.value = '';

                scheduleStatusEl.textContent = 'Task added to today.';
                scheduleStatusEl.className = 'status-text ok';

                await loadSchedule();
            } catch (err) {
                console.error(err);
                scheduleStatusEl.textContent = 'Error adding task to today.';
                scheduleStatusEl.className = 'status-text error';
            }
        }

        if (addTodayBtn) {
            addTodayBtn.addEventListener('click', async () => {
                await addAdhocTodayTask();
            });
        }

        async function loadSchedule() {
            if (!scheduleListEl) return;
            if (editingTaskId !== null) {
                return;
            }
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
            if (topNowStripEl) {
                topNowStripEl.textContent = 'Now: —';
                topNowStripEl.classList.remove('active', 'paused');
            }
            renderNowNextOverlay(items);

            if (!items.length) {
                scheduleListEl.innerHTML = '<div class="hint">No schedule for today yet. Add some templates to get started.</div>';
                scheduleStatusEl.textContent = '';
                return;
            }
            if (activeBannerEl || topNowStripEl) {
                const pausedItem = items.find((item) => item.status === 'paused');
                const activeItem = items.find((item) => item.status === 'active');
                const bannerItem = pausedItem || activeItem;
                if (bannerItem) {
                    const start = (bannerItem.planned_start_time || '').slice(0, 5);
                    const end = (bannerItem.planned_end_time || '').slice(0, 5);
                    const isPaused = bannerItem.status === 'paused';
                    const prefix = isPaused ? 'Paused: ' : 'Active now: ';
                    activeBannerBase = `${prefix}${bannerItem.task_name} (${start}–${end})`;

                    const hasServerRemaining =
                        typeof bannerItem.remaining_seconds === 'number' &&
                        Number.isFinite(bannerItem.remaining_seconds);
                    // Do not show a ticking countdown while paused; only for active tasks.
                    activeRemainingSeconds = !isPaused && hasServerRemaining
                        ? bannerItem.remaining_seconds
                        : null;

                    if (activeBannerEl) {
                        activeBannerEl.className = 'active-banner';
                    }
                    if (topNowStripEl) {
                        topNowStripEl.classList.remove('active', 'paused');
                        topNowStripEl.classList.add(isPaused ? 'paused' : 'active');
                    }
                    updateActiveBannerText();

                    // Visual alert when a task becomes active (PA-009)
                    if (activeItem && activeItem.id !== lastAlertedInstanceId) {
                        showAlertForItem(activeItem);
                    }

                    if (bannerItem.status === 'active' && activeRemainingSeconds != null) {
                        countdownIntervalId = setInterval(() => {
                            if (activeRemainingSeconds == null) return;
                            activeRemainingSeconds -= 1;
                            if (activeRemainingSeconds <= 0) {
                                activeRemainingSeconds = 0;
                                updateActiveBannerText();
                                clearInterval(countdownIntervalId);
                                countdownIntervalId = null;
                                // Force an immediate schedule refresh so that
                                // when the timer reaches zero, any next task
                                // becomes active and its alert is shown.
                                loadSchedule();
                                return;
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
                const adhocSuffix = item.is_adhoc ? ' · adhoc' : '';
                meta.textContent = `${item.category} · ${item.status}${adhocSuffix}`;

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

                timeInput.addEventListener('focus', () => {
                    editingTaskId = item.id;
                });
                timeInput.addEventListener('blur', () => {
                    if (editingTaskId === item.id) {
                        editingTaskId = null;
                    }
                });

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
                                if (typeof window.loadHistory === 'function') {
                                    await window.loadHistory();
                                }
                                await maybePromptForInteractionNote(
                                    item.id,
                                    'snooze',
                                    'Why did you snooze this task? (1 short sentence – optional)',
                                );
                                // Schedule a re-alert for this same task after the snooze period.
                                const ms = minutes * 60 * 1000;
                                clearSnoozeRealert(item.id);
                                snoozeRealertTimeouts[item.id] = setTimeout(async () => {
                                    try {
                                        const res2 = await fetch('/schedule/today');
                                        if (!res2.ok) {
                                            throw new Error('Failed to reload schedule after snooze');
                                        }
                                        const data2 = await res2.json();
                                        const refreshed = data2.find((it) => it.id === item.id);
                                        if (!refreshed) return;
                                        if (
                                            refreshed.status !== 'active' &&
                                            refreshed.status !== 'paused'
                                        ) {
                                            return;
                                        }
                                        showAlertForItem(refreshed);
                                    } catch (e) {
                                        console.error('Failed to re-alert after snooze', e);
                                    } finally {
                                        clearSnoozeRealert(item.id);
                                    }
                                }, ms);
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
                        if (editingTaskId === item.id) {
                            editingTaskId = null;
                        }
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
                        await maybePromptForInteractionNote(
                            item.id,
                            'skip',
                            'Why did you skip/disable this task for today? (1 short sentence – optional)',
                        );
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


        
        if (overlayEnabledInput) {
            nowNextOverlayEnabled = overlayEnabledInput.checked;
            overlayEnabledInput.addEventListener('change', () => {
                nowNextOverlayEnabled = overlayEnabledInput.checked;
                if (!nowNextOverlayEnabled) {
                    const wrapper = document.getElementById('now-next');
                    if (wrapper) {
                        wrapper.classList.add('now-next-hidden');
                    }
                } else {
                    markUserInteraction();
                    updateNowNextVisibility();
                }
            });
        }
        
        if (overlayModeSelect) {
            nowNextDisplayMode = overlayModeSelect.value || 'auto';
            const initialWrapper = document.getElementById('now-next');
            if (initialWrapper && nowNextDisplayMode === 'corner') {
                initialWrapper.classList.add('now-next-corner');
            }
            overlayModeSelect.addEventListener('change', () => {
                nowNextDisplayMode = overlayModeSelect.value || 'auto';
                const wrapper = document.getElementById('now-next');
                if (!wrapper) return;
                if (nowNextDisplayMode === 'corner') {
                    wrapper.classList.add('now-next-corner');
                } else {
                    wrapper.classList.remove('now-next-corner');
                }
                updateNowNextVisibility();
            });
        }

        // Global user interaction listeners to hide the Now & Next overlay immediately
        // and reset the idle timer whenever the user interacts with the UI.
        document.addEventListener('click', () => {
            markUserInteraction();
        });
        document.addEventListener('keydown', () => {
            markUserInteraction();
        });
        document.addEventListener('mousemove', () => {
            markUserInteraction();
        });
        document.addEventListener('touchstart', () => {
            markUserInteraction();
        });

        // Periodically check whether the user has been idle long enough to
        // show the Now & Next overlay as floating cards.
        setInterval(updateNowNextVisibility, 500);

        updateHudClock();
        setInterval(updateHudClock, 1000);

        loadSchedule();
        loadAlarmConfig();
        // High-frequency polling so the active task and alerts update almost in real time (PA-005)
        setInterval(loadSchedule, 1000);
};
