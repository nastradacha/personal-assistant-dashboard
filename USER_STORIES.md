# Personal Assistant Dashboard – User Stories

This document captures user stories derived from the project plan, including setup of the Raspberry Pi from a clean state and a GitHub-based development workflow (Windows → GitHub → Raspberry Pi).

---

## Epic 1 – Task & Schedule Management

### PA-001 – Create Task Templates
**As** Nasif  
**I want** to create reusable task templates for things I do regularly (work blocks, coding, chores, gym, dog, sleep, supplements)  
**So that** I don’t have to manually recreate them every day.

**Acceptance Criteria**
 - [x] From the UI, I can open a “New Task Template” form.
 - [x] I can set: name, category, default duration, recurrence (e.g. daily, weekdays), and preferred time window.
 - [x] I can save the template and see it in a list of templates.
 - [x] Templates are stored in the database and persist after restart.

---

### PA-002 – Edit & Delete Task Templates
**As** Nasif  
**I want** to edit or delete existing task templates  
**So that** my recurring tasks stay up to date with my real-life routine.

**Acceptance Criteria**
 - [x] From the templates list, I can open an existing template and change its fields.
 - [x] I can delete a template and it disappears from the list.
 - [x] Deleting a template does **not** remove historical log data, only future schedule generation.

---

### PA-003 – Auto-generate Daily Schedule
**As** Nasif  
**I want** the system to generate a daily schedule from my templates  
**So that** I have a full day plan without manually assigning every task.

**Acceptance Criteria**
- [x] When a new day starts, the system creates `schedule_instances` from enabled templates.
- [x] The schedule respects recurrence rules (e.g. weekdays only, specific days).
- [x] I can see a list of today’s tasks ordered by time.
- [x] If no templates exist, the schedule shows as empty with a friendly message.

---

### PA-004 – Manually Adjust Today’s Schedule
**As** Nasif  
**I want** to adjust today’s generated schedule  
**So that** I can move tasks around when real life changes.

**Acceptance Criteria**
- [x] I can change the start time of a scheduled task instance for today.
- [x] I can disable a task instance for today (e.g. cancel gym).
- [x] Adjusted times are saved and reflected on the dashboard.
- [x] Adjustments affect only that day, not the underlying template.

---

## Epic 2 – Scheduler & Timer Engine

### PA-005 – Start Tasks Automatically At Scheduled Time
**As** Nasif  
**I want** tasks to start automatically when their scheduled time comes  
**So that** I don’t have to remember to manually start timers.

**Acceptance Criteria**
 - [x] When current time >= planned start_time for a pending task, it becomes “active”.
 - [x] Only one task can be “active” at a time.
 - [x] The active task is shown prominently on the dashboard.
 - [x] If system restarts, it restores the correct active task based on current time.

---

### PA-006 – Show Countdown Timer for Active Task
**As** Nasif  
**I want** to see a countdown timer for the current task  
**So that** I know how much time I have left.

**Acceptance Criteria**
 - [x] The dashboard shows remaining time (e.g. `00:23:45`) for the active task.
 - [x] Timer updates every second.
 - [ ] When timer reaches zero, the appropriate alert is triggered.
 - [ ] Pausing/resuming the task updates remaining time correctly.

---

### PA-007 – Pause and Resume Current Task
**As** Nasif  
**I want** to pause and resume a task  
**So that** I can handle interruptions without losing context.

**Acceptance Criteria**
 - [x] There is a “Pause” button for the active task.
 - [x] When paused, countdown stops and visual state indicates paused.
 - [x] “Resume” restarts countdown from where it left off.
 - [x] Pause/resume events are recorded in the database (optional log).

---

### PA-008 – Snooze Current Task
**As** Nasif  
**I want** to snooze a task for a few minutes  
**So that** I can delay switching when needed without cancelling.

**Acceptance Criteria**
- [x] There is a “Snooze” button with preset options (e.g. +5, +10, +15 mins).
- [x] Choosing snooze extends the end time or delays task start (depending on design).
- [ ] Alert stops when snoozed and restarts after snooze period.
- [x] Snooze is logged with timestamp and duration.

---

## Epic 3 – Visual Alerts & Audio Alarms

### PA-009 – Flickering Visual Alert on Task Start
**As** Nasif  
**I want** a bright flickering screen when a new task starts  
**So that** I can’t ignore when it’s time to switch.

**Acceptance Criteria**
- [x] When a task becomes active, dashboard enters “alert mode”.
- [x] Background or a large area flashes between at least two colors.
- [x] Alert continues until I acknowledge or snooze.
- [x] Flicker works full-screen and is clearly noticeable.

---

### PA-010 – Visual Alert Escalation to Alarm
**As** Nasif  
**I want** the system to escalate from visual to audio alarm if I ignore it  
**So that** I don’t miss important transitions.

**Acceptance Criteria**
- [x] If no response within configurable delay (e.g. 60–120 seconds), an audio alarm starts.
- [x] Visual flicker continues while alarm is playing.
- [x] Alarm stops instantly when I acknowledge/snooze/skip.
- [x] Escalation delay is configurable (e.g. via settings file or UI).

