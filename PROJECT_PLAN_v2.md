# Personal Assistant Dashboard – Project Plan (v2)

**Project Name:** Personal Assistant Dashboard (Raspberry Pi)  
**Owner:** Nasif  
**Platform:** Raspberry Pi + external monitor + speaker (and later: phone & sensors)

---

## 1. Project Overview

### 1.1 Problem Statement

You have:
- A full-time job (hybrid WFH + office).
- Multiple personal coding projects.
- House chores (cleaning, errands, gym, dog care).
- Sleep schedule and supplements.

You frequently:
- Get stuck on one task and don’t switch to others.
- Miss chores, gym, or supplements.
- Go to bed late or wake up late.
- Get distracted by TV / random activities.

You want a **physical, hard-to-ignore assistant** that:
- Lives on a Raspberry Pi with its own monitor and speaker.
- Drives your day visually and audibly.
- Learns from your behavior and adjusts how it notifies you.

You will:
- Develop code on your **Windows laptop**, commit and push to **GitHub**.
- Have the **Raspberry Pi pull code from GitHub** (e.g. `git pull`), then restart the app.

### 1.2 Project Vision

Create a **personal operations center** that:

- Shows a colorful dashboard with:
  - Current task.
  - Countdown timer.
  - Next tasks for the day.
- Uses flickering visual alerts, alarms, and voice to force your attention.
- Logs your interactions and learns:
  - Which alert style works best for which task category.
  - When you tend to ignore or delay tasks.
- Eventually:
  - Notifies you via phone when you’re away.
  - Uses sensors/camera to detect inactivity and prompt movement or dog-related tasks.
  - Exposes an AI “coach” that helps design better routines for you.

---

## 2. Goals & Success Criteria

### 2.1 Primary Goals

1. Ensure you switch between work, coding, and chores on time.
2. Reduce missed tasks (gym, dog walks, chores, supplements).
3. Build a system that adapts to you (not the other way around).

### 2.2 Success Criteria

- You can define a daily schedule (or recurring tasks) on the system.
- Visual alerts + alarm run reliably on schedule.
- You can acknowledge or snooze/skip tasks from the dashboard.
- System logs every interaction and:
  - Adjusts alert style per task category (e.g. gym = alarm first, coding = soft visual).
- You can access your schedule and notifications from your phone (web or app).
- Later: motion/camera triggers movement reminders after X minutes at desk.
- Raspberry Pi runs a clean, fresh OS install dedicated to this project.
- Code changes on Windows can be pushed to GitHub and pulled cleanly to the Pi.

---

## 3. Scope

### 3.1 In Scope (Phase 1–3)

- Raspberry Pi backend service (Python).
- Local web dashboard (full screen on Pi).
- Task scheduling & timer logic.
- Visual alert (flickering UI) and alarm (sound) escalation.
- Logging interactions: response time, alert mode used, outcomes.
- Simple rules-based adaptation (before LLM).
- Basic web UI accessible from other devices on local network.
- Initial integration with an LLM (cloud API) for routine suggestions (non real-time).
- Clean reinstallation and configuration of the Raspberry Pi 4 for this project.
- Git-based development and deployment workflow (Windows → GitHub → Raspberry Pi).

### 3.2 Future Scope (Phase 4+)

- Mobile PWA/app with push notifications.
- Voice commands (STT) and voice responses (TTS).
- Camera & motion sensor integration.
- Advanced LLM agent for:
  - Natural language schedule edits.
  - Deeper behavior analysis.
- Automated or semi-automated deployment scripts on the Pi (e.g. one-click `git pull && restart`).

---

## 4. User & Use Cases

### 4.1 Primary User

- **Nasif** – a hybrid worker, coder, and multi-tasker who needs external structure and strong reminders.

### 4.2 Key Use Cases

1. **Daily Schedule Management**
   - Define recurring tasks (work blocks, coding blocks, chores, gym, dog-related, sleep/wake, supplements).
   - View current + next tasks on dashboard.

2. **Task Transition Alerts**
   - At the end of a work block, screen flashes and prompts you to move to coding.
   - If no response, it escalates to an alarm.

