import json
import os
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
import httpx
from fastapi import HTTPException


# Load environment variables from .env in the project root (if present),
# resolving relative to this file so it works regardless of the cwd.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

AI_API_URL = os.getenv("AI_DESCRIPTION_API_URL", "https://api.deepseek.com/chat/completions")
AI_MODEL_NAME = os.getenv("AI_DESCRIPTION_MODEL", "deepseek-chat")
AI_API_KEY = os.getenv("AI_DESCRIPTION_API_KEY")
AI_SSL_VERIFY = os.getenv("AI_SSL_VERIFY", "true").lower() != "false"


async def call_deepseek(messages: List[Dict[str, str]], *, max_tokens: int = 512) -> str:
    """Call the DeepSeek chat completion API and return the assistant message content.

    Messages should be an array of {"role": "system"|"user"|"assistant", "content": "..."}.
    """
    if not AI_API_KEY:
        raise HTTPException(status_code=500, detail="AI API key is not configured")

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": AI_MODEL_NAME,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.4,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, verify=AI_SSL_VERIFY) as client:
            resp = await client.post(AI_API_URL, headers=headers, json=payload)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"AI service request failed: {exc}") from exc

    if resp.status_code != 200:
        detail = resp.text[:500]
        raise HTTPException(status_code=502, detail=f"AI service error: {detail}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="AI service returned unexpected format") from exc