---

### PA-011 – Acknowledge Alert From Dashboard
**As** Nasif  
**I want** a simple “I’m on it” button  
**So that** I can tell the system I’ve seen the alert.

**Acceptance Criteria**
- [x] There is a large, clearly labeled “Acknowledge” button during alerts.
- [x] Clicking it:
  - Stops flickering.
  - Stops audio if playing.
  - Marks the alert as responded (with timestamp).
- [x] System transitions to “normal” mode showing task progress.

---

### PA-012 – Alarm Configuration
**As** Nasif  
**I want** to configure alarm sounds and volume  
**So that** the alerts are loud enough but not unbearable.

**Acceptance Criteria**
 - [x] I can choose between at least two alarm sounds.
 - [x] I can set a preferred volume level (within OS limits).
 - [x] Test button plays sound at configured volume.
 - [x] Settings persist after restart.

---

## Epic 4 – Interaction Logging & Adaptive Logic

### PA-013 – Log Each Alert Interaction
**As** the system owner  
**I want** every alert and my response to be logged  
**So that** the AI can analyze my habits later.

**Acceptance Criteria**
- [ ] For every scheduled task alert, an entry is added to `interactions`.
- [ ] Logged fields include: schedule_instance_id, alert_type, alert_started_at.
- [ ] When I respond, log is updated with response_type, response_stage, responded_at.
- [ ] If I never respond, system eventually marks response_type as `none` after some timeout.

---

### PA-014 – View Basic Interaction History
**As** Nasif  
**I want** to view recent interaction history  
**So that** I can understand how I’ve been responding to reminders.

**Acceptance Criteria**
- [ ] Simple “History” page listing recent tasks with:
  - Task name, category.
  - Alert type used.
  - Response type (acknowledge/snooze/skip/none).
  - Response stage (visual vs alarm).
- [ ] History is sorted by most recent first.
- [ ] I can filter by date range and category (optional for later).

---

### PA-015 – Calculate Preferred Alert Style Per Category
**As** the system  
**I want** to compute a preferred alert style per task category  
**So that** future alerts match Nasif’s actual behavior.

**Acceptance Criteria**
- [ ] A scheduled job (e.g. once per day) runs an analysis of interactions per category.
- [ ] For each category, it calculates:
  - Percent of responses at visual stage.
  - Percent of responses at alarm stage.
  - Percent of no responses.
- [ ] Based on thresholds (configurable), it chooses a `preferred_alert_style` and saves it in `preferences`.

---

### PA-016 – Use Preferred Alert Style for New Tasks
**As** Nasif  
**I want** new alerts to adapt based on my habits  
**So that** I get the type of notification that actually works for me.

**Acceptance Criteria**
- [ ] When new schedule instances are created, they get an alert style based on their category’s `preferred_alert_style`.
- [ ] If no preference exists yet, they use template’s default style.
- [ ] When preferences change, new tasks use updated style; old historical data stays unchanged.

---

## Epic 5 – Phone / Remote Access

### PA-017 – Access Dashboard from Phone Browser
**As** Nasif  
**I want** to view my schedule on my phone  
**So that** I can keep up with tasks when away from the Pi screen.

**Acceptance Criteria**
- [ ] The same web dashboard is reachable from another device on the local network (via IP/hostname).
- [ ] Layout is responsive and readable on mobile screen.
- [ ] I can see current task and today’s list.

---

### PA-018 – Remote Acknowledge/Snooze/Skip
**As** Nasif  
**I want** to acknowledge or snooze tasks from my phone  
**So that** I don’t have to be physically at the Pi.

**Acceptance Criteria**
- [ ] On mobile view, I can see active alerts and buttons to Ack/Snooze/Skip.
- [ ] Actions taken on phone are reflected on Pi dashboard in near real-time.
- [ ] These remote interactions are logged with `response_channel = phone_ui`.

---

### PA-019 – Lightweight Mobile View (Compact Mode)
**As** Nasif  
**I want** a simplified view on my phone  
**So that** I can quickly see what’s next without heavy UI.

**Acceptance Criteria**
- [ ] Mobile view shows:
  - Next upcoming task.
  - Current task status.
  - A short list of next 3–5 tasks.
- [ ] Pages load quickly over LAN.
- [ ] Optional: toggle between “full dashboard” and “compact view”.

---

## Epic 6 – LLM / AI Coaching (Later Phase)

### PA-020 – Weekly Behavior Summary
**As** Nasif  
**I want** a weekly summary of my behavior  
**So that** I can understand patterns like “always late to gym”.

**Acceptance Criteria**
- [ ] A command or scheduled job generates a summary for a selected week:
  - Number of tasks completed, snoozed, skipped, missed.
  - Breakdown by category.
  - Average response times and stages.
- [ ] Summary is human-readable and also available in a structured format (JSON or similar).

---

### PA-021 – Generate AI-based Routine Suggestions
**As** Nasif  
**I want** the AI to suggest a better weekly routine  
**So that** I gradually improve my habits.

