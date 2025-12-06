window.initHistoryView = function initHistoryView() {
        const historyListEl = document.getElementById('history-list');
        const historyFromInput = document.getElementById('history-from');
        const historyToInput = document.getElementById('history-to');
        const historyCategorySelect = document.getElementById('history-category');

        let historyItemsAll = [];

        function renderHistory(items) {
            if (!historyListEl) return;
            if (!items.length) {
                historyListEl.innerHTML =
                    '<div class="hint">No interactions yet. Recent alerts will show here.</div>';
                return;
            }
            historyListEl.innerHTML = '';
            for (const item of items) {
                const row = document.createElement('div');
                row.className = 'history-item';

                const main = document.createElement('div');
                main.className = 'history-main';

                const task = document.createElement('div');
                task.className = 'history-task';
                task.textContent = item.task_name || '';

                const meta = document.createElement('div');
                meta.className = 'history-meta';
                const resp = item.response_type || 'none';
                const stage = item.response_stage || '';
                const metaText = document.createElement('span');
                metaText.textContent = `${item.category} · ${item.alert_type} → ${resp}${
                    stage ? ' (' + stage + ')' : ''
                }`;
                const respBadge = document.createElement('span');
                respBadge.className = 'history-badge';
                respBadge.textContent = resp;
                const respLower = resp.toLowerCase();
                if (respLower === 'acknowledge' || respLower === 'ack') {
                    respBadge.classList.add('history-badge-ack');
                } else if (respLower === 'snooze') {
                    respBadge.classList.add('history-badge-snooze');
                } else if (respLower === 'skip') {
                    respBadge.classList.add('history-badge-skip');
                } else {
                    respBadge.classList.add('history-badge-none');
                }
                meta.appendChild(metaText);
                meta.appendChild(respBadge);

                main.appendChild(task);
                main.appendChild(meta);

                const times = document.createElement('div');
                times.className = 'history-times';
                const started = (item.alert_started_at || '').slice(11, 16);
                const responded = item.responded_at ? item.responded_at.slice(11, 16) : '';
                times.textContent = responded ? `${started} → ${responded}` : `${started} → …`;

                row.appendChild(main);
                row.appendChild(times);
                historyListEl.appendChild(row);
            }
        }

        function updateHistoryCategoryOptions() {
            if (!historyCategorySelect) return;
            const seen = new Set();
            for (const item of historyItemsAll) {
                const cat = (item.category || '').trim();
                if (!cat) continue;
                seen.add(cat);
            }
            const sorted = Array.from(seen).sort((a, b) => a.localeCompare(b));
            historyCategorySelect.innerHTML = '<option value="">All categories</option>';
            for (const cat of sorted) {
                const opt = document.createElement('option');
                opt.value = cat;
                opt.textContent = cat;
                historyCategorySelect.appendChild(opt);
            }
        }

        function applyHistoryFilters() {
            if (!historyListEl) return;
            let items = historyItemsAll.slice();

            const getDateOnly = (ts) => {
                if (!ts || typeof ts !== 'string') return null;
                return ts.slice(0, 10);
            };

            const fromVal = historyFromInput && historyFromInput.value
                ? historyFromInput.value
                : '';
            const toVal = historyToInput && historyToInput.value ? historyToInput.value : '';
            const catVal = historyCategorySelect ? historyCategorySelect.value : '';

            if (fromVal) {
                items = items.filter((item) => {
                    const d = getDateOnly(item.alert_started_at || item.responded_at);
                    return d && d >= fromVal;
                });
            }
            if (toVal) {
                items = items.filter((item) => {
                    const d = getDateOnly(item.alert_started_at || item.responded_at);
                    return d && d <= toVal;
                });
            }
            if (catVal) {
                items = items.filter((item) => (item.category || '') === catVal);
            }

            items.sort((a, b) => {
                const aTs = a.alert_started_at || a.responded_at || '';
                const bTs = b.alert_started_at || b.responded_at || '';
                if (aTs < bTs) return 1;
                if (aTs > bTs) return -1;
                const aId = typeof a.id === 'number' ? a.id : 0;
                const bId = typeof b.id === 'number' ? b.id : 0;
                return bId - aId;
            });

            renderHistory(items);
        }

        async function loadHistoryInternal() {
            if (!historyListEl) return;
            try {
                const res = await fetch('/schedule/interactions/recent?limit=50');
                if (!res.ok) throw new Error('Failed to load history');
                const data = await res.json();
                historyItemsAll = Array.isArray(data) ? data : [];
                updateHistoryCategoryOptions();
                applyHistoryFilters();
            } catch (err) {
                console.error('Failed to load history', err);
            }
        }

        if (historyFromInput) {
            historyFromInput.addEventListener('change', () => {
                applyHistoryFilters();
            });
        }
        if (historyToInput) {
            historyToInput.addEventListener('change', () => {
                applyHistoryFilters();
            });
        }
        if (historyCategorySelect) {
            historyCategorySelect.addEventListener('change', () => {
                applyHistoryFilters();
            });
        }

        window.loadHistory = async function loadHistory() {
            await loadHistoryInternal();
        };

        if (historyListEl) {
            window.loadHistory();
        }
};
