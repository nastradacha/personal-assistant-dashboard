import json
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from ..ai_client import call_deepseek


def _extract_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        parts = stripped.split("```", 2)
        if len(parts) >= 3:
            stripped = parts[1] if parts[0] == "" else parts[2]
        stripped = stripped.strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and start < end:
        return stripped[start : end + 1]
    return stripped


async def generate_template_suggestions(free_text: str) -> List[Dict[str, Any]]:
    system_prompt = (
        "You are helping design recurring schedule templates for a personal assistant dashboard. "
        "Given a natural language description of how the user wants to structure their days, "
        "propose between 3 and 7 task templates. Each template should have: "
        "name (short, action-oriented), category (e.g. work, health, chores, dog, sleep), "
        "default_duration_minutes (integer), recurrence_pattern (e.g. daily, weekdays, weekends, or custom), "
        "preferred_time_window (e.g. '07:00-09:00' or 'evenings'), default_alert_style (one of: "
        "'visual_then_alarm', 'visual_only', 'alarm_only'), and enabled (boolean). "
        "Respond ONLY with a JSON object of the form {\"templates\":[...]} and no extra text."
    )
    user_prompt = (
        "User description of desired routine:\n" f"{free_text.strip()}\n\n" "Return JSON now."
    )
    raw = await call_deepseek(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=700,
    )
    try:
        json_text = _extract_json_object(raw)
        data = json.loads(json_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI response could not be parsed as JSON") from exc
    templates_data = data.get("templates")
    if not isinstance(templates_data, list):
        raise HTTPException(status_code=502, detail="AI response missing 'templates' list")
    return templates_data


async def refine_template(template: Dict[str, Any], instruction: Optional[str] = None) -> Dict[str, Any]:
    system_prompt = (
        "You are helping refine a single recurring schedule template for a personal assistant dashboard. "
        "Given the current template fields and an optional user instruction, propose a slightly improved version. "
        "Keep the template broadly similar (same general purpose and category), but you may adjust "
        "default_duration_minutes, recurrence_pattern, preferred_time_window, default_alert_style, and enabled. "
        "When the user provides an instruction, you MUST change at least one field versus the original template. "
        "If the user mentions tone (e.g. gentler, firmer, more motivating), interpret this by changing the task name "
        "and/or choosing a different default_alert_style that matches that tone. "
        "Respond ONLY with a JSON object of the form {\"template\": {...}} matching the existing schema and no extra text."
    )
    user_parts = [
        "Current template as JSON:",
        json.dumps(template, ensure_ascii=False),
    ]
    if instruction:
        user_parts.append("\nUser instruction for refinement:\n" + instruction.strip())
    user_prompt = "\n".join(user_parts)
    raw = await call_deepseek(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=400,
    )
    try:
        json_text = _extract_json_object(raw)
        data = json.loads(json_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI response could not be parsed as JSON") from exc
    template_data = data.get("template")
    if not isinstance(template_data, dict):
        raise HTTPException(status_code=502, detail="AI response missing 'template' object")
    return template_data


async def generate_now_suggestion(context: Dict[str, Any]) -> str:
    system_prompt = (
        "You are a gentle focus assistant helping the user decide what to do right now based on their schedule "
        "and recent behavior. Return a single, concise suggestion (1–2 sentences, maximum about 50 words). "
        "Be concrete but non-judgmental. If there is no schedule, suggest a simple, healthy default like planning or rest. "
        "Respond ONLY with a JSON object of the form {\"suggestion\": \"...\"} and no extra text."
    )
    user_prompt = (
        "Here is the current context for the user's day as JSON:\n"
        + json.dumps(context, default=str)
        + "\n\nBased on this, what should the user focus on right now?"
    )
    raw = await call_deepseek(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=160,
    )
    try:
        json_text = _extract_json_object(raw)
        data = json.loads(json_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI response could not be parsed as JSON") from exc
    suggestion = data.get("suggestion")
    if not isinstance(suggestion, str) or not suggestion.strip():
        raise HTTPException(status_code=502, detail="AI response missing 'suggestion' text")
    return suggestion.strip()


async def generate_alert_wording(
    category: str,
    tone: str,
    max_length: int,
    count: int,
) -> List[str]:
    system_prompt = (
        "You are generating short alert messages for a single user's personal assistant. "
        "Each message will be used as the main text of an alert for a recurring task. "
        "Given a task category and a desired tone, propose several alternative alert texts. "
        "Each option must be a single sentence fragment or sentence, no longer than the provided character limit. "
        "Avoid numbered lists or bullet markers; return only the texts. "
        "Respond ONLY with a JSON object of the form {\"options\":[...]} and no extra text."
    )
    user_prompt = (
        "Category: "
        + category
        + "\nTone: "
        + tone
        + "\nMaximum length (characters) for each option: "
        + str(max_length)
        + "\nNumber of options to return: "
        + str(count)
        + "\n\nReturn JSON now."
    )
    raw = await call_deepseek(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=300,
    )
    try:
        json_text = _extract_json_object(raw)
        data = json.loads(json_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI response could not be parsed as JSON") from exc
    options_raw = data.get("options") or []
    options: List[str] = []
    if isinstance(options_raw, list):
        for item in options_raw:
            text = str(item).strip()
            if not text:
                continue
            if len(text) > max_length:
                text = text[: max_length - 1].rstrip() + "…"
            options.append(text)
    if not options:
        raise HTTPException(status_code=502, detail="AI did not return any alert text options")
    return options


async def summarize_history(summary: Dict[str, Any]) -> Dict[str, List[str]]:
    system_prompt = (
        "You are analyzing a single user's alert interaction patterns for a personal assistant dashboard. "
        "You receive ONLY aggregated counts of interactions (no raw logs). From this data you must produce: "
        "(1) 3-5 bullet insights summarizing behavior patterns, and (2) 2-3 concrete, actionable recommendations "
        "about how the user might adjust their schedule or alerts. Keep the tone practical and non-judgmental. "
        "Each insight and recommendation should be a short sentence. "
        "Respond ONLY with a JSON object of the form {\"insights\":[...],\"recommendations\":[...]} and no extra text."
    )
    user_prompt = (
        "Here is aggregated interaction history for one user over a selected date range, as JSON:\n"
        + json.dumps(summary, default=str)
        + "\n\nPlease infer patterns and suggestions based on this summary."
    )
    raw = await call_deepseek(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=400,
    )
    try:
        json_text = _extract_json_object(raw)
        data = json.loads(json_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI response could not be parsed as JSON") from exc
    insights_raw = data.get("insights") or []
    recs_raw = data.get("recommendations") or []
    insights: List[str] = []
    recommendations: List[str] = []
    if isinstance(insights_raw, list):
        for item in insights_raw:
            text = str(item).strip()
            if text:
                insights.append(text)
    if isinstance(recs_raw, list):
        for item in recs_raw:
            text = str(item).strip()
            if text:
                recommendations.append(text)
    if not insights and not recommendations:
        insights = [
            "The AI could not derive clear patterns from the aggregated data, but you can still review your history manually.",
        ]
    return {"insights": insights, "recommendations": recommendations}


async def summarize_notes(summary: Dict[str, Any]) -> Dict[str, List[str]]:
    system_prompt = (
        "You are analyzing a single user's short reasons for snoozing or skipping tasks. "
        "You receive only brief one-sentence notes, with the task category and time. "
        "From this data you must produce: (1) a small list of recurring patterns in the reasons, "
        "and (2) 2-3 concrete schedule or alert adjustments that might help. "
        "Keep the tone practical and compassionate. Each pattern and recommendation should be a short sentence. "
        "Respond ONLY with a JSON object of the form {\"patterns\":[...],\"recommendations\":[...]} and no extra text."
    )
    user_prompt = (
        "Here are short notes about why the user snoozed or skipped tasks over a selected date range, as JSON:\n"
        + json.dumps(summary, default=str)
        + "\n\nPlease infer recurring themes and suggest helpful adjustments."
    )
    raw = await call_deepseek(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=320,
    )
    try:
        json_text = _extract_json_object(raw)
        data = json.loads(json_text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI response could not be parsed as JSON") from exc
    patterns_raw = data.get("patterns") or []
    recs_raw = data.get("recommendations") or []
    patterns: List[str] = []
    recommendations: List[str] = []
    if isinstance(patterns_raw, list):
        for item in patterns_raw:
            text = str(item).strip()
            if text:
                patterns.append(text)
    if isinstance(recs_raw, list):
        for item in recs_raw:
            text = str(item).strip()
            if text:
                recommendations.append(text)
    if not patterns and not recommendations:
        patterns = [
            "The AI could not derive clear patterns from the available notes, but you can still review them manually.",
        ]
    return {"patterns": patterns, "recommendations": recommendations}