3. **Chore & Lifestyle Reminders**
   - Reminders to go to gym, clean, run errands, walk dog, go to bed, wake up, take supplements.

4. **Adaptive Notification Style**
   - For tasks where you always ignore flicker and only respond to alarm, the system auto-skips flicker for that category.

5. **Remote Access**
   - View today’s schedule and receive notifications on phone when not at home (later phase).

6. **Activity Monitoring (Future)**
   - Detect extended sitting and trigger “movement” tasks.
   - Remind you to check on or walk the dog.

7. **Dev & Deployment Workflow**
   - Write and test code on Windows.
   - Push to GitHub.
   - Log into Raspberry Pi, pull latest code and restart the app.

---

## 5. System Architecture Overview

### 5.1 Components

1. **Backend Service (Raspberry Pi)**
   - Language: Python.
   - Framework: Flask or FastAPI.
   - Responsibilities:
     - Task management (CRUD).
     - Scheduling/trigger engine.
     - Interaction logging.
     - Notification orchestration.
     - Simple adaptation logic.
   - Deployed from GitHub repository via `git clone` / `git pull`.

2. **Database**
   - SQLite (file-based, simple).
   - Tables for tasks, schedule instances, interactions, user preferences.

3. **Dashboard UI (Frontend)**
   - Tech: HTML/CSS/JavaScript.
   - Served by backend (Flask templates or SPA).
   - Runs in full-screen browser on Pi (Chromium in kiosk mode).
   - Shows:
     - Current task, remaining time.
     - Next tasks.
     - Big buttons for “Acknowledge”, “Snooze”, “Skip”.
   - Handles flicker by CSS animations.

4. **Notification Engine**
   - Visual alerts via UI state flags → JS triggers flashing.
   - Sound alarms: Python script using OS audio, e.g. `pygame`, `aplay`, or similar.
   - Voice prompts: TTS integration in later phase.

5. **AI/Learning Engine**
   - Stage 1: local rules based on logs (no LLM required).
   - Stage 2: offline calls to LLM API with summarized data for suggestions.

6. **Remote/Phone Interface**
   - Web UI (responsive) and/or API endpoints.
   - For viewing schedule, receiving simplified notifications, acknowledging tasks.

7. **Sensors & Camera (Future)**
   - PIR motion sensor via GPIO.
   - Camera via PiCam or USB.
   - Monitoring service that publishes “activity events” to backend.

8. **Development & Deployment Pipeline**
   - Development machine: Windows laptop.
   - Source control: Git + GitHub repository.
   - Raspberry Pi:
     - Clones the GitHub repo.
     - Uses `git pull` to update code.
     - Uses a systemd service or script to restart the app after updates.

---

## 6. Detailed Feature Breakdown

### 6.1 Task & Schedule Management

**Description:** Define and manage all tasks that the assistant will track.

#### Features

- Create/Edit/Delete **task templates**:
  - Name (e.g. “Morning Work Block”, “Gym”, “Evening Coding”, “Walk Dog”).
  - Category (work, coding, chore, gym, dog, sleep, supplements, misc).
  - Default duration (e.g. 60 mins).
  - Preferred time window (e.g. “anytime 6–9pm”, “exactly 7:00–8:00am”).
  - Recurrence pattern (daily, weekdays, specific days, one-off).
  - Default notification style (start with visual, or alarm, etc. – can be overridden by AI).

- Daily schedule generation:
  - Each day, generate specific **schedule instances** from templates.
  - Allow manual tweaks: move tasks earlier/later, disable for that day.

#### Acceptance Criteria

- [ ] User can create templates via UI form.
- [ ] Today’s schedule shows a time-ordered list of tasks.
- [ ] Backend stores schedule instances for each day.

---

### 6.2 Scheduler & Timer Engine

**Description:** Manages timing and triggers notifications.

#### Responsibilities

- Every few seconds:
  - Check current time vs tasks.
  - For the active task:
    - Track remaining time.
    - Trigger notifications when task start time is reached.
  - At task end:
    - Prompt transition to next task.

- Support:
  - Start, pause, resume, end for each task.
  - Snooze (e.g. +5/+10/+15 minutes).

#### Acceptance Criteria

