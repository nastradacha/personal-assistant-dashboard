window.initPlannerView = function initPlannerView() {
        const form = document.getElementById('task-form');
        const statusEl = document.getElementById('status');
        const tasksListEl = document.getElementById('tasks-list');
        const templateSearchInput = document.getElementById('template-search');
        const aiTemplateFreeText = document.getElementById('ai-template-free-text');
        const aiTemplateSuggestBtn = document.getElementById('ai-template-suggest-btn');
        const aiTemplateStatus = document.getElementById('ai-template-status');
        const submitBtn = document.getElementById('submit-btn');
        const alertWordingCategorySelect = document.getElementById('alert-wording-category');
        const alertWordingToneInput = document.getElementById('alert-wording-tone');
        const alertWordingMaxLengthInput = document.getElementById('alert-wording-max-length');
        const alertWordingCountInput = document.getElementById('alert-wording-count');
        const aiAlertWordingBtn = document.getElementById('ai-alert-wording-btn');
        const aiAlertWordingStatusEl = document.getElementById('ai-alert-wording-status');
        const alertWordingCurrentEl = document.getElementById('alert-wording-current');
        const aiAlertWordingOptionsEl = document.getElementById('ai-alert-wording-options');

        let editingTaskId = null;
        let templateTasksAll = [];

        if (aiTemplateSuggestBtn && aiTemplateFreeText && aiTemplateStatus) {
            aiTemplateSuggestBtn.addEventListener('click', async () => {
                const text = (aiTemplateFreeText.value || '').trim();
                if (!text) {
                    aiTemplateStatus.textContent = 'Describe your routine in 1–3 sentences before asking the assistant.';
                    aiTemplateStatus.className = 'status-text error';
                    return;
                }
                aiTemplateStatus.textContent = 'Designing routine templates with AI…';
                aiTemplateStatus.className = 'status-text';
                aiTemplateSuggestBtn.disabled = true;
                try {
                    const res = await fetch('/ai/templates/suggestions', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ free_text: text }),
                    });
                    if (!res.ok) {
                        const txt = await res.text();
                        throw new Error(txt || 'AI request failed');
                    }
                    const data = await res.json();
                    const templates = Array.isArray(data.templates) ? data.templates : [];
                    if (!templates.length) {
                        aiTemplateStatus.textContent = 'The assistant did not return any usable templates.';
                        aiTemplateStatus.className = 'status-text error';
                        return;
                    }
                    const first = templates[0];
                    document.getElementById('name').value = first.name || '';
                    document.getElementById('category').value = first.category || '';
                    if (typeof first.default_duration_minutes === 'number') {
                        document.getElementById('default_duration_minutes').value = String(first.default_duration_minutes);
                    }
                    document.getElementById('recurrence_pattern').value = first.recurrence_pattern || '';
                    document.getElementById('preferred_time_window').value = first.preferred_time_window || '';
                    document.getElementById('default_alert_style').value = first.default_alert_style || 'visual_then_alarm';
                    document.getElementById('enabled').checked = first.enabled !== false;
                    editingTaskId = null;
                    submitBtn.textContent = 'Save template';
                    statusEl.textContent = 'AI suggestion loaded into the form. Review and save when it looks right.';
                    statusEl.className = 'status-text ok';
                    aiTemplateStatus.textContent = `Loaded 1 of ${templates.length} AI-suggested templates into the form.`;
                    aiTemplateStatus.className = 'status-text ok';
                } catch (err) {
                    console.error('AI template suggestions failed', err);
                    aiTemplateStatus.textContent = 'Could not design routine templates with AI right now.';
                    aiTemplateStatus.className = 'status-text error';
                } finally {
                    aiTemplateSuggestBtn.disabled = false;
                }
            });
        }

        if (templateSearchInput) {
            templateSearchInput.addEventListener('input', () => {
                applyTemplateFilterAndRender();
            });
        }

        async function loadTasks() {
            try {
                const res = await fetch('/tasks/');
                if (!res.ok) throw new Error('Failed to load tasks');
                const data = await res.json();
                templateTasksAll = Array.isArray(data) ? data : [];
                applyTemplateFilterAndRender();
                updateAlertWordingCategoryOptions();
            } catch (err) {
                console.error(err);
                if (tasksListEl) {
                    tasksListEl.innerHTML = '<div class="hint">Could not load templates. Check that the backend is running.</div>';
                }
            }
        }

        function applyTemplateFilterAndRender() {
            if (!tasksListEl) return;
            const all = Array.isArray(templateTasksAll) ? templateTasksAll : [];
            let tasks = all.slice();
            const q = templateSearchInput && templateSearchInput.value
                ? templateSearchInput.value.toLowerCase().trim()
                : '';
            if (q) {
                tasks = tasks.filter((t) => {
                    const name = (t.name || '').toLowerCase();
                    const cat = (t.category || '').toLowerCase();
                    return name.includes(q) || cat.includes(q);
                });
            }
            renderTasks(tasks);
        }

        function renderTasks(tasks) {
            if (!tasksListEl) return;
            tasksListEl.innerHTML = '';
            const all = Array.isArray(templateTasksAll) ? templateTasksAll : [];
            if (!all.length) {
                tasksListEl.innerHTML = '<div class="hint">No templates yet. Use the form on the left to create your first one.</div>';
                return;
            }
            if (!tasks.length) {
                tasksListEl.innerHTML = '<div class="hint">No templates match your search.</div>';
                return;
            }

            const groups = new Map();
            for (const t of tasks) {
                const rawCat = (t.category || '').trim();
                const catKey = rawCat || 'Uncategorized';
                if (!groups.has(catKey)) {
                    groups.set(catKey, []);
                }
                groups.get(catKey).push(t);
            }
            const sortedCats = Array.from(groups.keys()).sort((a, b) =>
                a.toLowerCase().localeCompare(b.toLowerCase()),
            );

            for (const catName of sortedCats) {
                const catTasks = groups.get(catName) || [];
                const groupEl = document.createElement('div');
                groupEl.className = 'task-group';

                const headerEl = document.createElement('button');
                headerEl.type = 'button';
                headerEl.className = 'task-group-header';

                const titleWrap = document.createElement('div');
                titleWrap.className = 'task-group-title-wrap';

                const caretEl = document.createElement('span');
                caretEl.className = 'task-group-caret';
                caretEl.textContent = '▾';

                const titleEl = document.createElement('span');
                titleEl.className = 'task-group-title';
                titleEl.textContent = catName;

                titleWrap.appendChild(caretEl);
                titleWrap.appendChild(titleEl);

                const countEl = document.createElement('span');
                countEl.className = 'task-group-count';
                const count = catTasks.length;
                countEl.textContent = `${count} template${count === 1 ? '' : 's'}`;

                headerEl.appendChild(titleWrap);
                headerEl.appendChild(countEl);

                const bodyEl = document.createElement('div');
                bodyEl.className = 'task-group-body';

                headerEl.addEventListener('click', () => {
                    groupEl.classList.toggle('collapsed');
                });

                groupEl.appendChild(headerEl);
                groupEl.appendChild(bodyEl);
                tasksListEl.appendChild(groupEl);

                for (const t of catTasks) {
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
                        const durVal =
                            typeof t.default_duration_minutes === 'number'
                                ? t.default_duration_minutes
                                : '';
                        document.getElementById('default_duration_minutes').value = String(durVal);
                        document.getElementById('recurrence_pattern').value = t.recurrence_pattern || '';
                        document.getElementById('preferred_time_window').value =
                            t.preferred_time_window || '';
                        document.getElementById('default_alert_style').value = t.default_alert_style || 'visual_then_alarm';
                        document.getElementById('enabled').checked = !!t.enabled;
                        submitBtn.textContent = 'Update template';
                        statusEl.textContent = 'Editing existing template…';
                        statusEl.className = 'status-text';
                    });

                    const refineBtn = document.createElement('button');
                    refineBtn.type = 'button';
                    refineBtn.className = 'action-btn edit';
                    refineBtn.textContent = 'Refine with AI';
                    refineBtn.addEventListener('click', async () => {
                        const instruction = window.prompt(
                            'Optional: tell the assistant how to adjust this template (e.g. "shorten evening routine", "move to mornings", "gentler tone").',
                            '',
                        );
                        statusEl.textContent = 'Refining this template with AI…';
                        statusEl.className = 'status-text';
                        refineBtn.disabled = true;
                        try {
                            const payload = {
                                template: {
                                    name: t.name,
                                    category: t.category,
                                    default_duration_minutes: t.default_duration_minutes,
                                    recurrence_pattern: t.recurrence_pattern,
                                    preferred_time_window: t.preferred_time_window,
                                    default_alert_style: t.default_alert_style,
                                    enabled: t.enabled,
                                },
                                instruction: instruction || null,
                            };
                            const res = await fetch('/ai/templates/refine', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify(payload),
                            });
                            if (!res.ok) {
                                const txt = await res.text();
                                throw new Error(txt || 'AI refine request failed');
                            }
                            const data = await res.json();
                            const refined = data && data.template ? data.template : null;
                            if (!refined) {
                                throw new Error('AI did not return a refined template');
                            }
                            document.getElementById('name').value = refined.name || '';
                            document.getElementById('category').value = refined.category || '';
                            if (typeof refined.default_duration_minutes === 'number') {
                                document.getElementById('default_duration_minutes').value = String(
                                    refined.default_duration_minutes,
                                );
                            }
                            document.getElementById('recurrence_pattern').value = refined.recurrence_pattern || '';
                            document.getElementById('preferred_time_window').value =
                                refined.preferred_time_window || '';
                            document.getElementById('default_alert_style').value =
                                refined.default_alert_style || 'visual_then_alarm';
                            document.getElementById('enabled').checked = refined.enabled !== false;
                            editingTaskId = t.id;
                            submitBtn.textContent = 'Update template';
                            statusEl.textContent = 'AI refinement loaded. Review and update/save when ready.';
                            statusEl.className = 'status-text ok';
                        } catch (err) {
                            console.error('AI template refine failed', err);
                            statusEl.textContent = 'Could not refine template with AI.';
                            statusEl.className = 'status-text error';
                        } finally {
                            refineBtn.disabled = false;
                        }
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
                    actions.appendChild(refineBtn);
                    actions.appendChild(deleteBtn);

                    item.appendChild(header);
                    item.appendChild(badges);
                    item.appendChild(actions);
                    bodyEl.appendChild(item);
                }
            }
        }

        function updateAlertWordingCategoryOptions() {
            if (!alertWordingCategorySelect) return;
            const seen = new Set();
            for (const t of templateTasksAll) {
                const cat = (t.category || '').trim();
                if (!cat) continue;
                seen.add(cat);
            }
            const sorted = Array.from(seen).sort((a, b) => a.localeCompare(b));
            alertWordingCategorySelect.innerHTML = '<option value="">Select category</option>';
            for (const cat of sorted) {
                const opt = document.createElement('option');
                opt.value = cat;
                opt.textContent = cat;
                alertWordingCategorySelect.appendChild(opt);
            }
        }

        async function loadAlertWordingForCategory(category) {
            if (!alertWordingCurrentEl) return;
            if (!category) {
                alertWordingCurrentEl.textContent = '';
                alertWordingCurrentEl.className = 'status-text';
                return;
            }
            try {
                const res = await fetch(`/schedule/alert-wordings/${encodeURIComponent(category)}`);
                if (!res.ok) {
                    alertWordingCurrentEl.textContent = '';
                    alertWordingCurrentEl.className = 'status-text';
                    return;
                }
                const data = await res.json();
                const text = (data && data.text ? String(data.text) : '').trim();
                const tone = (data && data.tone ? String(data.tone) : '').trim();
                if (text) {
                    alertWordingCurrentEl.textContent = tone
                        ? `Current wording (${tone}): ${text}`
                        : `Current wording: ${text}`;
                    alertWordingCurrentEl.className = 'status-text ok';
                } else {
                    alertWordingCurrentEl.textContent = '';
                    alertWordingCurrentEl.className = 'status-text';
                }
            } catch (err) {
                console.error('Failed to load alert wording config', err);
                alertWordingCurrentEl.textContent = '';
                alertWordingCurrentEl.className = 'status-text';
            }
        }

        if (alertWordingCategorySelect) {
            alertWordingCategorySelect.addEventListener('change', async () => {
                const cat = alertWordingCategorySelect.value || '';
                await loadAlertWordingForCategory(cat);
            });
        }

        if (aiAlertWordingBtn && aiAlertWordingStatusEl && aiAlertWordingOptionsEl) {
            aiAlertWordingBtn.addEventListener('click', async () => {
                const category = alertWordingCategorySelect ? alertWordingCategorySelect.value : '';
                const tone = alertWordingToneInput ? alertWordingToneInput.value : '';
                const maxLenStr = alertWordingMaxLengthInput
                    ? alertWordingMaxLengthInput.value
                    : '120';
                const countStr = alertWordingCountInput ? alertWordingCountInput.value : '5';

                if (!category) {
                    aiAlertWordingStatusEl.textContent =
                        'Please select a category before asking the AI for alert texts.';
                    aiAlertWordingStatusEl.className = 'status-text error';
                    return;
                }
                if (!tone || !tone.trim()) {
                    aiAlertWordingStatusEl.textContent =
                        'Please describe the tone you want (e.g. neutral/firm, encouraging, protective).';
                    aiAlertWordingStatusEl.className = 'status-text error';
                    return;
                }

                let maxLength = parseInt(maxLenStr || '120', 10);
                if (!Number.isFinite(maxLength)) maxLength = 120;
                let count = parseInt(countStr || '5', 10);
                if (!Number.isFinite(count)) count = 5;

                aiAlertWordingStatusEl.textContent = 'Asking AI for alert wording options…';
                aiAlertWordingStatusEl.className = 'status-text';
                aiAlertWordingOptionsEl.innerHTML = '';
                aiAlertWordingBtn.disabled = true;

                const payload = {
                    category,
                    tone: tone.trim(),
                    max_length: maxLength,
                    count,
                };

                try {
                    const res = await fetch('/ai/alerts/wording', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload),
                    });
                    if (!res.ok) {
                        const txt = await res.text();
                        throw new Error(txt || 'AI alert wording request failed');
                    }
                    const data = await res.json();
                    const options = Array.isArray(data.options) ? data.options : [];
                    if (!options.length) {
                        aiAlertWordingStatusEl.textContent =
                            'AI did not return any usable alert texts.';
                        aiAlertWordingStatusEl.className = 'status-text error';
                        return;
                    }

                    aiAlertWordingStatusEl.textContent =
                        'Click an option below to save it as the alert wording for this category.';
                    aiAlertWordingStatusEl.className = 'status-text ok';

                    for (const text of options) {
                        const row = document.createElement('div');
                        row.className = 'history-item';
                        const main = document.createElement('div');
                        main.className = 'history-main';
                        const textEl = document.createElement('div');
                        textEl.className = 'history-task';
                        textEl.textContent = text;
                        main.appendChild(textEl);
                        row.appendChild(main);

                        row.style.cursor = 'pointer';
                        row.addEventListener('click', async () => {
                            try {
                                const payloadSave = {
                                    tone: tone.trim(),
                                    text,
                                };
                                const resSave = await fetch(
                                    `/schedule/alert-wordings/${encodeURIComponent(category)}`,
                                    {
                                        method: 'PUT',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify(payloadSave),
                                    },
                                );
                                if (!resSave.ok) {
                                    const txt = await resSave.text();
                                    throw new Error(txt || 'Failed to save alert wording');
                                }
                                aiAlertWordingStatusEl.textContent = 'Alert wording saved for this category.';
                                aiAlertWordingStatusEl.className = 'status-text ok';
                                await loadAlertWordingForCategory(category);
                            } catch (err) {
                                console.error('Failed to save alert wording', err);
                                aiAlertWordingStatusEl.textContent =
                                    'Error saving alert wording. See console for details.';
                                aiAlertWordingStatusEl.className = 'status-text error';
                            }
                        });

                        aiAlertWordingOptionsEl.appendChild(row);
                    }
                } catch (err) {
                    console.error('AI alert wording request failed', err);
                    aiAlertWordingStatusEl.textContent = 'Could not get alert wording suggestions right now.';
                    aiAlertWordingStatusEl.className = 'status-text error';
                } finally {
                    aiAlertWordingBtn.disabled = false;
                }
            });
        }

        if (form && submitBtn) {
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
        }

        loadTasks();
    };
