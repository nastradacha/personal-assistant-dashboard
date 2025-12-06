window.initAIHelpers = function initAIHelpers() {
        const aiNowBtn = document.getElementById('ai-now-btn');
        const aiNowSuggestionEl = document.getElementById('ai-now-suggestion');

        const historyFromInput = document.getElementById('history-from');
        const historyToInput = document.getElementById('history-to');
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

        let lastHistoryInsights = [];
        let lastHistoryRecs = [];
        let lastNotesPatterns = [];
        let lastNotesRecs = [];

        if (aiNowBtn && aiNowSuggestionEl) {
            aiNowBtn.addEventListener('click', async () => {
                aiNowSuggestionEl.textContent = 'Asking AI for a quick suggestion…';
                aiNowSuggestionEl.className = 'status-text';
                aiNowBtn.disabled = true;
                try {
                    const res = await fetch('/ai/now/suggestion');
                    if (!res.ok) {
                        const txt = await res.text();
                        throw new Error(txt || 'AI now suggestion failed');
                    }
                    const data = await res.json();
                    const suggestion = (data && data.suggestion ? String(data.suggestion) : '').trim();
                    if (!suggestion) {
                        aiNowSuggestionEl.textContent = 'AI did not return a usable suggestion.';
                        aiNowSuggestionEl.className = 'status-text error';
                        return;
                    }
                    aiNowSuggestionEl.textContent = suggestion;
                    aiNowSuggestionEl.className = 'status-text ok';
                } catch (err) {
                    console.error('AI now suggestion failed', err);
                    aiNowSuggestionEl.textContent = 'Could not get a suggestion right now.';
                    aiNowSuggestionEl.className = 'status-text error';
                } finally {
                    aiNowBtn.disabled = false;
                }
            });
        }

        if (aiHistoryBtn && aiHistoryStatusEl && aiHistoryInsightsEl && aiHistoryRecsEl) {
            aiHistoryBtn.addEventListener('click', async () => {
                aiHistoryStatusEl.textContent = 'Asking AI for an overview of recent history…';
                aiHistoryStatusEl.className = 'status-text';
                aiHistoryInsightsEl.innerHTML = '';
                aiHistoryRecsEl.innerHTML = '';
                aiHistoryBtn.disabled = true;

                const fromVal = historyFromInput && historyFromInput.value
                    ? historyFromInput.value
                    : '';
                const toVal = historyToInput && historyToInput.value ? historyToInput.value : '';

                const payload = {};
                if (fromVal) payload.start_date = fromVal;
                if (toVal) payload.end_date = toVal;

                try {
                    const res = await fetch('/ai/history/insights', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload),
                    });
                    if (!res.ok) {
                        const txt = await res.text();
                        throw new Error(txt || 'AI history insights request failed');
                    }
                    const data = await res.json();
                    const insights = Array.isArray(data.insights) ? data.insights : [];
                    const recs = Array.isArray(data.recommendations) ? data.recommendations : [];

                    lastHistoryInsights = insights.slice();
                    lastHistoryRecs = recs.slice();

                    if (!insights.length && !recs.length) {
                        aiHistoryStatusEl.textContent = 'No insights available for this range.';
                        aiHistoryStatusEl.className = 'status-text';
                        return;
                    }

                    aiHistoryStatusEl.textContent = '';
                    aiHistoryStatusEl.className = 'status-text';

                    if (insights.length) {
                        const header = document.createElement('div');
                        header.className = 'history-task';
                        header.textContent = 'Behavior patterns';
                        aiHistoryInsightsEl.appendChild(header);
                        for (const line of insights) {
                            const row = document.createElement('div');
                            row.className = 'history-item';
                            const main = document.createElement('div');
                            main.className = 'history-main';
                            const textEl = document.createElement('div');
                            textEl.className = 'history-task';
                            textEl.textContent = `• ${line}`;
                            main.appendChild(textEl);
                            row.appendChild(main);
                            aiHistoryInsightsEl.appendChild(row);
                        }
                    }

                    if (recs.length) {
                        const header = document.createElement('div');
                        header.className = 'history-task';
                        header.textContent = 'Recommendations';
                        aiHistoryRecsEl.appendChild(header);
                        for (const line of recs) {
                            const row = document.createElement('div');
                            row.className = 'history-item';
                            const main = document.createElement('div');
                            main.className = 'history-main';
                            const textEl = document.createElement('div');
                            textEl.className = 'history-task';
                            textEl.textContent = `• ${line}`;
                            main.appendChild(textEl);
                            row.appendChild(main);
                            aiHistoryRecsEl.appendChild(row);
                        }
                    }
                } catch (err) {
                    console.error('AI history insights failed', err);
                    aiHistoryStatusEl.textContent = 'Could not get AI insights right now.';
                    aiHistoryStatusEl.className = 'status-text error';
                } finally {
                    aiHistoryBtn.disabled = false;
                }
            });
        }

        if (aiNotesBtn && aiNotesStatusEl && aiNotesPatternsEl && aiNotesRecsEl) {
            aiNotesBtn.addEventListener('click', async () => {
                aiNotesStatusEl.textContent =
                    'Asking AI to summarize patterns in your skip/snooze notes…';
                aiNotesStatusEl.className = 'status-text';
                aiNotesPatternsEl.innerHTML = '';
                aiNotesRecsEl.innerHTML = '';
                aiNotesBtn.disabled = true;

                const fromVal = historyFromInput && historyFromInput.value
                    ? historyFromInput.value
                    : '';
                const toVal = historyToInput && historyToInput.value ? historyToInput.value : '';

                const payload = {};
                if (fromVal) payload.start_date = fromVal;
                if (toVal) payload.end_date = toVal;

                try {
                    const res = await fetch('/ai/notes/summary', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload),
                    });
                    if (!res.ok) {
                        const txt = await res.text();
                        throw new Error(txt || 'AI notes summary request failed');
                    }
                    const data = await res.json();
                    const patterns = Array.isArray(data.patterns) ? data.patterns : [];
                    const recs = Array.isArray(data.recommendations)
                        ? data.recommendations
                        : [];

                    lastNotesPatterns = patterns.slice();
                    lastNotesRecs = recs.slice();

                    if (!patterns.length && !recs.length) {
                        aiNotesStatusEl.textContent = 'No summary available for this range.';
                        aiNotesStatusEl.className = 'status-text';
                        return;
                    }

                    aiNotesStatusEl.textContent = '';
                    aiNotesStatusEl.className = 'status-text';

                    if (patterns.length) {
                        const header = document.createElement('div');
                        header.className = 'history-task';
                        header.textContent = 'Patterns in reasons';
                        aiNotesPatternsEl.appendChild(header);
                        for (const line of patterns) {
                            const row = document.createElement('div');
                            row.className = 'history-item';
                            const main = document.createElement('div');
                            main.className = 'history-main';
                            const textEl = document.createElement('div');
                            textEl.className = 'history-task';
                            textEl.textContent = `• ${line}`;
                            main.appendChild(textEl);
                            row.appendChild(main);
                            aiNotesPatternsEl.appendChild(row);
                        }
                    }

                    if (recs.length) {
                        const header = document.createElement('div');
                        header.className = 'history-task';
                        header.textContent = 'Recommendations';
                        aiNotesRecsEl.appendChild(header);
                        for (const line of recs) {
                            const row = document.createElement('div');
                            row.className = 'history-item';
                            const main = document.createElement('div');
                            main.className = 'history-main';
                            const textEl = document.createElement('div');
                            textEl.className = 'history-task';
                            textEl.textContent = `• ${line}`;
                            main.appendChild(textEl);
                            row.appendChild(main);
                            aiNotesRecsEl.appendChild(row);
                        }
                    }
                } catch (err) {
                    console.error('AI notes summary failed', err);
                    aiNotesStatusEl.textContent =
                        'Could not get a skip/snooze notes summary right now.';
                    aiNotesStatusEl.className = 'status-text error';
                } finally {
                    aiNotesBtn.disabled = false;
                }
            });
        }

        if (aiHistoryPlayBtn && aiHistoryStatusEl) {
            aiHistoryPlayBtn.addEventListener('click', async () => {
                if (!lastHistoryInsights.length && !lastHistoryRecs.length) {
                    aiHistoryStatusEl.textContent =
                        'Generate insights (AI) first, then you can listen to them as audio.';
                    aiHistoryStatusEl.className = 'status-text';
                    return;
                }

                const parts = [];
                if (lastHistoryInsights.length) {
                    parts.push('Here are some patterns in your recent alerts.');
                    for (const line of lastHistoryInsights) {
                        parts.push(line);
                    }
                }
                if (lastHistoryRecs.length) {
                    parts.push('Here are some recommendations based on those patterns.');
                    for (const line of lastHistoryRecs) {
                        parts.push(line);
                    }
                }

                const text = parts.join(' ');
                if (!text.trim()) return;

                aiHistoryStatusEl.textContent = 'Preparing audio summary…';
                aiHistoryStatusEl.className = 'status-text';
                aiHistoryPlayBtn.disabled = true;

                try {
                    const res = await fetch('/ai/tts/play', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text }),
                    });
                    if (!res.ok) {
                        const msg = await res.text();
                        throw new Error(msg || 'TTS request failed');
                    }
                    aiHistoryStatusEl.textContent =
                        'Playing summary as audio in the background.';
                    aiHistoryStatusEl.className = 'status-text';
                } catch (err) {
                    console.error('AI history TTS failed', err);
                    aiHistoryStatusEl.textContent =
                        "I couldn't play the summary as audio right now.";
                    aiHistoryStatusEl.className = 'status-text error';
                } finally {
                    aiHistoryPlayBtn.disabled = false;
                }
            });
        }

        if (aiNotesPlayBtn && aiNotesStatusEl) {
            aiNotesPlayBtn.addEventListener('click', async () => {
                if (!lastNotesPatterns.length && !lastNotesRecs.length) {
                    aiNotesStatusEl.textContent =
                        'Generate the notes summary (AI) first, then you can listen to it as audio.';
                    aiNotesStatusEl.className = 'status-text';
                    return;
                }

                const parts = [];
                if (lastNotesPatterns.length) {
                    parts.push('Here are patterns in why you snoozed or skipped tasks.');
                    for (const line of lastNotesPatterns) {
                        parts.push(line);
                    }
                }
                if (lastNotesRecs.length) {
                    parts.push('Here are some adjustments the assistant recommends.');
                    for (const line of lastNotesRecs) {
                        parts.push(line);
                    }
                }

                const text = parts.join(' ');
                if (!text.trim()) return;

                aiNotesStatusEl.textContent = 'Preparing notes summary audio…';
                aiNotesStatusEl.className = 'status-text';
                aiNotesPlayBtn.disabled = true;

                try {
                    const res = await fetch('/ai/tts/play', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text }),
                    });
                    if (!res.ok) {
                        const msg = await res.text();
                        throw new Error(msg || 'TTS request failed');
                    }
                    aiNotesStatusEl.textContent =
                        'Playing notes summary as audio in the background.';
                    aiNotesStatusEl.className = 'status-text';
                } catch (err) {
                    console.error('AI notes TTS failed', err);
                    aiNotesStatusEl.textContent =
                        "I couldn't play the notes summary as audio right now.";
                    aiNotesStatusEl.className = 'status-text error';
                } finally {
                    aiNotesPlayBtn.disabled = false;
                }
            });
        }
};