- [ ] Tasks start at scheduled times.
- [ ] A countdown is visible for current task.
- [ ] When timer ends, an alert is triggered.
- [ ] Snoozes correctly adjust timer and logs it.

---

### 6.3 Visual Alerts & Flickering Dashboard

**Description:** Big, colorful, difficult-to-ignore screen alerts.

#### Behavior

- On task start:
  - Screen transitions to **alert mode**:
    - Large card with task name (“TIME TO GO TO THE GYM”).
    - Background or border flickers using CSS/JS.
- Alert stays active until:
  - User clicks “Acknowledge” OR
  - Timeout reached → escalate to alarm.

#### Acceptance Criteria

- [ ] Flickering effect is visually obvious and persistent.
- [ ] User can click to stop flickering.
- [ ] Visual alert triggers only for relevant tasks (not while in idle mode).

---

### 6.4 Alarm & Audio Notifications

**Description:** Escalate from visual to audio.

#### Behavior

1. Stage 1: Visual flicker only (X seconds).
2. Stage 2: If no response:
   - Play alarm sound through speaker.
   - Optionally increase volume or pattern over time.
3. Configurable delay between stages.

#### Acceptance Criteria

- [ ] If visual alert is not acknowledged within configured time, alarm starts.
- [ ] Acknowledging during alarm stops the sound.
- [ ] Alarm is loud/clear on Pi speaker.

---

### 6.5 Interaction Logging

**Description:** Every interaction is logged for learning.

#### Data to Log

For each scheduled task instance:

- Task ID, category.
- Planned start & end time.
- Actual alert start time.
- Alert path:
  - visual_only.
  - visual_then_alarm.
  - alarm_only.
- Response:
  - response type (acknowledge, snooze, skip, no_response).
  - response time (seconds from alert start).
  - which stage triggered response (visual vs alarm).
- Device used to respond (Pi UI vs phone UI later).

#### Acceptance Criteria

- [ ] Each alert generates a log entry.
- [ ] Logs can be queried (e.g. by date, category).

---

### 6.6 Adaptive Notification Logic (Rule-Based)

**Description:** Adjusts future alerts based on patterns.

#### Logic (Initial Version)

Per task category (e.g. gym, coding, chores, dog, sleep, supplements):

- Compute for the last N instances:
  - Percentage of responses at visual stage.
  - Percentage at alarm stage.
  - Percentage with no responses.
  - Average response time.

#### Rules Examples

- If >80% of responses for that category happen during alarm stage:
  - Change default alert path → start with alarm (no visual pre-stage).
- If >80% of responses happen quickly (e.g. < 20s) during visual stage:
  - Keep or make default → visual-only or visual + soft sound.
- If no response occurs often:
  - Extend alarm duration or schedule extra follow-up reminders.
- Some categories fixed (e.g. sleep might always escalate strongly).

#### Acceptance Criteria

- [ ] Scheduler reads “preferred alert style” per category.
- [ ] Preferred style is recalculated at least once per day from logs.
- [ ] Changes in alert style are reflected in later tasks automatically.

---

### 6.7 LLM Integration (Phase 3)

**Description:** Use an LLM as a “coach” for schedule and behavior.

#### Use Cases

- Weekly routine suggestions:
  - Input: summary of last week’s behavior (from logs).
  - Output: suggested schedule for next week:
    - e.g. shorter work blocks, earlier gym, bundling chores with existing routines.

- Natural language interaction:
  - “Move today’s gym session to tomorrow evening.”
  - “I’ll be out on Friday, compress my coding tasks into Monday–Thursday.”

#### Architecture

- Backend composes summarized data, sends to LLM API.
- LLM returns a structured JSON or plain text plan.
- Backend validates + maps to tasks / schedule instances.
- No real-time dependency (to avoid downtime issues).

#### Acceptance Criteria

- [ ] System can generate a summary of your behavior for a defined period.
- [ ] LLM can propose a modified schedule.
- [ ] With your confirmation, schedule is updated from that proposal.

---

### 6.8 Phone / Remote Access

**Description:** Control and view schedule from phone.

#### Features

- Responsive web dashboard:
  - View today’s tasks, statuses, reminders.
  - Acknowledge tasks, snooze, skip.
