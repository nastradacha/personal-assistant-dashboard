# TTS Setup – Google Cloud Text-to-Speech

This document captures user stories and implementation notes for wiring the dashboard to **Google Cloud Text-to-Speech (TTS)** with lightweight caching, optimized for a Raspberry Pi 4 host.

**Status (Dec 2025):** TTS-001 through TTS-006 are implemented in the app; this document remains the design and reference for how TTS is wired and configured.

Assumptions:
- Backend is FastAPI (`/ai/tts/play` endpoint already exists).
- Host environment is a Raspberry Pi 4 (low CPU, limited SD card writes).
- Google Cloud project and TTS API can be enabled by the operator.

---

## TTS-001 – Hear my tasks and summaries via Google TTS

**User story**  
_As a user, when I tap a "Play" or "Listen" button in the app, I want the assistant to read out a short, friendly sentence about my task or summary using Google Cloud Text-to-Speech, so I can follow along without staring at the screen._

**Where in the UI**
- Today tab:
  - Future: optional "Play aloud" for the current task (not yet implemented).
- History & Insights tab:
  - "Listen to summary (audio)" for AI Insights.
  - "Listen to notes summary (audio)" for Skip/Snooze Notes.

**Alert escalation model (Today alerts)**
- Stage 1 – Light only:
  - Show the existing flickering alert overlay with task name and time window.
- Stage 2 – Light + voice:
  - Shortly after the overlay appears, play a short spoken announcement of the task and window via Google TTS.
- Stage 3 – Light + voice + beep (last resort):
  - Only if the alert remains unacknowledged after a longer delay, start the existing beeping alarm as a final escalation.

**Acceptance criteria**
- **AC1 – Basic playback**
  - When the frontend calls `/ai/tts/play` with `{ text: "..." }`, the backend uses **Google Cloud TTS** to synthesize speech and plays it on the Pi (or returns a short success response once playback has started).
- **AC2 – Reasonable latency**
  - For short texts (1–4 sentences), the time from button press to audible playback is **< 2–3 seconds** in typical conditions.
- **AC3 – Voice configuration**
  - The assistant uses a **Standard** voice by default (to stay within the generous free tier).
  - Language and voice (e.g., `en-US`, `en-GB`) can be changed via configuration without a code change.
- **AC4 – No UI changes required**
  - Frontend contract is unchanged: still calls `POST /ai/tts/play` with `{ text }` and expects a simple success/failure.
- **AC5 – Escalation ordering respected (Today tab)**
  - For Today alerts, implementation follows the 3-step ladder:
    1. Flickering overlay (light).
    2. Spoken announcement via Google TTS.
    3. Beeping alarm only if there is still no user response after the configured delay.

**Implementation notes**
- Use the official Google Cloud TTS client or simple REST calls from the backend.
- Prefer a **synchronous call** for now (no job queue), but keep the code structured so a future async/queued path is possible.
- Use **Standard voices** by default (4M free characters/month).

---

## TTS-002 – Cache repeated phrases to avoid re-hitting the API

**User story**  
_As a user with recurring tasks, I want the app to reuse audio for repeated phrases (e.g., the same task announcement or the same summary blob) so playback feels fast and we dont waste TTS calls on the same text over and over._

**Acceptance criteria**
- **AC1 – Stable cache key**
  - For each TTS request, the backend computes a **cache key** based on:
    - The text being read.
    - The language code.
    - The voice name.
- **AC2 – File-based cache**
  - If an audio file for that key exists (e.g., under `tts_cache/`), the backend **uses the cached file** instead of calling Google TTS again.
- **AC3 – Transparent to the frontend**
  - The frontend doesnt need to know if audio came from cache or live synthesis.
  - The response contract of `/ai/tts/play` stays the same.
- **AC4 – Reasonable storage footprint**
  - Cache files are small compressed audio (e.g., MP3 or OGG).
  - There is a simple limit to avoid unbounded growth (e.g., max number of files or periodic pruning of old ones).

**Implementation notes**
- Store audio under a dedicated directory such as `tts_cache/` at the project root (configurable via env var).
- Use a **hash-based filename** (e.g., SHA-256 or SHA-1) to avoid filesystem issues and keep paths deterministic.
- Optionally, store a tiny metadata file (JSON) alongside audio files with the original text and voice for debugging.

---

## TTS-003 – Operator-friendly configuration and secrets

**User story**  
_As the person running this dashboard on my Pi, I want to configure Google Cloud TTS credentials, language, voice, and whether TTS is enabled at all using a simple `.env` file or environment variables, without hard-coding secrets in the repo._

**Acceptance criteria**
- **AC1 – Credentials via environment**
  - Google Cloud credentials are **not checked into Git**.
  - The backend reads credentials via environment variables or a config path (e.g., `GOOGLE_APPLICATION_CREDENTIALS` or a JSON key path referenced from `.env`).
