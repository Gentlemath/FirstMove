# File: call_deepseek_chat.py

import os
import sys
from openai import OpenAI

# Check the server state
sys.path.append(".")  # Optional: adjust if needed to locate the launch script
from launch_vllm_server import main as ensure_server_running

# Step 1: Ensure server is running
ensure_server_running()

# Step 2: Point to your local vLLM OpenAI-compatible endpoint
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY",  # vLLM does not require a real API key
)

content_exp1 = """Filter the following Weibo content for futures investment related posts:
1. Had hotpot today, it was delicious.
2. Rebar futures main contract price rose today.
3. Happy weekend!
4. Discussion on crude oil futures trading strategies.
In your response, please only list number of the relevant post and a brief reason in 1-2 sentences directly.
"""

content_exp2 = """过滤以下几条微博信息，寻找跟期货投资相关的内容: 
1. Had hotpot today, it was delicious.
2. Rebar futures main contract price rose today.
3. Happy weekend!
4. Discussion on crude oil futures trading strategies.
回答仅需要列出相关条目的号码，并用一两句话给出简要原因.
"""

# Step 3: Create a chat completion request
response = client.chat.completions.create(
    model="/net/scratch/whymath/Qwen3-30B-A3B-Instruct-2507-FP8",
    messages=[
        {"role": "user", "content": content_exp1}
    ],
    max_tokens=512,
    temperature=0.7,
    top_p=0.8,
    extra_body={
            "top_k": 20, # <--- Pass top_k here!
            # You can also pass other vLLM-specific parameters here, e.g.:
            # "repetition_penalty": 1.1,
            "min_p": 0.0,
            # "chat_template_kwargs": {"enable_thinking": False} # For older Qwen3 if applicable
        },
    stream=False, # Set to True for streaming responses
)

# Step 4: Print the model's reply

try:
    content = response.choices[0].message.content
    print(f"\n\nContent: {content}")
except Exception as e:
    print("Failed to extract content:", e)
    content = ""


response = client.chat.completions.create(
    model="/net/scratch/whymath/Qwen3-30B-A3B-Instruct-2507-FP8",
    messages=[
        {"role": "user", "content": content_exp2}
    ],
    max_tokens=512,
    temperature=0.7,
    top_p=0.8,
    extra_body={
            "top_k": 20, # <--- Pass top_k here!
            # You can also pass other vLLM-specific parameters here, e.g.:
            # "repetition_penalty": 1.1,
            "min_p": 0.0,
            # "chat_template_kwargs": {"enable_thinking": False} # For older Qwen3 if applicable
        },
    stream=False, # Set to True for streaming responses
)

# Step 4: Print the model's reply

try:
    content = response.choices[0].message.content
    print(f"\n\nContent: {content}")
except Exception as e:
    print("Failed to extract content:", e)
    content = ""