- Optional:
  - PWA installable on phone.
  - Push notifications (later).

#### Acceptance Criteria

- [ ] From same network, phone can open dashboard in browser.
- [ ] User can perform basic actions (ack, snooze, skip) from phone.
- [ ] Changes reflect on Pi dashboard in near real-time.

---

### 6.9 Sensors & Camera Integration (Future)

**Description:** Detect inactivity and physical presence to trigger movement and dog-related reminders.

#### Features

- Motion sensor via GPIO:
  - Detect whether you are at the desk.
  - Track continuous sitting duration.
- Camera (optional):
  - Simple presence detection (no heavy facial recognition needed initially).
- Movement tasks:
  - If you’ve been at desk > X minutes:
    - Add “Move break” task.
    - Trigger alert.

#### Acceptance Criteria

- [ ] Sensor service can detect presence and send events to backend.
- [ ] Backend can create on-the-fly “Move break” tasks based on sensor data.

---

## 7. Data Model (Initial Draft)

### Tables

1. **tasks**
   - `id` (PK).
   - `name`.
   - `category` (ENUM-like text).
   - `default_duration_minutes`.
   - `recurrence_pattern` (JSON or text).
   - `preferred_time_window` (JSON or text).
   - `default_alert_style` (visual_only, visual_then_alarm, alarm_only, etc.).
   - `enabled` (bool).

2. **schedule_instances**
   - `id` (PK).
   - `task_id` (FK).
   - `date`.
   - `planned_start_time`.
   - `planned_end_time`.
   - `actual_start_time` (nullable).
   - `actual_end_time` (nullable).
   - `status` (pending, active, completed, skipped, cancelled).

3. **interactions**
   - `id` (PK).
   - `schedule_instance_id` (FK).
   - `alert_type` (visual_only, visual_then_alarm, alarm_only, etc.).
   - `alert_started_at`.
   - `response_type` (acknowledge, snooze, skip, none).
   - `response_stage` (visual, alarm).
   - `response_channel` (pi_ui, phone_ui, voice).
   - `responded_at` (nullable).

4. **preferences**
   - `id` (PK).
   - `category` (same categories as tasks).
   - `preferred_alert_style`.
   - `last_updated_at`.

---

## 8. Hardware, Infrastructure & Dev Workflow

### 8.1 Raspberry Pi Cleanup & Setup

- Wipe/repurpose Raspberry Pi 4 that was used for a previous project.
- Re-flash the microSD card with a **fresh Raspberry Pi OS** image.
- Basic OS configuration:
  - Set hostname.
  - Enable SSH.
  - Configure Wi-Fi or Ethernet.
  - Update packages (`apt update && apt upgrade`).

### 8.2 Runtime Setup

- Install:
  - Python (and pip/venv).
  - Git.
  - Chromium browser (if not included).
- Configure:
  - Speakers (HDMI or audio jack) and test audio.
  - Auto-login to desktop (if using GUI).
  - Chromium to start in **kiosk mode** pointing to dashboard URL.
- Create a **systemd service** for the backend app so it starts on boot.

### 8.3 Development & Deployment Workflow

- **Development Environment (Windows Laptop)**
  - Use VS Code or preferred IDE.
  - Clone GitHub repository locally.
  - Develop features, run and test app locally (optional).
  - Commit and push changes to GitHub main or dev branch.

- **Source Control**
  - GitHub repository as single source of truth.
  - Branching strategy (e.g. `main` for stable, `dev` for work-in-progress).

- **Deployment to Raspberry Pi**
  - On Pi, clone GitHub repository once (e.g. `/home/pi/personal-assistant`).
  - For updates:
    - `cd /home/pi/personal-assistant`
    - `git pull`
    - Restart backend service (`sudo systemctl restart personal-assistant.service` or equivalent).
  - Optionally create a simple deployment script (e.g. `deploy.sh`) to automate pull + restart.

---

## 9. Implementation Phases

### Phase 0 – Pi Cleanup, Setup & Project Skeleton

- Physically gather:
  - Raspberry Pi 4, microSD card, power supply, HDMI cable, monitor, speakers, keyboard/mouse (for setup).
