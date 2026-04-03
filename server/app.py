from __future__ import annotations
import os
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from env import CodeReviewEnv, CodeReviewAction

app = FastAPI(title="CodeReviewEnv", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env: Optional[CodeReviewEnv] = None


class ResetRequest(BaseModel):
    task_id: Optional[str] = "easy"


class StepRequest(BaseModel):
    review_text: str


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.post("/reset")
def reset(req: ResetRequest = Body(default=ResetRequest())):
    global env
    task_id = req.task_id or "easy"
    if task_id not in ["easy", "medium", "hard"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task_id '{task_id}'. Use easy/medium/hard."
        )
    env = CodeReviewEnv(task_id=task_id)
    result = env.reset()
    return {
        "observation": result["observation"].model_dump(),
        "done": False,
        "reward": 0.0
    }


@app.post("/step")
def step(req: StepRequest = Body(...)):
    global env
    if env is None:
        raise HTTPException(
            status_code=400,
            detail="Environment not initialized. Call /reset first."
        )
    result = env.step(CodeReviewAction(review_text=req.review_text))
    return {
        "observation": result["observation"].model_dump(),
        "reward": result["reward"],
        "done": result["done"],
        "info": result["info"],
    }


@app.get("/state")
def state():
    global env
    if env is None:
        raise HTTPException(
            status_code=400,
            detail="Call /reset first."
        )
    return env.state()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "env": "CodeReviewEnv",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 7860)))