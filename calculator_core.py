"""Shared calculator logic (math evaluation + Groq AI) used by desktop and web versions."""

from __future__ import annotations

import math
import os
from typing import Any, Dict, List, Optional

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

def get_safe_ns(mode='deg'):
    """Get a safe namespace for evaluation, wrapping trig functions if in deg mode."""
    ns = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    ns.update({"abs": abs, "round": round, "pow": pow})

    if mode == 'deg':
        def sin_deg(x): return math.sin(math.radians(x))
        def cos_deg(x): return math.cos(math.radians(x))
        def tan_deg(x):
            # Handle tan(90) which is undefined in degrees
            # Due to float precision x % 180 == 90 is safest check
            if abs(x % 180) == 90:
                raise ValueError("Tangent is undefined for 90 or 270 degrees.")
            return math.tan(math.radians(x))
        
        ns.update({"sin": sin_deg, "cos": cos_deg, "tan": tan_deg})
    
    return ns


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
        .replace("log(", "log10(") # Use log10 for 'log' in calculator context
    )


def safe_eval(expr: str, mode: str = 'deg') -> Any:
    """Evaluate a math expression safely without exposing builtins."""
    expr = normalize_expr(expr)
    safe_ns = get_safe_ns(mode)
    return eval(expr, {"__builtins__": {}}, safe_ns)  # noqa: S307


def evaluate_expression(expr: str, mode: str = 'deg') -> Dict[str, Any]:
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
        result = safe_eval(expr, mode=mode)
        if isinstance(result, float):
            result = round(result, 10)
            if result == int(result):
                result = int(result)

        return {"expr": expr, "result": result}
    except ZeroDivisionError:
        return {"error": "Division by zero."}
    except Exception as exc:
        return {"error": f"Syntax error: {str(exc)}"}


def groq_math_query(
    question: str, 
    api_key: Optional[str] = None, 
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """Ask Groq a math question and return the response with memory support."""

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
        "You are an expert mathematician with advanced logical thinking and problem-solving skills. "
        "When users ask questions, provide precise, logically structured answers. "
        "Use formal mathematical notation and step-by-step reasoning where appropriate. "
        "Be concise but thorough. Focus on providing the most accurate and elegant solution possible. "
        "Keep answers short (≤6 lines). Use plain text (no markdown headers)."
    )

    # Build message list
    messages = [{"role": "system", "content": SYSTEM}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": question})

    raw_resp = client.chat.completions.with_raw_response.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
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
