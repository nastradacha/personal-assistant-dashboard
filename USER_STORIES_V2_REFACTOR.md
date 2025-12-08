# Refactor & Product V2 User Stories

## Product V2: What This Is

**Charter**  
A daily rituals coach that lives on the Pi, shows a calm "Now & Next" view, nudges you with smart alerts, and once in a while gives you a short, helpful reflection.

**Status (Dec 2025):** Core refactor stories (R1–R5), the Today micro-journal and AI polish stories (P1–P3), and TTS-001–TTS-006 are implemented in code. This document now serves as the product/architecture reference and backlog for future tweaks.

From this, we anchor on three core modes. Everything else should support these.

### Mode 1: Today (Now & Next) – Hero Screen

- **Goal**: I always know what I should be doing right now and what happens if I press a button.
- **Core elements**:
  - **Now**: current task name, time window, remaining time.
  - **Next**: upcoming task name + time window.
  - **Actions**: acknowledge, snooze (+5/+10/+15), skip for today (disable today), pause.
  - **Micro‑journal prompt**: light, low‑friction way to capture why I snoozed/skipped.
  - **AI coaching**: one clear entry point, "What should I do now?", with an optional "Play aloud" when TTS is available.

### Mode 2: Planner

- **Goal**: I can design and adjust my recurring day using a few clear tools.
- **Core elements**:
  - **Templates and recurring routines** grouped by category.
  - A **single, excellent AI helper** for designing/refining routines:
    - From free‑text routine description → suggested templates.
    - From selected template → refined version.
  - Avoid scattered AI entry points; focus on two high‑value flows:
    - "Design my routine" (text → multiple templates).
    - "Refine selected template" (one template → one refined template).

### Mode 3: Insights

- **Goal**: I periodically understand patterns in my behavior and get 1–2 concrete suggestions.
- **Core elements**:
  - Unified **history list** (alerts and interactions).
  - A simple **weekly summary** (or date‑range‑based summary).
  - 1–2 **AI analyses** per range:
    - Patterns in behavior.
    - Suggestions/adjustments.
  - Optional: **"Play this as audio"** when TTS is configured.

---

## Architecture V2: Cleaner Shape (Same Stack)

We keep FastAPI + SQLite + server‑rendered HTML, but introduce clearer layers and modules.

### Backend Layers

- **Data & Schemas (existing)**
  - `models.py` / `schemas.py`
  - Responsibility: data tables and Pydantic models only.

- **Services (new modules)**
  - `services.schedule`
    - Today schedule generation.
    - Status transitions: active/paused/disabled.
    - Snooze/disable/skip and any "re‑alert" logic.
  - `services.interactions`
    - Log interactions (ack, snooze, skip, etc.).
    - Attach and retrieve micro‑journal notes.
    - Provide summarized views of interactions for AI.
  - `services.ai`
    - Thin wrappers around DeepSeek (or other LLM) calls.
    - Each function returns Python data structures, not raw JSON strings.
    - Example functions:
      - `generate_template_suggestions(free_text: str) -> List[TemplateSuggestion]`
      - `refine_template(template, instruction) -> RefinedTemplate`
      - `summarize_history(payload) -> HistorySummary`
      - `summarize_notes(payload) -> NotesSummary`

- **Routers (thinner)**
  - `routers/schedule.py`
    - Map HTTP → service calls.
    - Validate input, call `services.schedule`, serialize output.
  - `routers/ai.py`
    - Compose:
      - Gather data from `services.schedule` / `services.interactions`.
      - Call `services.ai` functions.
    - Minimal prompt logic in routers; prompts live in `services.ai`.

This separation makes it easier to evolve AI prompts, schedule rules, or logging behavior without touching a lot of HTTP glue.

### Frontend Shape

- **HTML shell** remains inline/server‑rendered, but behavior moves to static JS files:
  - `static/js/today.js`
  - `static/js/planner.js`
  - `static/js/history.js`
  - `static/js/ai.js`
  - `static/js/audio.js` (later, for TTS and audio controls)

- **Tiny API client module** (e.g., in `static/js/api.js`):

  ```js
  const api = {
      getToday: () => fetchJson('/schedule/today'),
      snooze: (id, body) => fetchJson(`/schedule/instances/${id}/snooze`, { method: 'POST', body }),
      // etc.
  };
  ```

- **View modules**:
  - Each view file owns:
    - DOM queries for its section.
    - Event wiring for its buttons.
    - Usage of the `api` client, not raw `fetch` scattered everywhere.
  - Each exposes a single `init*View()` entry point:
    - `initTodayView()`
    - `initPlannerView()`
    - `initHistoryView()`
    - `initAIHelpers()` / `initAudio()` as needed.

No front‑end framework is required; this is purely structuring existing behavior.

---

## UI V2: Screens & Flows

### A. Today (Default Tab)

**User story**:  
_As a user, when I look at the Today tab, I want a calm Now & Next view and clear buttons so I understand what happens when I act._

- **Layout**
  - **Top strip**:
    - `Now: <task name> · HH:MM–HH:MM · remaining time`.
    - If no task: "No active task – choose something from Planner or rest.".
  - **Now & Next panel**:
    - Now block: name, time range, countdown.
    - Next block: name + time window.

- **Buttons / actions**
  - Acknowledge (or implied via dismiss).
  - Snooze (+5 / +10 / +15).
  - Skip for today (mapped to current "Disable today").
  - Pause/resume if relevant.

