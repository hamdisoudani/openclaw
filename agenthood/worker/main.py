import os
import sys
import time
import redis
from groq import Groq
from dotenv import load_dotenv

# Load secrets
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

if not GROQ_API_KEY:
    print("FATAL: GROQ_API_KEY is not set.")
    sys.exit(1)

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Initialize Redis
r = redis.from_url(REDIS_URL)
stream_name = "task_queue"
group_name = "worker_group"

# Try to create the consumer group (ignore if exists)
try:
    r.xgroup_create(stream_name, group_name, id='0', mkstream=True)
    print(f"Created Redis Consumer Group: {group_name}")
except redis.exceptions.ResponseError as e:
    if "BUSYGROUP" not in str(e):
        print(f"Error creating group: {e}")

print("Python Swarm Worker started. Waiting for tasks from Go Receptionist...")

def process_task(task_id: str, prompt: str):
    print(f"\n[Worker] Claimed Task {task_id}: '{prompt}'")
    print(f"[Worker] Thinking using Groq Llama/OSS Model...")

    try:
        completion = client.chat.completions.create(
            # "llama-3.3-70b-versatile" is commonly available on Groq
            # Since gpt-oss-120b might not be standard on Groq, we fall back to a known Groq model
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert software engineer inside the AgentHood."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_completion_tokens=1024,
            stream=True
        )

        print(f"\n[Task {task_id} Output]:\n", end="")
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print(f"\n\n[Worker] Task {task_id} Completed.\n")

    except Exception as e:
        print(f"\n[Worker] Error processing task {task_id}: {e}")

# The Infinite Worker Loop (The Pull Model)
while True:
    try:
        # Block and wait for a new message in the Redis stream (0 = infinite wait)
        # This consumes 0 CPU while waiting.
        messages = r.xreadgroup(group_name, "worker-1", {stream_name: ">"}, count=1, block=0)

        if messages:
            for stream, msg_list in messages:
                for msg_id, msg_data in msg_list:
                    # msg_data comes back as bytes, decode to string
                    task_id = msg_data.get(b"task_id", b"").decode("utf-8")
                    prompt = msg_data.get(b"prompt", b"").decode("utf-8")

                    # Run the AI logic
                    process_task(task_id, prompt)

                    # Acknowledge the message so it's removed from the queue
                    r.xack(stream_name, group_name, msg_id)

    except Exception as e:
        print(f"Redis polling error: {e}")
        time.sleep(2)
