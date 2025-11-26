# Dev Workflow – Personal Assistant Dashboard

## Local development (Windows laptop)

1. Create and activate virtualenv (once per machine):
   ```bash
   python -m venv .venv
   .venv\\Scripts\\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the backend (FastAPI):
   ```bash
   uvicorn backend.main:app --reload
   ```

4. Open in browser:
   - API health: http://127.0.0.1:8000/health
   - Dashboard: http://127.0.0.1:8000/

## Git & GitHub workflow

1. Initialize repo (first time only):
   ```bash
   git init
   git add .
   git commit -m "chore: initialize FastAPI skeleton"
   ```

2. Create an empty GitHub repo (via GitHub UI), e.g. `personal-assistant-dashboard`.

3. Add remote and push:
   ```bash
   git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
   git branch -M main
   git push -u origin main
   ```

## Raspberry Pi workflow (later)

Once the Pi is cleaned and has Python + Git + Chromium:

1. Clone the repo on the Pi (once):
   ```bash
   git clone https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
   ```

2. Update and redeploy when code changes:
   ```bash
   cd /path/to/personal-assistant-dashboard
   git pull
   # then restart the systemd service or app process
   ```

We will extend this document as we add the scheduler, database models, and deployment scripts.
