"""
Minimal client for any OpenAI-compatible chat-completions API.

Works with Google Gemini (default, has a free tier), OpenAI, Groq, OpenRouter,
Ollama, etc. — you only change AI_BASE_URL / AI_MODEL / AI_API_KEY in .env.

Uses only the standard library (urllib), so no extra dependency is needed.
If AI_API_KEY is empty or the call fails, `ask_json` returns None and the
caller falls back to rule-based results, so the app keeps working offline.
"""

import json
import logging
import re
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


def ai_enabled() -> bool:
    return bool(getattr(settings, "AI_API_KEY", ""))


def _extract_json(text: str):
    """Models sometimes wrap JSON in ```json fences or add text around it."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def ask_json(system_prompt: str, user_prompt: str, *, temperature: float = 0.4):
    """Sends a chat request and returns the parsed JSON object, or None on any failure."""
    if not ai_enabled():
        return None

    url = settings.AI_BASE_URL.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.AI_MODEL,
        "temperature": temperature,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
                + "\nResponde ÚNICAMENTE con un objeto JSON válido, sin texto adicional.",
            },
            {"role": "user", "content": user_prompt},
        ],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.AI_API_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=settings.AI_TIMEOUT_SECONDS) as res:
            body = json.loads(res.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        data = _extract_json(content)
        return data if isinstance(data, dict) else None
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError) as exc:
        logger.warning("AI request failed, using fallback: %s", exc)
        return None
