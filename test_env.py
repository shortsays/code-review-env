from env import CodeReviewEnv, CodeReviewAction

def test_task(task_id: str, review: str):
    env = CodeReviewEnv(task_id=task_id)
    env.reset()
    result = env.step(CodeReviewAction(review_text=review))
    print(f"[{task_id}] reward={result['reward']:.4f} | done={result['done']}")
    print(f"  Breakdown: {result['info']['breakdown']}")
    print(f"  Feedback:  {result['info']['grader_feedback']}\n")
    env.close()

if __name__ == "__main__":
    test_task("easy",
        "Line 3 has a division by zero error. Add a guard: if b == 0 raise ValueError. Use try/except ZeroDivisionError.")

    test_task("medium",
        "range(1, ...) skips index 0 — off-by-one bug. scores.sort() mutates the input list. Empty list crashes. n=0 causes divide by zero. No isinstance validation.")

    test_task("hard",
        "SQL injection via f-string — use ? parameterized queries. Password stored in plaintext — use bcrypt. Missing authorization check on update_user_email — IDOR vulnerability. No try/except around sqlite3.connect — use context manager. SELECT * exposes sensitive columns.")

    print("All tests complete!")