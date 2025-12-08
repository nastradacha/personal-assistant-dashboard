# Personal Assistant Dashboard

A small, Pi‑friendly **daily rituals coach**. It runs on a FastAPI backend with a simple HTML+JS frontend and a SQLite database, and is designed to sit on a Raspberry Pi 4 next to you and quietly nudge you through your day.

The app centers on three modes:

- **Today (Now & Next)** – the hero screen. Shows what you should be doing now, what is next, and handles alerts.
- **Planner** – where you design and adjust recurring routines using templates (with optional AI help).
- **Insights** – where you review history, see patterns, and get short AI suggestions (with optional audio playback).

Google Cloud Text‑to‑Speech (TTS) powers spoken alerts and audio summaries when enabled.

---

## Features

- **Today / Now & Next**
  - Daily schedule of tasks (from templates or ad‑hoc entries).
  - Clear "Now" and "Next" blocks with remaining time.
  - One primary AI helper: **"What should I do now?"**
  - Inline micro‑journal prompt after snooze/skip.
  - 3‑stage alert escalation for each task:
    1. Visual overlay (light).
    2. Voice announcement via Google TTS (repeated up to 10× or until you acknowledge).
    3. Beep alarm on the browser as a final escalation.

- **Planner**
  - Templates for recurring tasks, grouped by category.
  - AI helper to:
    - Turn a free‑text routine description into suggested templates.
    - Refine an existing template.
  - Support for `preferred_time_window` like `07:00-11:00` or `1:17 pm - 1:20 pm` that the Today schedule respects when seeding.

- **Insights**
  - Unified history of alerts and interactions.
  - AI history insights (patterns + recommendations).
  - AI summary of skip/snooze notes.
  - Optional **"Play as audio"** for both insights and notes when TTS is configured.

- **TTS integration (Google Cloud)**
  - `/ai/tts/play` endpoint for short coaching text.
  - File‑based audio cache under `tts_cache/` with stable keys and pruning.
  - Environment‑driven config for language, voice, enable/disable, and player command.
  - Repeated spoken alerts on the Today view and audio summaries on the Insights tab.
  - Privacy‑focused: text length is clamped before sending to Google.

---

## Architecture

- **Backend**
  - **FastAPI** app in `backend.main:app`.
  - SQLite database in `assistant.db` (see `backend/db.py`).
  - Routers:
    - `backend/routers/schedule.py` – Today schedule, alerts, interactions, alarm settings.
    - `backend/routers/tasks.py` – CRUD for templates/tasks.
    - `backend/routers/ai.py` – AI helpers, insights, notes summary, and `/ai/tts/play`.
  - Services:
    - `backend/services/schedule.py` – schedule rules and status transitions.
    - `backend/services/interactions.py` – logging interactions and notes.
    - `backend/services/ai.py` – DeepSeek (or other LLM) prompts and parsing.
  - TTS helper:
    - `backend/tts.py` – Google Cloud TTS client, file cache, and audio playback.

- **Frontend**
  - Single HTML shell served from `backend/main.py`.
  - Behavior lives in static JS modules under `backend/static/js/`:
    - `today.js` – Today view, alerts, micro‑journal, Now & Next overlay.
    - `planner.js` – Planner view behaviors.
    - `history.js` – History & Insights rendering.
    - `ai.js` – AI buttons and audio summary playback via TTS.

---

## Getting Started (Local Dev)

### Prerequisites

- Python 3.10+ (tested on 3.11).
- A modern browser.
- Optional but recommended: a virtual environment.

### 1. Clone and install

```bash
git clone https://github.com/your-user/personal-assistant-dashboard.git
cd personal-assistant-dashboard

python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file (or set environment variables another way) in the project root.

Minimal setup without TTS:

```env
# Disable TTS entirely (optional)
TTS_ENABLED=false
```

To enable Google Cloud TTS on a Pi or local machine:

```env
# Path to your Google Cloud service account JSON key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account.json

# Turn TTS on/off
TTS_ENABLED=true

# Language and voice (Standard voice to stay in the free tier)
TTS_LANGUAGE=en-US
TTS_VOICE=en-US-Standard-C

# Local audio player command (Pi):
# Simple default
TTS_PLAYER_COMMAND=aplay
# Or, with a specific ALSA device
# TTS_PLAYER_COMMAND=aplay -D hw:1,0

# File-based cache
TTS_CACHE_DIR=tts_cache
TTS_CACHE_MAX_FILES=500

# TTS safety / hygiene
TTS_MAX_TEXT_CHARS=1000
TTS_TIMEOUT_SECONDS=10.0
```

> Note: how `.env` is loaded depends on how you run the app. When using `uvicorn`, you can pass `--env-file .env`, or you can export the variables in your shell.

### 3. Run the server

From the project root:

```bash
uvicorn backend.main:app --reload --env-file .env
```

Then open:

- `http://localhost:8000` – main dashboard.
- `http://localhost:8000/docs` – FastAPI docs (health, schedule, AI, TTS endpoints).

---

## Running on a Raspberry Pi 4

The app is designed to run on a Pi 4 as a small dedicated dashboard.

Basic outline:

1. Install Python and system audio tools (`aplay` / ALSA).
2. Clone the repo and create a virtualenv as above.
3. Install `requirements.txt`.
4. Place your Google service account JSON somewhere like `/home/pi/keys/tts-service-account.json`.
5. Create a `.env` with the TTS settings pointing at that JSON and your audio device.
6. Run `uvicorn` with `--env-file .env` or configure a systemd service that exports the env vars.
7. Pin a browser (kiosk mode) to `http://<pi-host>:8000`.

---

## Data & Persistence

- All app data (tasks, schedule instances, notes, interactions) is stored in `assistant.db` in the project root.
- `assistant.db` is **ignored by Git** (`.gitignore`), so local schedules and notes are not accidentally committed.
- You can back up or reset the app by copying or deleting this SQLite file.

---

## TTS Setup and Design Docs

- **TTS stories & implementation notes:** `tts_setup_stories.md`.
  - Documents user stories TTS‑001 through TTS‑006 (basic playback, caching, config, graceful failure handling, Pi resource limits, privacy).
- **Product / refactor V2 plan:** `USER_STORIES_V2_REFACTOR.md`.
  - Describes the Today/Planner/Insights modes, backend services split, and JS modularization.

These documents are the authoritative source for the product and TTS design; the README is a quick on‑ramp.

---

## Key Behaviors (Quick Reference)

- **Today schedule seeding**
  - Tasks with a `preferred_time_window` (e.g., `07:00-11:00` or `1:17 pm - 1:20 pm`) are placed inside that window when possible.
  - Tasks without a usable window are scheduled sequentially starting from 09:00.

- **Alert escalation**
  - When a task becomes active:
    1. A visual overlay appears.
    2. A spoken announcement is sent to `/ai/tts/play` and repeated up to 10 times (if TTS is enabled).
    3. If still unacknowledged after ~60 seconds, a continuous beep alarm starts in the browser.

- **Editing Today times**
  - The Today view polls `/schedule/today` once per second.
  - While you are editing a task start time, auto‑refresh pauses so the time input does not flicker.

---

## Contributing / Next Ideas

This project is intentionally small and opinionated. Some future directions:

- TTS Phase 4 niceties:
  - Pre‑generate audio for upcoming tasks.
  - In‑app note mentioning that audio is powered by Google Cloud TTS.
- A small "Regenerate today" control for testing template changes without touching the DB.
- More granular alarm sounds or chimes.

For changes, prefer incremental, behavior‑preserving refactors as outlined in `USER_STORIES_V2_REFACTOR.md`.
