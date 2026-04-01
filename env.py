from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class CodeReviewObservation(BaseModel):
    task_id: str = Field(description="Current task identifier: easy | medium | hard")
    code_snippet: str = Field(description="Python code snippet to review")
    instructions: str = Field(description="What the agent should look for")
    step_number: int = Field(description="Current step within the episode")
    max_steps: int = Field(description="Maximum steps allowed per episode")
    last_review: Optional[str] = Field(default=None, description="Agent's last review text")
    last_action_error: Optional[str] = Field(default=None, description="Error from last action if any")
    score_so_far: float = Field(default=0.0, description="Cumulative score in this episode")
    goal: str = Field(description="Episode goal description")


class CodeReviewAction(BaseModel):
    review_text: str = Field(description="The agent's code review text")


class CodeReviewReward(BaseModel):
    value: float = Field(description="Reward for this step (0.0 - 1.0)")
    breakdown: dict[str, float] = Field(description="Score breakdown by category")
    feedback: str = Field(description="Grader feedback on the review")


TASKS = {
    "easy": {
        "description": "Identify the single obvious bug in this short Python function.",
        "code": '''\
def divide_numbers(a, b):
    """Divide a by b and return the result."""
    result = a / b
    return result

print(divide_numbers(10, 0))
print(divide_numbers(10, 2))
''',
        "expected_issues": {
            "division_by_zero": ["division by zero", "zerodivisionerror", "b == 0", "zero check", "divide by zero"],
            "no_error_handling": ["try", "except", "raise", "error handling", "guard"],
        },
        "goal": "Find the ZeroDivisionError bug and suggest a fix.",
        "max_steps": 3,
    },
    "medium": {
        "description": "Find ALL bugs: off-by-one errors, mutation bug, edge cases, and type safety.",
        "code": '''\
def get_top_scores(scores, n):
    """Return the top n scores from a list."""
    scores.sort()
    top = scores[len(scores) - n:]
    total = 0
    for i in range(1, len(top)):
        total = total + top[i]
    average = total / n
    return top, average

data = [55, 92, 78, 45, 88, 60, 95]
print(get_top_scores(data, 3))
print(get_top_scores([], 3))
print(get_top_scores(data, 0))
''',
        "expected_issues": {
            "off_by_one": ["range(1", "off by one", "index 0", "skips first", "should start at 0"],
            "mutates_input": ["sort()", "in-place", "mutates", "modifies original", "sorted("],
            "empty_list": ["empty", "len(scores) == 0", "edge case", "[]"],
            "zero_n": ["n == 0", "zero division", "n=0", "divide by n"],
            "no_type_check": ["type check", "not a list", "isinstance", "validation"],
        },
        "goal": "Find off-by-one error, mutation bug, and edge cases (empty list, n=0).",
        "max_steps": 5,
    },
    "hard": {
        "description": "Security review: find SQL injection, auth flaws, input validation gaps, logic errors.",
        "code": '''\
import sqlite3

def authenticate_user(username, password, db_path="users.db"):
    """Authenticate user and return their data if credentials match."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username=\'{username}\' AND password=\'{password}\'"
    cursor.execute(query)
    user = cursor.fetchone()
    if user:
        conn.close()
        return {"authenticated": True, "user_id": user[0], "role": user[2]}
    conn.close()
    return {"authenticated": False}

def update_user_email(user_id, new_email, requestor_id):
    """Update a user\'s email address."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET email=\'{new_email}\' WHERE id={user_id}")
    conn.commit()
    conn.close()
    return True
''',
        "expected_issues": {
            "sql_injection": ["sql injection", "f-string", "parameterized", "? placeholder", "format string", "string interpolation"],
            "plaintext_password": ["plaintext", "plain text", "hash", "bcrypt", "argon2", "sha", "password storage"],
            "missing_authorization": ["authorization", "authorisation", "access control", "requestor_id", "privilege", "idor", "insecure direct object"],
            "no_connection_error_handling": ["try", "except", "finally", "connection error", "context manager", "with sqlite3"],
            "wildcard_select": ["select *", "wildcard", "specific columns", "expose", "sensitive fields"],
        },
        "goal": "Find SQL injection, plaintext password, missing authorization, and connection handling flaws.",
        "max_steps": 8,
    },
}


