import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

# Import the core logic
from calculator_core import evaluate_expression, groq_math_query

# Load .env (Hugging Face Secrets will also be picked up via environment variables)
load_dotenv()

app = FastAPI(title="Smart Calculator - Hugging Face")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
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
        # On HF Spaces, if user doesn't provide a key, it will use GROQ_API_KEY from Secrets
        return groq_math_query(req.question, api_key=req.api_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

if __name__ == "__main__":
    import uvicorn
    # HF Spaces expects the app to run on port 7860 by default
    uvicorn.run(app, host="0.0.0.0", port=7860)