- **AC2 – Toggle TTS on/off**
  - A config flag (e.g., `TTS_ENABLED=true/false`) controls whether `/ai/tts/play` actually calls Google TTS.
  - If disabled, the endpoint responds with a friendly message and does **not** attempt synthesis.
- **AC3 – Voice and language config**
  - Language code (e.g., `TTS_LANGUAGE=en-US`) and voice name (e.g., `TTS_VOICE=en-US-Standard-C`) are configurable via env.
- **AC4 – Safe defaults**
  - Default config uses **Standard** voice and a common English locale (to match the free tier and existing UI copy).

**Implementation notes**
- Use a small config module or utilities (e.g., `settings.py` / environment parsing) to centralize TTS options.
- Ensure local development can run with TTS disabled, but still exercise the endpoint (it might just log or no-op).

---

## TTS-004 – Graceful failure handling and fallbacks

**User story**  
_As a user, if TTS fails (network issues, quota limits, config problems), I want a clear but non-intrusive error, and I want the rest of the dashboard to continue working normally._

**Acceptance criteria**
- **AC1 – Non-blocking failure**
  - If Google TTS returns an error or times out, `/ai/tts/play` responds with a 4xx/5xx code and a short human-readable message.
  - The UI shows a small status message near the button but does not block other interactions.
- **AC2 – Logging but no secret leakage**
  - Errors are logged on the backend, but logs do **not** include full credentials.
  - Logging may include: truncated text, error codes, and whether the call came from cache or live synthesis.
- **AC3 – No crash on misconfiguration**
  - If credentials or env vars are missing, the app starts with TTS effectively disabled but the rest of the dashboard is intact.

**Implementation notes**
- Wrap Google TTS calls in a small helper in `backend/tts.py` that:
  - Handles timeouts.
  - Translates API errors into clean HTTPException messages.
- The frontend already has lightweight status messaging around the TTS buttons; reuse that pattern.

---

## TTS-005 – Respect Raspberry Pi 4 resource limits

**User story**  
_As the operator running this on a Raspberry Pi 4, I want TTS to add minimal overhead so that alerts, Today/Planner interactions, and AI calls remain responsive even when I occasionally play audio._

**Acceptance criteria**
- **AC1 – No local neural models**
  - All speech synthesis work is done by **Google Cloud TTS**, not by a heavy local model.
- **AC2 – Bounded CPU usage on the Pi**
  - The Pi does only lightweight work for TTS (HTTP I/O, file cache checks, simple streaming), not heavy DSP.
- **AC3 – Disk usage under control**
  - TTS cache is capped or pruned so it does not exhaust the SD card.
- **AC4 – No impact on scheduler**
  - Playing audio does not block or noticeably delay Today tab scheduling operations.

**Implementation notes**
- Keep TTS logic self-contained in `backend/tts.py` with minimal dependencies.
- Use efficient audio formats and avoid unnecessarily large bitrates.

---

## TTS-006 – Privacy and text hygiene

**User story**  
_As a privacy-conscious user, I want clarity about what text is sent to Google TTS, and for the system to avoid sending unnecessary personal details whenever possible._

**Acceptance criteria**
- **AC1 – Scope of text**
  - TTS requests only include the **short sentences** actually spoken (task names, brief summaries).
  - The system does not send raw history logs or full notes dumps to TTS.
- **AC2 – Documentation**
  - `tts_setup_stories.md` (this file) documents that Google TTS is used and what kind of text is sent.
- **AC3 – Opt-out path**
  - Users who dont want any text sent to TTS can disable the feature via config (see TTS-003) or simply avoid using the "Listen" buttons.

**Implementation notes**
- Keep TTS request text short and focused; do not pass free-form, unrelated content.
- Consider future addition of a short in-app note mentioning that TTS is powered by Google Cloud.

---

## Implementation phases (optional roadmap)

These are not separate user stories but a suggested sequence for implementing TTS safely:

1. **Phase 1 – Basic Google TTS wiring**
   - Implement `/ai/tts/play` using Google Cloud TTS.
   - Hard-code a single Standard voice and language in config.
   - No caching yet.

2. **Phase 2 – Add file-based caching**
   - Introduce a stable cache key.
   - Read/write audio files under `tts_cache/`.
   - Add simple pruning or a max-size policy.

3. **Phase 3 – Configuration polish**
   - Wire `.env`/environment-based config for language, voice, enable/disable.
   - Harden error handling and logging.

4. **Phase 4 – Nice-to-have UX**
   - Optional: pre-generate audio for upcoming tasks.
   - Optional: small in-app note that summaries can be listened to as audio.
