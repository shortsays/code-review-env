---
title: CodeReviewEnv
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# CodeReviewEnv

CodeReviewEnv is a compact OpenEnv-style code review environment built with FastAPI. It gives an agent a Python code snippet, asks for a review, and scores the review based on whether it identifies the intended issues.

## What it does

- Presents three review tasks: easy, medium, and hard.
- Returns a structured observation with the current code snippet and instructions.
- Scores reviews deterministically using keyword-based grading.
- Exposes a simple HTTP API for reset, step, state, and health checks.
- Ships as a Docker Space for easy deployment on Hugging Face.

## Endpoints

- `POST /reset` — start a task episode.
- `POST /step` — submit a code review.
- `GET /state` — inspect current environment state.
- `GET /health` — health check for deployment.

## Local run

```powershell
uvicorn server:app --host 0.0.0.0 --port 7860
```

Open:

```text
http://127.0.0.1:7860/docs
```

## Docker

```powershell
docker build -t code-review-env .
docker run -p 7860:7860 code-review-env
```

## Files

- `env.py` — environment, tasks, and grading logic.
- `server.py` — FastAPI app and HTTP routes.
- `inference.py` — baseline script for testing the environment.
- `openenv.yaml` — metadata/spec for the environment.
- `test_env.py` — local validation tests.
- `Dockerfile` — container setup for Hugging Face Spaces.

## Notes

This project is designed to be simple, deterministic, and easy to validate locally before pushing to Hugging Face Spaces.