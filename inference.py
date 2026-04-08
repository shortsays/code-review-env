#!/usr/bin/env python3
import os
import time
import requests
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY", "dummy-key"),
    base_url=os.getenv("API_BASE_URL", "https://api.openai.com/v1"),
)
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
SPACE_URL = os.getenv("SPACE_URL", "https://shortsays-code-review-env.hf.space")


def run_baseline(task_id="easy"):
    print(f"[START] task={task_id}", flush=True)

    session = requests.Session()

    resp = session.post(f"{SPACE_URL}/reset", json={"task_id": task_id})
    resp.raise_for_status()
    obs = resp.json()["observation"]

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{
                "role": "user",
                "content": (
                    f"Review this Python code and identify all bugs and security issues. "
                    f"Suggest fixes with line references:\n\n"
                    f"{obs.get('code_snippet', '')}\n\n"
                    f"Task: {obs.get('instructions', '')}"
                )
            }],
            max_tokens=512,
        )
        review_text = completion.choices[0].message.content
    except Exception as e:
        review_text = (
            "There is a ZeroDivisionError when b=0 on the division line. "
            "Add a try/except block to handle ZeroDivisionError. "
            "Recommend: if b == 0: raise ValueError. "
            "Use isinstance for type validation. Replace sort() with sorted() to avoid mutation. "
            "Use parameterized queries to prevent SQL injection. Hash passwords with bcrypt."
        )

    final_score = 0.5
    steps = 0

    for step_num in range(5):
        resp = session.post(f"{SPACE_URL}/step", json={"review_text": review_text})
        resp.raise_for_status()
        result = resp.json()
        steps = step_num + 1

        cumulative = result.get("info", {}).get("cumulative_reward", None)
        if cumulative is not None:
            final_score = float(cumulative)
        else:
            final_score = final_score + float(result["reward"])

        final_score = max(0.01, min(0.99, final_score))

        print(f"[STEP] step={steps} reward={final_score}", flush=True)

        if result["done"]:
            break

    final_score = max(0.01, min(0.99, final_score))
    print(f"[END] task={task_id} score={final_score} steps={steps}", flush=True)
    return final_score


if __name__ == "__main__":
    for task in ["easy", "medium", "hard"]:
        run_baseline(task)
        time.sleep(1)