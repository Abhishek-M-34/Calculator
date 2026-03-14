"""Web API layer for the Smart Calculator.

Run with:
  uvicorn server:app --reload

Endpoints:
  POST /api/calc  - Evaluate a math expression
  POST /api/ai    - Ask Groq (requires GROQ_API_KEY env var or api_key in payload)
"""

from __future__ import annotations

from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from calculator_core import evaluate_expression, groq_math_query

# Load `.env` from current directory (optional local development convenience)
load_dotenv()

app = FastAPI(title="Smart Calculator API")

# Serve the frontend from /static
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=FileResponse)
def root():
    return FileResponse("static/index.html")


class CalcRequest(BaseModel):
    expr: str


class AiRequest(BaseModel):
    question: str
    api_key: Optional[str] = None


@app.post("/api/calc")
def calc(req: CalcRequest):
    result = evaluate_expression(req.expr)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/ai")
def ai(req: AiRequest):
    try:
        return groq_math_query(req.question, api_key=req.api_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