def grade_review(task_id: str, review_text: str) -> CodeReviewReward:
    task = TASKS[task_id]
    expected = task["expected_issues"]
    review_lower = review_text.lower()
    breakdown: dict[str, float] = {}
    found = 0
    total = len(expected)

    for issue_key, keywords in expected.items():
        detected = any(kw in review_lower for kw in keywords)
        breakdown[issue_key] = 1.0 if detected else 0.0
        if detected:
            found += 1

    base_score = found / total if total > 0 else 0.0
    length_bonus = min(0.1, len(review_text) / 2000)
    has_fix = any(w in review_lower for w in ["fix", "replace", "instead", "use", "should", "recommend"])
    fix_bonus = 0.05 if has_fix else 0.0
    has_line_ref = any(w in review_lower for w in ["line", "l.", "ln", "row", "function"])
    line_bonus = 0.05 if has_line_ref else 0.0
    total_score = min(1.0, base_score + length_bonus + fix_bonus + line_bonus)

    missed = [k for k, v in breakdown.items() if v == 0.0]
    feedback_parts = []
    if missed:
        feedback_parts.append(f"Missed issues: {', '.join(missed)}.")
    if found == total:
        feedback_parts.append("All expected issues identified!")
    if not has_fix:
        feedback_parts.append("Tip: Include fix suggestions for higher score.")
    feedback = " ".join(feedback_parts) if feedback_parts else "Good review."

    return CodeReviewReward(value=round(total_score, 4), breakdown=breakdown, feedback=feedback)


class CodeReviewEnv:
    def __init__(self, task_id: str = "easy"):
        assert task_id in TASKS, f"task_id must be one of {list(TASKS.keys())}"
        self._task_id = task_id
        self._task = TASKS[task_id]
        self._step_num = 0
        self._done = False
        self._cumulative_reward = 0.0
        self._last_review: Optional[str] = None
        self._last_error: Optional[str] = None
        self._history: list[dict] = []

    def reset(self, task_id: Optional[str] = None) -> dict:
        if task_id:
            assert task_id in TASKS
            self._task_id = task_id
            self._task = TASKS[task_id]
        self._step_num = 0
        self._done = False
        self._cumulative_reward = 0.0
        self._last_review = None
        self._last_error = None
        self._history = []
        return {"observation": self._build_observation(), "done": False, "reward": 0.0, "info": {}}

    def step(self, action) -> dict:
        if self._done:
            return {"observation": self._build_observation(), "reward": 0.0, "done": True,
                    "info": {"error": "Episode already done. Call reset()."}}
        if isinstance(action, dict):
            try:
                action = CodeReviewAction(**action)
            except Exception as e:
                self._last_error = str(e)
                return {"observation": self._build_observation(), "reward": 0.0,
                        "done": False, "info": {"error": str(e)}}
        self._last_error = None
        self._step_num += 1
        self._last_review = action.review_text
        reward_obj = grade_review(self._task_id, action.review_text)
        step_reward = max(0.0, reward_obj.value - self._cumulative_reward)
        self._cumulative_reward = max(self._cumulative_reward, reward_obj.value)
        self._history.append({
            "step": self._step_num,
            "reward": reward_obj.value,
            "breakdown": reward_obj.breakdown,
            "feedback": reward_obj.feedback,
        })
        if reward_obj.value >= 0.99 or self._step_num >= self._task["max_steps"]:
            self._done = True
        return {
            "observation": self._build_observation(),
            "reward": round(step_reward, 4),
            "done": self._done,
            "info": {
                "grader_feedback": reward_obj.feedback,
                "breakdown": reward_obj.breakdown,
                "cumulative_reward": self._cumulative_reward,
            },
        }

    def state(self) -> dict:
        return {
            "task_id": self._task_id,
            "step_number": self._step_num,
            "done": self._done,
            "cumulative_reward": self._cumulative_reward,
            "history": self._history,
            "task_description": self._task["description"],
            "max_steps": self._task["max_steps"],
        }

    def close(self) -> None:
        pass

    def _build_observation(self) -> CodeReviewObservation:
        return CodeReviewObservation(
            task_id=self._task_id,
            code_snippet=self._task["code"],
            instructions=self._task["description"],
            step_number=self._step_num,
            max_steps=self._task["max_steps"],
            last_review=self._last_review,
            last_action_error=self._last_error,
            score_so_far=self._cumulative_reward,
            goal=self._task["goal"],
        )