**Acceptance Criteria**
- [ ] System sends the weekly summary + current schedule to an LLM API.
- [ ] LLM replies with suggested changes (e.g. shorter evening coding blocks, moving gym earlier).
- [ ] Suggestions are displayed on a “Recommendations” page.
- [ ] Nothing is changed automatically; I must confirm any updates.

---

### PA-022 – Apply AI Suggestions to Schedule
**As** Nasif  
**I want** to apply AI suggestions with one click  
**So that** I can quickly adopt a better schedule.

**Acceptance Criteria**
- [ ] On the “Recommendations” page, I can accept or reject each suggested change.
- [ ] Accepted changes are converted into updated templates or schedule instances.
- [ ] The system logs that changes came from AI suggestions.

---

## Epic 7 – Sensors & Activity Monitoring (Optional / Future)

### PA-023 – Detect Desk Presence via Sensor
**As** the system  
**I want** to know when I’m sitting at the desk  
**So that** I can track continuous sitting time.

**Acceptance Criteria**
- [ ] Motion or presence sensor data is read and converted into “present” or “away” states.
- [ ] Presence state and timestamps can be logged for debugging.
- [ ] Sensor errors are handled gracefully (no crash, just disable feature).

---

### PA-024 – Trigger Move Break Task After Long Sitting
**As** Nasif  
**I want** the system to remind me to move after I sit too long  
**So that** I don’t stay at the PC for unhealthy stretches.

**Acceptance Criteria**
- [ ] If presence has been “at desk” for more than X minutes (configurable), a “Move break” task is created or activated.
- [ ] Move break triggers the same visual/alarm alerts like other tasks.
- [ ] If I stand up (sensor sees “away”), move break can be considered completed or cancelled (depending on design).

---

### PA-025 – Dog Check / Walk Reminders Based on Time & Activity
**As** Nasif  
**I want** reminders to walk or check on my dog  
**So that** dog care is part of my routine, not random.

**Acceptance Criteria**
- [ ] I can create dog-related templates (e.g. “Walk Dog”, “Check Water/Food”).
- [ ] These tasks appear in the daily schedule like others.
- [ ] (Optional) If I’ve been at PC during scheduled dog walk time, alerts are escalated more strongly (e.g. direct alarm).

---

## Epic 8 – Setup, Pi Cleanup & Infrastructure

### PA-026 – Raspberry Pi Cleanup & Fresh OS Install
**As** Nasif  
**I want** to clean and reinitialize my Raspberry Pi 4  
**So that** it is dedicated to this assistant and not cluttered by old projects.

**Acceptance Criteria**
- [ ] Any needed data from the old project is backed up (if necessary).
- [ ] The microSD card is re-flashed with a fresh Raspberry Pi OS image.
- [ ] Pi boots successfully into the new OS.
- [ ] Basic configuration is done (hostname, SSH, Wi-Fi/Ethernet, OS updates).

---

### PA-027 – Raspberry Pi Runtime Environment Setup
**As** Nasif  
**I want** a reproducible Pi runtime environment  
**So that** the assistant runs reliably and can be rebuilt if needed.

**Acceptance Criteria**
- [ ] Python, pip/venv, Git, and Chromium are installed.
- [ ] Speakers are configured and a test sound plays successfully.
- [ ] Chromium is configured (or script is prepared) to launch in kiosk mode with the dashboard URL.
- [ ] A systemd service (or similar) is defined to auto-start the backend app on boot.

---

### PA-028 – Configuration Management
**As** a developer/admin  
**I want** a central configuration file  
**So that** I can tune things (delays, thresholds, LLM keys) without touching code.

**Acceptance Criteria**
- [ ] Single config file (e.g. `config.yaml` or `.env`) defines:
  - Alert escalation delay.
  - Thresholds for adaptive rules.
  - LLM API keys (if used).
- [ ] App reads config at startup.
- [ ] Changes take effect on restart.

---

### PA-029 – GitHub-based Development Workflow
**As** Nasif  
**I want** to develop on my Windows laptop and deploy via GitHub to the Raspberry Pi  
**So that** I have a clean, version-controlled workflow.

**Acceptance Criteria**
- [ ] A GitHub repository exists for the project.
- [ ] The repo is cloned on the Windows laptop and on the Raspberry Pi.
- [ ] I can develop features on Windows, commit, and push to GitHub.
- [ ] On the Pi, I can pull the latest changes (`git pull`) into the project folder.
- [ ] There is a documented or scripted way to restart the app after pulling (e.g. `deploy.sh` or `systemctl restart personal-assistant.service`).
- [ ] This workflow is documented in the repo (e.g. `DEV_WORKFLOW.md`).

---

### PA-030 – Basic Error Logging
**As** a developer  
**I want** to log errors and key events  
**So that** I can debug issues on the Pi.

**Acceptance Criteria**
- [ ] Application writes logs to a file (e.g. `app.log`).
- [ ] Errors contain timestamp and stack trace.
- [ ] Important events (task starts, alerts, user actions, deployment restarts) are logged at INFO level.

---

