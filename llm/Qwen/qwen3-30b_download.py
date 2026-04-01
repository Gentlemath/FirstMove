import os
from huggingface_hub import snapshot_download
from dotenv import dotenv_values
from load_token import *

def main():

    dotenv_path = os.path.join(os.path.dirname(__file__), 'api.env')
    token_name = "HF_TOKEN"
    token = load_token(dotenv_path, token_name)

    os.environ[token_name] = token

    model_repo = "Qwen/Qwen3-30B-A3B-Instruct-2507-FP8"
    target_dir = "/net/scratch/whymath/Qwen3-30B-A3B-Instruct-2507-FP8"

    os.makedirs(target_dir, exist_ok=True)

    print(f"Starting model download ...")
    try:
        snapshot_download(
                repo_id=model_repo,
                local_dir=target_dir,
                token=token,
                #allow_patterns=[
                #    "*.safetensors",
                #    "*.json",
                #    "*.model",
                #    "*.py",
                #]
        )
        print(f"Model download completed successfully!")

    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