- **Micro‑journal prompt**
  - As in PA‑035, but V2 goal is to move from blocking `window.prompt` to:
    - A small inline text field or a light modal.
    - Less jarring, more on‑brand with the calm dashboard.

- **AI on this screen**
  - One clear button:
    - "What should I do now?" → existing PA‑032 result.
  - Optional: "Play aloud" when TTS is configured.

### B. Planner Tab

**User story**:  
_As a user, I want to design and refine my recurring routines in one clear Planner view with focused AI help._

- **Sections**
  - Template list, grouped by category (as now).
  - Template editor form for the selected template.

- **AI block**
  - Free‑text routine → AI suggestions for multiple templates.
  - "Refine this template" for the selected template.
  - Remove or hide extra AI entry points; keep just:
    - "Design my routine" (text → multiple templates).
    - "Refine selected template" (one template → one refined template).

### C. Insights Tab

**User story**:  
_As a user, I want a single Insights page where I can review history, see patterns, and get short suggestions._

- **Layout**: one page, three stacked cards
  1. History list (existing behavior, with unified date filters).
  2. AI history insights (PA‑033).
  3. Skip/snooze notes summary (PA‑035).

- **V2 refinements**
  - Unified date range controls at the top of the Insights page.
  - Each AI card:
    - Returns "Explain this in 3 bullets" style output.
    - Offers a "Play as audio" option when TTS is available (PA‑040+).

---

## Refactor User Stories (V2 Backlog)

### Story R1: Modularize Frontend JavaScript (No Behavior Change)

**As a** developer/future maintainer  
**I want** the dashboard JavaScript split into small modules  
**so that** I can safely change behavior without touching an enormous `<script>` block.

**Acceptance criteria**
- The existing inline `<script>` in `backend/main.py` is moved to `static/js/main.js` with no behavior changes.
- The HTML references `static/js/main.js` instead of embedding the whole script.
- App behavior (Today, Planner, Insights, AI actions) is unchanged.

**Follow‑up subtasks**
- R1.1: Extract Today‑related functions into `static/js/today.js` and call `initTodayView()` from main.
- R1.2: Extract Planner‑related behavior into `static/js/planner.js` with `initPlannerView()`.
- R1.3: Extract History/Insights and AI helpers into `static/js/history.js` and `static/js/ai.js`.
- R1.4: (Later) Create `static/js/audio.js` for TTS interactions.

### Story R2: Introduce `services.ai` for LLM Logic

**As a** developer  
**I want** AI prompts and parsing logic moved into a dedicated `services.ai` module  
**so that** routers stay thin and I can iterate on prompts independently.

**Acceptance criteria**
- A new `services/ai.py` (or equivalent package) exists with functions like:
  - `generate_template_suggestions(free_text)`
  - `refine_template(template, instruction)`
  - `summarize_history(summary_dict)`
  - `summarize_notes(notes_summary_dict)`
- `routers/ai.py` calls these functions instead of embedding prompt text and parsing directly.
- Behavior of existing endpoints remains the same (same response shape and error handling).

### Story R3: Normalize Interaction and Note Handling

**As a** developer  
**I want** a single, consistent way to log interactions and attach notes  
**so that** analytics and AI summaries are reliable.

**Acceptance criteria**
- A helper in `services.interactions` (or equivalent) handles:
  - Logging snooze/disable/ack events.
  - Attaching micro‑journal notes to the correct schedule instance and latest interaction.
- `routers/schedule.py` uses this helper for all interaction events.
- When I perform snooze/disable/ack via the UI, the resulting DB records are predictable and consistent.

### Story R4: Tighten Today Behavior & State Transitions

**As a** user  
**I want** consistent behavior when tasks move between active/paused/disabled  
**so that** the Now & Next view always makes sense.

**Acceptance criteria**
- A documented set of rules for:
  - When an instance becomes active vs paused vs disabled.
  - When overlays (alerts) appear and disappear.
  - How snooze affects remaining time and future alerts.
- Implementation is encapsulated in `services.schedule`:
  - Status changes go through named functions (e.g. `snooze_instance`, `disable_for_today`, etc.).
- A small set of tests or manual scripts confirm expected transitions in a few scenarios (on‑time, snoozed, skipped).

### Story R5: Insights V2 – Unified Page

**As a** user  
**I want** one Insights tab with clear cards and date range controls  
**so that** I can quickly review the past and get a short reflection.

**Acceptance criteria**
- The Insights tab shows:
  - Unified date range filter inputs at the top.
  - Three cards stacked: History, AI History Insights, Skip/Snooze Notes Summary.
- AI cards:
  - Produce 3‑bullet summaries as they do now (or better structured).
  - Expose a "Play as audio" button when TTS is configured.

---

## Implementation Notes / Vision

- Refactors should be incremental and non‑breaking:
  - First move code (JS and Python) with behavior parity.
  - Then gradually improve prompts, UI polish, and state rules.
- The Pi‑hosted nature of the app remains central:
  - Local‑first, responsive on a small display.
  - Audio nudges should be short and infrequent, matching the "once in a while" reflection idea.
- The long‑term goal is that a future you can:
  - Open `services/ai` to tweak how coaching sounds.
  - Open `services.schedule` to change how strict or gentle the scheduler is.
  - Adjust JS modules independently without fear of breaking unrelated features.
