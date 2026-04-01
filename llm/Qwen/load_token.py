import os
import sys
from dotenv import dotenv_values

def load_token(env_file: str, token_name: str) -> str:
    if not os.path.exists(env_file):
        print(f"ERROR: .env file not found at {env_file}")
        sys.exit(1)

    config = dotenv_values(env_file)
    token = config.get(token_name)

    if not token:
        print("ERROR: HF_TOKEN not found in .env file.")
        sys.exit(1)

    return token

