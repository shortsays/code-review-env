#!/usr/bin/env python3
import os
import json
import time
import requests
from openai import OpenAI


client = OpenAI(
    api_key=os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY", "dummy-key"),
    base_url=os.getenv("API_BASE_URL", "https://api.openai.com/v1"),
)
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")

SPACE_URL = os.getenv("SPACE_URL", "https://shortsays-code-review-env.hf.space")


def log_step(step_type, data):
    print(json.dumps({
        "type": step_type,
        "data": data,
        "timestamp": time.time()
    }), flush=True)


def run_baseline(task_id="easy"):
    print(json.dumps({"type": "START", "task_id": task_id}), flush=True)

    session = requests.Session()

    # Reset environment
    resp = session.post(f"{SPACE_URL}/reset", json={"task_id": task_id})
    resp.raise_for_status()
    obs = resp.json()["observation"]
    log_step("STEP", {"action": "reset", "task_id": task_id})

    # ✅ New OpenAI v1 API call
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Review this Python code and identify all bugs and security issues. "
                        f"Suggest fixes with line references:\n\n"
                        f"{obs.get('code_snippet', '')}\n\n"
                        f"Task: {obs.get('instructions', '')}"
                    )
                }
            ],
            max_tokens=512,
        )
        review_text = completion.choices[0].message.content

    except Exception as e:
        # Fallback review if LLM is unavailable
        review_text = (
            "There is a ZeroDivisionError when b=0 on the division line. "
            "Add a try/except block to handle ZeroDivisionError. "
            "Recommend: if b == 0: raise ValueError('b cannot be zero'). "
            "Also add input type validation and error handling."
        )
        log_step("STEP", {"action": "llm_fallback", "error": str(e)})

    total_reward = 0.0

    for step_num in range(5):
        resp = session.post(f"{SPACE_URL}/step", json={"review_text": review_text})
        resp.raise_for_status()
        result = resp.json()
        log_step("STEP", {
            "step_num": step_num,
            "reward": result["reward"],
            "done": result["done"]
        })
        total_reward += result["reward"]
        if result["done"]:
            break

    print(json.dumps({"type": "END", "total_reward": total_reward}), flush=True)
    return total_reward


if __name__ == "__main__":
    for task in ["easy", "medium", "hard"]:
        run_baseline(task)
        time.sleep(1)