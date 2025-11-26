from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Personal Assistant Dashboard")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    return """<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Personal Assistant Dashboard</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            background: #050816;
            color: #f9fafb;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        .container {
            text-align: center;
        }
        .title {
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
        }
        .subtitle {
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class=\"container\">
        <div class=\"title\">Personal Assistant Dashboard</div>
        <div class=\"subtitle\">Backend is running  skeleton phase</div>
    </div>
</body>
</html>"""
