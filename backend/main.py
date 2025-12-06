from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .db import Base, engine
from .routers import schedule, tasks, ai


# Ensure tables are created on startup (simple dev-time approach)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Assistant Dashboard")

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


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
            background-color: #020617;
            background-image:
                linear-gradient(rgba(31,41,55,0.55) 1px, transparent 1px),
                linear-gradient(90deg, rgba(31,41,55,0.55) 1px, transparent 1px),
                radial-gradient(circle at top, #111827 0, #020617 55%, #000 100%);
            background-size: 40px 40px, 40px 40px, auto;
            background-position: 0 0, 0 0, center;
            color: #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
        }
        .shell {
            width: min(1100px, 100%);
            background: radial-gradient(circle at top left, rgba(56,189,248,0.18), rgba(15,23,42,0.96));
            border-radius: 1.5rem;
            border: 1px solid rgba(148,163,184,0.5);
            box-shadow: 0 26px 70px rgba(15,23,42,0.95);
            padding: 1.5rem 1.75rem 1.6rem;
            backdrop-filter: blur(16px);
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
        .header-right {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 0.3rem;
        }
        .hud-clock {
            font-size: 0.8rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #9ca3af;
            font-variant-numeric: tabular-nums;
        }
        .top-now-strip {
            margin: 0 0 0.6rem;
            padding: 0.35rem 0.85rem;
            border-radius: 999px;
            border: 1px solid rgba(59,130,246,0.8);
            background: radial-gradient(circle at left, rgba(59,130,246,0.35), rgba(15,23,42,0.98));
            font-size: 0.8rem;
            color: #bfdbfe;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.75rem;
            font-variant-numeric: tabular-nums;
        }
        .top-now-strip.active {
            border-color: rgba(34,197,94,0.9);
            box-shadow: 0 0 0 1px rgba(34,197,94,0.55);
        }
        .top-now-strip.paused {
            border-color: rgba(245,158,11,0.95);
            box-shadow: 0 0 0 1px rgba(245,158,11,0.55);
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
        #view-today.grid {
            grid-template-columns: 1fr;
        }
        #view-history.grid {
            grid-template-columns: 1fr;
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
        .template-search-row {
            margin-top: 0.35rem;
            margin-bottom: 0.25rem;
        }
        .task-group {
            margin-bottom: 0.6rem;
        }
        .task-group-header {
            width: 100%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.3rem 0.55rem;
            border-radius: 0.7rem;
            border: 1px solid rgba(30,64,175,0.8);
            background: radial-gradient(circle at left, rgba(30,64,175,0.4), rgba(15,23,42,0.98));
            color: #e5e7eb;
            font-size: 0.78rem;
            cursor: pointer;
        }
        .task-group-title-wrap {
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }
        .task-group-title {
            font-weight: 500;
            font-size: 0.8rem;
        }
        .task-group-count {
            font-size: 0.75rem;
            color: #9ca3af;
        }
        .task-group-caret {
            font-size: 0.7rem;
            color: #9ca3af;
            transition: transform 0.15s ease-out;
        }
        .task-group-body {
            margin-top: 0.35rem;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }
        .task-group.collapsed .task-group-body {
            display: none;
        }
        .task-group.collapsed .task-group-caret {
            transform: rotate(-90deg);
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
            margin-bottom: 0.55rem;
            font-size: 1.05rem;
            padding: 0.6rem 0.9rem;
            border-radius: 0.9rem;
            border: 1px solid rgba(34,197,94,0.7);
            background:
                radial-gradient(circle at left, rgba(34,197,94,0.3), transparent 60%),
                rgba(15,23,42,0.98);
            color: #bbf7d0;
            font-variant-numeric: tabular-nums;
            box-shadow: 0 0 0 1px rgba(34,197,94,0.35);
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
            position: relative;
            padding-left: 0.6rem;
        }
        .schedule-list::before {
            content: "";
            position: absolute;
            top: 0.3rem;
            bottom: 0.3rem;
            left: 0.9rem;
            width: 1px;
            background-image: linear-gradient(to bottom, rgba(55,65,81,0.8), transparent 55%);
            opacity: 0.85;
        }
        .add-today-row {
            margin-top: 0.35rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            align-items: center;
            font-size: 0.78rem;
        }
        .add-today-row input[type="text"],
        .add-today-row input[type="number"],
        .add-today-row input[type="time"] {
            max-width: 7.5rem;
        }
        .add-today-label {
            color: #9ca3af;
        }
        .micro-journal {
            margin-top: 0.5rem;
            padding-top: 0.45rem;
            border-top: 1px solid rgba(31,41,55,0.9);
        }
        .micro-journal-hidden {
            display: none;
        }
        .micro-journal-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            align-items: center;
            font-size: 0.78rem;
        }
        .micro-journal-input {
            flex: 1;
            min-width: 0;
        }
        .overlay-controls {
            margin-top: 0.35rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
            font-size: 0.78rem;
        }
        .overlay-toggle {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            color: #9ca3af;
        }
        .overlay-mode-select {
            border-radius: 0.5rem;
            border: 1px solid rgba(55,65,81,0.9);
            background: rgba(15,23,42,0.9);
            color: #e5e7eb;
            padding: 0.25rem 0.5rem;
            font-size: 0.78rem;
        }
        .history-list {
            margin-top: 0.35rem;
            display: flex;
            flex-direction: column;
            gap: 0.3rem;
            max-height: 220px;
            overflow-y: auto;
            font-size: 0.78rem;
        }
        .history-item {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            border-radius: 0.6rem;
            padding: 0.3rem 0.45rem;
            background: rgba(15,23,42,0.96);
            border: 1px solid rgba(55,65,81,0.9);
        }
        .history-main {
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
            margin-right: 0.5rem;
        }
        .history-task {
            font-weight: 500;
        }
        .history-meta {
            color: #9ca3af;
            font-size: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.35rem;
            flex-wrap: wrap;
        }
        .history-badge {
            padding: 0.05rem 0.4rem;
            border-radius: 999px;
            border: 1px solid rgba(55,65,81,0.9);
            font-size: 0.7rem;
            font-variant-numeric: tabular-nums;
        }
        .history-badge-ack {
            border-color: rgba(34,197,94,0.9);
            background: rgba(22,163,74,0.18);
            color: #bbf7d0;
        }
        .history-badge-snooze {
            border-color: rgba(245,158,11,0.95);
            background: rgba(217,119,6,0.2);
            color: #fed7aa;
        }
        .history-badge-skip {
            border-color: rgba(248,113,113,0.95);
            background: rgba(185,28,28,0.35);
            color: #fecaca;
        }
        .history-badge-none {
            border-color: rgba(75,85,99,0.9);
            background: rgba(17,24,39,0.9);
            color: #9ca3af;
        }
        .history-times {
            font-variant-numeric: tabular-nums;
            color: #9ca3af;
            font-size: 0.72rem;
            white-space: nowrap;
        }
        .history-filters {
            margin-top: 0.25rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            align-items: flex-end;
            font-size: 0.78rem;
        }
        .history-filter-group {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
        }
        .history-filter-label {
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
            color: #9ca3af;
        }
        .history-filter-input {
            border-radius: 0.5rem;
            border: 1px solid rgba(55,65,81,0.9);
            background: rgba(15,23,42,0.9);
            color: #e5e7eb;
            padding: 0.2rem 0.4rem;
            font-size: 0.78rem;
        }
        .history-filter-select {
            border-radius: 0.5rem;
            border: 1px solid rgba(55,65,81,0.9);
            background: rgba(15,23,42,0.9);
            color: #e5e7eb;
            padding: 0.2rem 0.4rem;
            font-size: 0.78rem;
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
            position: relative;
            border-radius: 0.7rem;
            padding: 0.4rem 0.5rem 0.4rem 1.4rem;
            background: rgba(15,23,42,0.96);
            border: 1px solid rgba(30,64,175,0.75);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.6rem;
            font-size: 0.8rem;
        }
        .schedule-item::before {
            content: "";
            position: absolute;
            left: 0.55rem;
            top: 50%;
            transform: translateY(-50%);
            width: 0.55rem;
            height: 0.55rem;
            border-radius: 999px;
            background: radial-gradient(circle, #60a5fa 0, #1d4ed8 55%, transparent 100%);
            box-shadow: 0 0 0 1px rgba(37,99,235,0.9);
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
        .now-next-overlay {
            position: fixed;
            inset: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            pointer-events: none; /* let clicks pass through to main UI */
            z-index: 30;
        }
        .now-next-overlay.now-next-hidden {
            display: none;
        }
        .now-next-overlay.now-next-corner {
            align-items: flex-start;
            justify-content: flex-end;
            padding: 0.75rem 0.75rem 0 0;
        }
        .now-next-overlay.now-next-corner .now-next-inner {
            min-width: 320px;
            max-width: 360px;
            padding: 0.75rem 1rem;
            border-radius: 1.1rem;
        }
        .now-next-overlay.now-next-corner .now-name {
            font-size: 1.2rem;
        }
        .now-next-overlay.now-next-corner #now-next-countdown {
            font-size: 1.5rem;
        }
        .now-next-inner {
            pointer-events: none; /* purely visual cards */
            padding: 2rem 2.5rem;
            border-radius: 1.5rem;
            background: rgba(15,23,42,0.65);
            border: 1px solid rgba(148,163,184,0.7);
            box-shadow: 0 24px 60px rgba(0,0,0,0.8);
            backdrop-filter: blur(18px);
            min-width: 520px;
            max-width: 720px;
        }
        .now-next-header {
            font-size: 0.9rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #9ca3af;
            margin-bottom: 0.6rem;
        }
        .now-block {
            padding: 1rem 1.2rem;
            border-radius: 1rem;
            background: radial-gradient(circle at left, rgba(34,197,94,0.3), transparent 70%);
            border: 1px solid rgba(34,197,94,0.7);
            margin-bottom: 0.9rem;
            font-size: 1.1rem;
        }
        .now-name {
            font-weight: 700;
            font-size: 1.6rem;
            margin-bottom: 0.25rem;
        }
        .now-meta-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            font-variant-numeric: tabular-nums;
            color: #bbf7d0;
            font-size: 1.1rem;
            gap: 1.25rem;
        }
        #now-next-countdown {
            font-size: 3rem;
            font-weight: 700;
        }
        .next-block {
            padding: 0.9rem 1.1rem;
            border-radius: 1.1rem;
            background: radial-gradient(circle at left, rgba(59,130,246,0.32), transparent 70%);
            border: 1px solid rgba(59,130,246,0.75);
            font-size: 1.1rem;
        }
        .next-label {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #bfdbfe;
            margin-bottom: 0.25rem;
        }
        .next-name {
            font-weight: 700;
            font-size: 1.4rem;
            margin-bottom: 0.1rem;
        }
        .next-time {
            font-size: 1.1rem;
            color: #bfdbfe;
            font-variant-numeric: tabular-nums;
        }
        .now-next-empty {
            font-size: 0.8rem;
            color: #9ca3af;
        }
        .tab-bar {
            display: flex;
            gap: 0.5rem;
            margin: 0 0 1rem;
            border-bottom: 1px solid rgba(55, 65, 81, 0.9);
            padding-bottom: 0.5rem;
        }
        .tab-button {
            border: none;
            border-radius: 999px;
            padding: 0.35rem 0.9rem;
            font-size: 0.85rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            background: rgba(31, 41, 55, 0.9);
            color: #9ca3af;
            cursor: pointer;
            transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
        }
        .tab-button:hover {
            color: #e5e7eb;
            box-shadow: 0 0 0 1px rgba(55, 65, 81, 0.9);
        }
        .tab-button.tab-active {
            background: radial-gradient(circle at top left, rgba(34,197,94,0.5), rgba(15,23,42,0.9));
            color: #ecfdf5;
            box-shadow: 0 0 0 1px rgba(34,197,94,0.7);
        }
        .view-hidden {
            display: none;
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
                <div class="subtitle">Today-focused view with quick access to templates, alerts, and history.</div>
            </div>
            <div class="header-right">
                <div id="hud-clock" class="hud-clock"></div>
                <div class="pill">Today · Planner · Insights</div>
            </div>
        </header>
        <div id="top-now-strip" class="top-now-strip">Now: —</div>
        <div id="now-next" class="now-next-overlay now-next-hidden">
            <div class="now-next-inner">
                <div class="now-next-header">Now &amp; Next</div>
                <div id="now-next-content" class="now-next-empty">No active task yet.</div>
            </div>
        </div>
        <div class="tab-bar">
            <button class="tab-button tab-active" data-view="today">Today</button>
            <button class="tab-button" data-view="planner">Planner</button>
            <button class="tab-button" data-view="history">History &amp; Insights</button>
        </div>

        <section id="view-today" class="grid">
            <section class="card">
                <h2 class="schedule-section-title">Today's Schedule</h2>
                <p class="hint">Focus mode: adjust only what you need for today, including ad-hoc tasks.</p>
                <div class="template-search-row" style="margin-bottom: 0.2rem;">
                    <div style="display: flex; flex-direction: column; gap: 0.25rem; width: 100%;">
                        <div style="display: flex; justify-content: space-between; align-items: center; gap: 0.5rem;">
                            <span style="font-size: 0.8rem; color: #9ca3af;">What should I do now?</span>
                            <button id="ai-now-btn" type="button" class="action-btn edit" style="padding: 0.25rem 0.7rem; font-size: 0.75rem;">Ask AI</button>
                        </div>
                        <div id="ai-now-suggestion" class="status-text" style="min-height: 1.4rem;"></div>
                    </div>
                </div>
                <div class="add-today-row">
                    <span class="add-today-label">Add task to today:</span>
                    <input id="add-today-name" type="text" placeholder="Name" />
                    <input id="add-today-category" type="text" placeholder="Category" />
                    <input
                        id="add-today-duration"
                        type="number"
                        min="1"
                        step="1"
                        placeholder="Min"
                    />
                    <input id="add-today-start" type="time" />
                    <button id="add-today-btn" type="button" class="action-btn edit">Add</button>
                </div>
                <div id="active-task-banner" class="active-banner"></div>
                <div id="schedule-status" class="status-text"></div>
                <div class="overlay-controls">
                    <label class="overlay-toggle">
                        <input id="overlay-enabled" type="checkbox" checked />
                        <span>Show Now &amp; Next overlay</span>
                    </label>
                    <select id="overlay-mode" class="overlay-mode-select">
                        <option value="auto" selected>Auto (center on idle)</option>
                        <option value="corner">Always-on corner</option>
                    </select>
                </div>
                <div id="schedule-list" class="schedule-list"></div>
                <div id="micro-journal" class="micro-journal micro-journal-hidden">
                    <p class="hint" style="margin-bottom: 0.4rem;">Optional: jot a short note about why you snoozed or skipped.</p>
                    <div class="micro-journal-row">
                        <span id="micro-journal-label" class="add-today-label"></span>
                        <input
                            id="micro-journal-input"
                            type="text"
                            maxlength="300"
                            class="history-filter-input micro-journal-input"
                            placeholder="One short sentence (optional)"
                        />
                        <button id="micro-journal-save" type="button" class="action-btn edit">Save note</button>
                        <button id="micro-journal-skip" type="button" class="action-btn">Skip</button>
                    </div>
                    <div id="micro-journal-status" class="status-text"></div>
                </div>
            </section>
        </section>

        <section id="view-planner" class="grid view-hidden">
            <section class="card">
                <h2>Design &amp; refine your routine</h2>
                <p class="hint">Use the form and AI helper to design your recurring day, then refine individual templates as you go.</p>
                <div class="template-search-row">
                    <textarea
                        id="ai-template-free-text"
                        rows="2"
                        style="width: 100%; resize: vertical; font-size: 0.8rem;"
                        placeholder="Describe your routine in a few sentences, e.g. 'On weekdays I want deep work blocks, a walk, and a short evening wind‑down.'"
                    ></textarea>
                    <button id="ai-template-suggest-btn" type="button" class="action-btn edit" style="margin-top: 0.3rem;">
                        Design my routine (AI)
                    </button>
                    <div id="ai-template-status" class="status-text"></div>
                </div>
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
                <div class="template-search-row">
                    <input
                        id="template-search"
                        type="search"
                        class="history-filter-input"
                        placeholder="Search templates by name or category"
                    />
                </div>
                <div id="tasks-list" class="tasks-list"></div>
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
                <hr class="divider" />
                <h2 class="schedule-section-title">AI Alert Wording Experiments</h2>
                <p class="hint">Have the AI suggest alternative alert texts per category and tone, then pick one to use.</p>
                <div class="alarm-settings" id="alert-wording-settings">
                    <div class="alarm-settings-row">
                        <label class="alarm-label">
                            Category
                            <select id="alert-wording-category" class="history-filter-select">
                                <option value="">Select category</option>
                            </select>
                        </label>
                    </div>
                    <div class="alarm-settings-row">
                        <label class="alarm-label">
                            Tone
                            <input
                                id="alert-wording-tone"
                                type="text"
                                class="history-filter-input"
                                placeholder="e.g. neutral/firm, encouraging, protective"
                            />
                        </label>
                    </div>
                    <div class="alarm-settings-row">
                        <label class="alarm-label">
                            Max length (characters)
                            <input
                                id="alert-wording-max-length"
                                type="number"
                                class="history-filter-input"
                                min="40"
                                max="200"
                                step="10"
                                value="120"
                            />
                        </label>
                        <label class="alarm-label">
                            Options to generate
                            <input
                                id="alert-wording-count"
                                type="number"
                                class="history-filter-input"
                                min="3"
                                max="8"
                                step="1"
                                value="5"
                            />
                        </label>
                    </div>
                    <div class="alarm-settings-row alarm-settings-actions">
                        <button id="ai-alert-wording-btn" type="button" class="action-btn edit">Ask AI for alert texts</button>
                    </div>
                    <div id="ai-alert-wording-status" class="status-text"></div>
                    <div id="alert-wording-current" class="status-text"></div>
                    <div id="ai-alert-wording-options" class="history-list" style="margin-top: 0.3rem;"></div>
                </div>
            </section>
        </section>

        <section id="view-history" class="grid view-hidden">
            <section class="card">
                <h2 class="schedule-section-title">Interaction History</h2>
                <p class="hint">Recent alerts and how you responded. Use filters, then ask the assistant for summaries.</p>
                <div class="history-filters">
                    <div class="history-filter-group">
                        <label class="history-filter-label">
                            From
                            <input id="history-from" type="date" class="history-filter-input" />
                        </label>
                        <label class="history-filter-label">
                            To
                            <input id="history-to" type="date" class="history-filter-input" />
                        </label>
                    </div>
                    <label class="history-filter-label">
                        Category
                        <select id="history-category" class="history-filter-select">
                            <option value="">All categories</option>
                        </select>
                    </label>
                </div>
                <div id="history-list" class="history-list"></div>
            </section>
            <section class="card">
                <h2 class="schedule-section-title">AI Insights on Alerts</h2>
                <p class="hint">Have the assistant scan this range for behavior patterns and gentle adjustments.</p>
                <div class="history-filters" style="margin-top: 0.3rem; margin-bottom: 0.4rem;">
                    <div class="history-filter-group">
                        <span style="font-size: 0.78rem; color: #9ca3af;">Uses the same From/To range above. Leave blank for last 7 days.</span>
                    </div>
                    <button id="ai-history-btn" type="button" class="action-btn edit">Generate insights (AI)</button>
                </div>
                <div id="ai-history-status" class="status-text"></div>
                <div id="ai-history-insights" class="history-list" style="margin-top: 0.4rem;"></div>
                <div id="ai-history-recs" class="history-list" style="margin-top: 0.2rem;"></div>
                <div class="history-filters" style="margin-top: 0.3rem;">
                    <button id="ai-history-play-btn" type="button" class="action-btn">Listen to summary (audio)</button>
                </div>
            </section>
            <section class="card">
                <h2 class="schedule-section-title">Skip &amp; Snooze Notes – AI Summary</h2>
                <p class="hint">Summarize why you skipped or snoozed tasks in this range, using your micro-journal notes.</p>
                <div class="history-filters" style="margin-top: 0.3rem; margin-bottom: 0.4rem;">
                    <div class="history-filter-group">
                        <span style="font-size: 0.78rem; color: #9ca3af;">Uses the same From/To range above. Only considers notes recorded right after snooze/disable actions.</span>
                    </div>
                    <button id="ai-notes-btn" type="button" class="action-btn edit">Summarize notes (AI)</button>
                </div>
                <div id="ai-notes-status" class="status-text"></div>
                <div id="ai-notes-patterns" class="history-list" style="margin-top: 0.4rem;"></div>
                <div id="ai-notes-recs" class="history-list" style="margin-top: 0.2rem;"></div>
                <div class="history-filters" style="margin-top: 0.3rem;">
                    <button id="ai-notes-play-btn" type="button" class="action-btn">Listen to notes summary (audio)</button>
                </div>
            </section>
        </section>
        <footer class="footer">
            <span>Backend: FastAPI · SQLite · SQLAlchemy</span>
            <span>Epics: Task & schedule management first, then scheduler & alerts.</span>
        </footer>
    </main>
    <script src="/static/js/today.js"></script>
    <script src="/static/js/planner.js"></script>
    <script src="/static/js/history.js"></script>
    <script src="/static/js/ai.js"></script>
    <script src="/static/js/main.js"></script>
    </body>
    </html>
"""
app.include_router(tasks.router)
app.include_router(schedule.router)
app.include_router(ai.router)
