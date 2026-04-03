---
title: CodeReviewEnv
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# CodeReviewEnv 🚀

[![Docker](https://img.shields.io/badge/Docker-Success-brightgreen)](Dockerfile)
[![FastAPI](https://img.shields.io/badge/FastAPI-v1.0-blue)](server.py)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Ready-green)](openenv.yaml)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Space-yellow)](https://huggingface.co/spaces/shortsays/code-review-env)

**CodeReviewEnv** is a production-ready OpenEnv environment for training AI code review agents. Agents receive Python code snippets with deliberate bugs and security issues, and must identify problems through structured reviews scored by a deterministic grader.

## 🎯 Features

- **3 Difficulty Levels**: Easy (single bug), Medium (multiple bugs), Hard (security review)
- **Deterministic Grading**: Keyword-based scoring with detailed breakdown and feedback
- **Standard OpenEnv API**: `/reset`, `/step`, `/state`, `/health`
- **Live on Hugging Face**: Deployed at [shortsays/code-review-env](https://huggingface.co/spaces/shortsays/code-review-env)
- **Baseline Agent**: `inference.py` with OpenAI client + structured START/STEP/END logging

## 🏗️ Architecture
env.py → Core environment, 3 tasks, grader logic
server.py → FastAPI app with all OpenEnv endpoints
inference.py → Baseline agent using OpenAI client
Dockerfile → Container setup for Hugging Face Spaces
openenv.yaml → Environment specification (OpenEnv format)
pyproject.toml → Python project metadata
requirements.txt → Python dependencies
test_env.py → Local validation tests
validate-submission.sh → Submission validator script


## 🏗️ Architecture

| File | Description |
|------|-------------|
| `env.py` | Core environment, 3 tasks, grader logic |
| `server.py` | FastAPI app with all OpenEnv endpoints |
| `inference.py` | Baseline agent using OpenAI client |
| `Dockerfile` | Container setup for Hugging Face Spaces |
| `openenv.yaml` | Environment specification (OpenEnv format) |
| `pyproject.toml` | Python project metadata |
| `requirements.txt` | Python dependencies |
| `test_env.py` | Local validation tests |
| `validate-submission.sh` | Submission validator script |

### Example Usage

```bash
# Reset environment
curl -X POST https://shortsays-code-review-env.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy"}'

# Submit a review
curl -X POST https://shortsays-code-review-env.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"review_text": "There is a ZeroDivisionError when b=0. Add a try/except or guard clause."}'
```

## 🧪 Tasks

| Task | Description | Bugs to Find | Max Steps | Max Score |
|------|-------------|--------------|-----------|-----------|
| **Easy** | Short function with one obvious bug | ZeroDivisionError | 3 | 1.0 |
| **Medium** | Function with multiple subtle bugs | Off-by-one, mutation, edge cases | 5 | 1.0 |
| **Hard** | Security review of auth + DB code | SQL injection, plaintext password, missing auth, connection handling | 8 | 1.0 |

## 📊 Grading

Reviews are scored on:

- **Issue Detection** — keyword matching against expected issues (base score)
- **Review Length** — reviews > 200 chars get a small bonus (+0.05 max)
- **Fix Suggestions** — mentioning fix/replace/recommend adds +0.05
- **Line References** — mentioning line/function adds +0.05
- **Max Score**: 1.0 (capped)

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_BASE_URL` | No | `https://api.openai.com/v1` | OpenAI-compatible API base URL |
| `MODEL_NAME` | No | `gpt-3.5-turbo` | Model name for inference |
| `HF_TOKEN` | No | None (no default) | Hugging Face token |
| `LOCAL_IMAGE_NAME` | No | None | Docker image name (if using from_docker_image) |

## 🚀 Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn server:app --host 0.0.0.0 --port 7860

# Open Swagger UI
# http://localhost:7860/docs
```

## 🐳 Docker

```bash
# Build image
docker build -t code-review-env .

# Run container
docker run -p 7860:7860 code-review-env

# Open http://localhost:7860/docs
```

## 🤖 Run Baseline Agent

```bash
# Set env vars
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-3.5-turbo
export HF_TOKEN=your_token_here

# Run inference
python inference.py
```

Stdout follows the required structured format:

```json
{"type": "START", "task_id": "easy"}
{"type": "STEP", "step_num": 0, "reward": 0.45, "done": false}
{"type": "END", "total_reward": 0.85}
```

## ✅ Pre-Submission Checklist

- ✅ Read the sample `inference.py` and followed it strictly
- ✅ Environment variables present in `inference.py` (`API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`)
- ✅ Defaults set only for `API_BASE_URL` and `MODEL_NAME` (not `HF_TOKEN`)
- ✅ All LLM calls use the OpenAI client configured via these variables
- ✅ Stdout logs follow the required structured format (START/STEP/END) exactly

## 🔗 Links

- **Live Space**: https://huggingface.co/spaces/shortsays/code-review-env
- **Swagger UI**: https://shortsays-code-review-env.hf.space/docs
- **GitHub Repo**: https://github.com/shortsays/code-review-env

---

*Built for Scaler × OpenEnv Hackathon 2026 · by shortsays*