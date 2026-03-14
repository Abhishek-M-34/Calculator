"""Shared calculator logic (math evaluation + Groq AI) used by desktop and web versions."""

from __future__ import annotations

import math
import os
from typing import Any, Dict, Optional

# ── Groq SDK (optional) ───────────────────────────────────────────────────────
GROQ_IMPORT_ERROR = None
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError as e:
    GROQ_AVAILABLE = False
    GROQ_IMPORT_ERROR = str(e)
except Exception as e:
    GROQ_AVAILABLE = False
    GROQ_IMPORT_ERROR = f"Unexpected error: {str(e)}"

# ── Safe math evaluator ───────────────────────────────────────────────────────
_SAFE_NS = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
_SAFE_NS.update({"abs": abs, "round": round, "pow": pow})


def normalize_expr(expr: str) -> str:
    """Normalize a user expression to Python-compatible math syntax."""
    # Common user-friendly tokens used by the UI
    return (
        expr
        .replace("÷", "/")
        .replace("×", "*")
        .replace("−", "-")
        .replace("π", str(math.pi))
        .replace("^", "**")
        .replace("ln(", "log(")
    )


def safe_eval(expr: str) -> Any:
    """Evaluate a math expression safely without exposing builtins."""
    expr = normalize_expr(expr)
    return eval(expr, {"__builtins__": {}}, _SAFE_NS)  # noqa: S307


def evaluate_expression(expr: str) -> Dict[str, Any]:
    """Evaluate a math expression and return a standardized result dict."""

    expr = (expr or "").strip()
    if not expr:
        return {"error": "Expression is empty."}

    # Auto-close brackets if user forgets
    open_brackets = expr.count("(")
    close_brackets = expr.count(")")
    if open_brackets > close_brackets:
        expr += ")" * (open_brackets - close_brackets)

    try:
        result = safe_eval(expr)
        if isinstance(result, float):
            result = round(result, 10)
            if result == int(result):
                result = int(result)

        return {"expr": expr, "result": result}
    except ZeroDivisionError:
        return {"error": "Division by zero."}
    except Exception as exc:
        return {"error": f"Syntax error: {str(exc)}"}


def groq_math_query(question: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Ask Groq a math question and return the response.

    The API key may be provided explicitly, or by setting the
    `GROQ_API_KEY` environment variable.

    If the Groq SDK is not installed, we return a friendly message rather than
    raising an exception so the UI can show a helpful note.
    """

    if not GROQ_AVAILABLE:
        return {
            "question": question,
            "answer": (
                f"Groq SDK issue on server: {GROQ_IMPORT_ERROR or 'Not installed'}. "
                "Please run: pip install groq"
            ),
            "remaining_requests": 0,
        }

    api_key = api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Groq API key is required (set GROQ_API_KEY or pass api_key).")

    client = Groq(api_key=api_key)

    SYSTEM = (
        "You are a concise math assistant embedded in a calculator app. "
        "When the user asks a math or calculation question, show the result clearly. "
        "If applicable, also show the formula or steps briefly. "
        "Keep answers short (≤6 lines). Use plain text, no markdown headers."
    )

    raw_resp = client.chat.completions.with_raw_response.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": question},
        ],
        max_tokens=400,
        temperature=0.3,
    )

    parsed = raw_resp.parse()
    answer = parsed.choices[0].message.content.strip()

    remaining = (
        raw_resp.headers.get("x-ratelimit-remaining-requests-today")
        or raw_resp.headers.get("x-ratelimit-remaining-requests")
        or "Unknown"
    )

    return {
        "question": question,
        "answer": answer,
        "remaining_requests": remaining,
    }
