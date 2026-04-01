"""
Inference Script — CodeReviewEnv
MANDATORY: Named inference.py, placed in root, uses OpenAI client.
"""
import os
import textwrap
from typing import Optional
from openai import OpenAI
from env import CodeReviewEnv, CodeReviewAction

API_BASE_URL: str = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY: Optional[str] = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME: Optional[str] = os.getenv("MODEL_NAME")
TEMPERATURE = 0.2
MAX_TOKENS = 800

SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert Python code reviewer.
    List every bug, security issue, or code smell you find.
    Reference the specific line or construct with the problem.
    Explain WHY each issue is a problem.
    Suggest a concrete fix for each issue.
    Format as a numbered list. Start directly with issue #1.
""").strip()


def run_task(client: OpenAI, task_id: str) -> float:
    env = CodeReviewEnv(task_id=task_id)
    result = env.reset()
    obs = result["observation"]
    print(f"\n{'='*50}\n  TASK: {task_id.upper()} | Goal: {obs.goal}\n{'='*50}")
    cumulative_score = 0.0

    for step in range(1, obs.max_steps + 1):
        if result["done"]:
            break
        user_prompt = textwrap.dedent(f"""
            Task: {task_id.upper()} | Goal: {obs.goal}
            Instructions: {obs.instructions}
            Step {obs.step_number}/{obs.max_steps} | Score so far: {obs.score_so_far:.2f}
            {f"Previous review: {obs.last_review[:200]}..." if obs.last_review else ""}

            --- CODE ---
            {obs.code_snippet}
            --- END CODE ---

            Write a thorough code review identifying all issues.
        """).strip()

        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )
            review_text = completion.choices[0].message.content or ""
        except Exception as exc:
            print(f"  [Step {step}] LLM call failed: {exc}")
            break

        result = env.step(CodeReviewAction(review_text=review_text))
        obs = result["observation"]
        cumulative_score = result["info"]["cumulative_reward"]
        print(f"  Step {step}: reward={result['reward']:+.4f} | cumulative={cumulative_score:.4f}")
        print(f"    Feedback: {result['info'].get('grader_feedback', '')}")
        if cumulative_score >= 0.99:
            print("  Perfect score!")
            break

    print(f"\n  FINAL [{task_id}]: {cumulative_score:.4f}")
    env.close()
    return cumulative_score


def main() -> None:
    if not API_KEY:
        raise EnvironmentError("HF_TOKEN or API_KEY environment variable is not set.")
    if not MODEL_NAME:
        raise EnvironmentError("MODEL_NAME environment variable is not set.")

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    scores = {}
    for task_id in ["easy", "medium", "hard"]:
        scores[task_id] = run_task(client, task_id)

    print(f"\n{'='*50}\n  BASELINE SCORES\n{'='*50}")
    for t, s in scores.items():
        print(f"  {t:<10} {s:.4f}")
    print(f"  {'OVERALL':<10} {sum(scores.values()) / 3:.4f}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()