- Clean the Pi:
  - Backup any old data if needed.
  - Re-flash microSD with Raspberry Pi OS.
- Initial configuration:
  - Set up SSH, networking, OS updates.
  - Install Python, Git, Chromium.
- GitHub workflow:
  - Create GitHub repo for the project.
  - Clone it on Windows & Raspberry Pi.
- Create base project structure:
  - `backend/`, `frontend/`, config files, `requirements.txt`.
- Implement hello world backend + simple dashboard page.

**Deliverable:**  
Clean Raspberry Pi dedicated to this project, GitHub repo connected, and a basic app skeleton running on Pi.

---

### Phase 1 – Core Tasks & Scheduler (MVP)

- Implement:
  - `tasks`, `schedule_instances` tables.
  - Basic CRUD for tasks.
  - Daily schedule generation.
- Display:
  - Current task + countdown timer.
- Add:
  - Simple visual alert (color change, not yet flickering).
  - Button to “Acknowledge”.
- Use Git workflow:
  - Develop on Windows, push to GitHub.
  - Pull and deploy to Pi.

**Deliverable:**  
MVP where a scheduled task appears and a basic alert is shown on the Pi.

---

### Phase 2 – Full Alerts & Logging

- Upgrade UI:
  - Colorful, fullscreen dashboard.
  - CSS-based flickering effect.
- Implement escalation:
  - Visual → Alarm audio.
- Add:
  - Audio playback script.
- Implement `interactions` table and logging of:
  - alert start time.
  - response time.
  - response type and stage.
- Continue deployments via GitHub → Raspberry Pi.

**Deliverable:**  
Working alert flow and complete logging.

---

### Phase 3 – Adaptive Logic

- Implement daily job:
  - Read last N interactions per category.
  - Compute stats.
  - Update `preferences` table with `preferred_alert_style`.
- Integrate preferences:
  - When scheduling tasks, set alert style based on current preferences.

**Deliverable:**  
System automatically tailors alert style for each task category.

---

### Phase 4 – Phone UI & Remote Control

- Make dashboard responsive.
- Add “compact” view for mobile:
  - Today’s tasks list.
  - Basic controls: Ack, Snooze, Skip.
- Ensure real-time or near real-time sync with Pi UI (polling or WebSockets).

**Deliverable:**  
You can manage tasks from phone on same network.

---

### Phase 5 – LLM & Coaching

- Implement:
  - Weekly summary generator (from logs).
- Add:
  - Endpoint to call LLM API with summary.
- Map LLM response to:
  - Proposals (e.g., JSON tasks) shown on a “Recommendations” page.
- Add UI to:
  - Accept or edit proposed schedule.

**Deliverable:**  
AI-generated routine suggestions and schedule adjustments.

---

### Phase 6 – Sensors, Camera & Advanced Features (Optional)

- Integrate motion sensor / camera.
- Implement inactivity detection.
- Configure automatic “move breaks” and dog reminders.

**Deliverable:**  
The assistant reacts to your physical presence and inactivity.

---

## 10. Risks & Mitigations

- **Risk:** Over-complexity early on → project stalls.  
  **Mitigation:** Focus first on Phase 0–2 (Pi setup + scheduler + flashing + alarm).

- **Risk:** Audio, TTS, or STT issues on Pi.  
  **Mitigation:** Start with simple WAV playback; treat voice features as later phase.

- **Risk:** LLM dependency / cost.  
  **Mitigation:** Make the system fully usable with only rule-based learning; use LLM only for occasional “reviews”.

- **Risk:** You stop using the system if it’s annoying.  
  **Mitigation:** Make alert styles adjustable and allow easy “mute for X hours” during emergencies.

- **Risk:** Git merge conflicts or broken deployments.  
  **Mitigation:** Keep a simple branching model at first and test changes locally on Windows before pulling to Pi.

---

## 11. Next Steps

- Save this plan as `PROJECT_PLAN.md` in your GitHub repo.
- Clean and re-flash your Raspberry Pi 4.
- Set up Git, Python, and Chromium on Pi.
- Start implementing Phase 0 and Phase 1 using the GitHub-based workflow.
