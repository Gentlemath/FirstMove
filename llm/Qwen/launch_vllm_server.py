import os
import time
import requests
import subprocess
from huggingface_hub import snapshot_download
from dotenv import dotenv_values

# ---- Config ----
REPO_ID = "Qwen/Qwen3-30B-A3B-Instruct-2507-FP8"
LOCAL_MODEL_DIR = "/net/scratch/whymath/Qwen3-30B-A3B-Instruct-2507-FP8"
VLLM_PORT = 8000
VLLM_HOST = f"http://localhost:{VLLM_PORT}"
MAX_MODEL_LEN = 4096

# ---- Load HuggingFace token from .env ----
dotenv_path = os.path.join(os.path.dirname(__file__), "api.env")
config = dotenv_values(dotenv_path)

if "HF_TOKEN" not in config:
    raise RuntimeError("HF_TOKEN not found in api.env")
os.environ["HF_TOKEN"] = config["HF_TOKEN"]

# ---- Download model if not already downloaded ----
if not os.path.exists(LOCAL_MODEL_DIR) or not os.listdir(LOCAL_MODEL_DIR):
    print(f"Downloading model: {REPO_ID}")
    snapshot_download(
        repo_id=REPO_ID,
        local_dir=LOCAL_MODEL_DIR,
        token=config["HF_TOKEN"],
        allow_patterns=[
            "*.safetensors",
            "*.json",
            "*.model",
            "*.py",
            ".md"
        ]
    )
    print("Model downloaded.")
else:
    print("Model already exists locally.")

# ---- Check if vLLM server is running ----
def is_vllm_server_running():
    try:
        response = requests.get(f"{VLLM_HOST}/v1/models", timeout=2)
        return response.status_code == 200
    except Exception:
        return False

# ---- Start vLLM server ----
def start_vllm_server():
    command = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", LOCAL_MODEL_DIR,
        "--max-model-len", str(MAX_MODEL_LEN),
        "--tensor-parallel-size", "1",
        "--port", str(VLLM_PORT),
        "--trust-remote-code"
    ]
    log_file = os.path.expanduser("~/vllm_server.log")
    print(f"Starting vLLM server... (logs at {log_file})")
    with open(log_file, "a") as log:
        subprocess.Popen(command, stdout=log, stderr=log)

# ---- Main logic ----
def main():
    if is_vllm_server_running():
        print("vLLM server is already running.")
    else:
        start_vllm_server()
        print("Waiting for vLLM server to become available...")
        for _ in range(1000):  # 30 seconds max
            if is_vllm_server_running():
                print("vLLM server is now running.")
                break
            time.sleep(2)
        else:
            raise TimeoutError("vLLM server did not start in time.")

if __name__ == "__main__":
    main()
