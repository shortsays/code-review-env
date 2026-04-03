import os
import requests
import json
import time
import openai

openai.api_base = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
openai.api_key = os.getenv("HF_TOKEN")
openai.model = os.getenv("MODEL_NAME", "gpt-3.5-turbo")

SPACE_URL = "https://shortsays-code-review-env.hf.space"

def log_step(step_type, data):
    """Structured logging for checklist #5"""
    print(json.dumps({
        "type": step_type,
        "data": data,
        "timestamp": time.time()
    }))

def run_baseline(task_id="easy"):
    print(json.dumps({"type": "START", "task_id": task_id}))
    
    client = requests.Session()
    
   
    resp = client.post(f"{SPACE_URL}/reset", json={"task_id": task_id})
    obs = resp.json()["observation"]
    log_step("STEP", {"action": "reset", "observation": obs})
    
    
    prompt = f"Review this code: {obs.get('code_snippet', '')}"
    response = openai.ChatCompletion.create(
        model=openai.model,
        messages=[{"role": "user", "content": prompt}]
    )
    review_text = response.choices[0].message.content
    
    step_data = {"review_text": review_text}
    
    total_reward = 0
    for step_num in range(5):  
        resp = client.post(f"{SPACE_URL}/step", json=step_data)
        result = resp.json()
        log_step("STEP", {"step_num": step_num, "reward": result['reward'], "done": result['done']})
        total_reward += result['reward']
        if result['done']:
            break
    
    print(json.dumps({"type": "END", "total_reward": total_reward})) 
    return total_reward

if __name__ == "__main__":
    for task in ["easy", "medium", "hard"]:
        run_baseline(task)
        time.sleep(1)