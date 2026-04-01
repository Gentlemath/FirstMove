import os
from pathlib import Path

import pytest
import socket
from dotenv import load_dotenv

# Load .env early for local test environment
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

try:
    import requests
except ImportError:
    requests = None


def _require_env_var(name: str):
    value = os.environ.get(name)
    assert value is not None and value.strip() != "", f"Environment variable {name} is not set"
    return value


def test_required_env_vars_are_set():
    _require_env_var("GOOGLE_CALENDAR_ID")
    _require_env_var("GOOGLE_CALENDAR_TOKEN_PATH")
    _require_env_var("GOOGLE_CALENDAR_TIMEZONE")
    _require_env_var("LLM_ENDPOINT_URL")
    _require_env_var("LLM_MODEL")
    _require_env_var("LLM_TIMEOUT")


def test_google_token_file_exists():
    token_path = _require_env_var("GOOGLE_CALENDAR_TOKEN_PATH")
    assert os.path.exists(token_path), f"Google token path does not exist: {token_path}"


def test_python_packages_installed():
    try:
        import openai
    except ModuleNotFoundError:
        pytest.fail("openai package is not installed")

    try:
        import google.auth
        import googleapiclient
    except ModuleNotFoundError as exc:
        pytest.fail(f"Google client package missing: {exc}")

    assert requests is not None, "requests package is not installed"


def test_backend_health_endpoint():
    assert requests is not None, "requests package is not installed"
    resp = requests.get("http://127.0.0.1:8000/health", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"


def test_vllm_models_endpoint():
    assert requests is not None, "requests package is not installed"
    llm_endpoint = _require_env_var("LLM_ENDPOINT_URL")
    url = f"{llm_endpoint.rstrip('/')}/models"
    resp = requests.get(url, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("data"), list)
    assert len(data["data"]) > 0


def test_direct_vllm_chat_completion():
    from openai import OpenAI

    llm_endpoint = _require_env_var("LLM_ENDPOINT_URL")
    llm_model = _require_env_var("LLM_MODEL")

    client = OpenAI(api_key="not-needed-for-local-llm", base_url=llm_endpoint)

    response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in one sentence."},
        ],
        temperature=0.0,
    )

    assert hasattr(response, "choices")
    assert len(response.choices) > 0
    assert response.choices[0].message.content


def test_workspace_generation_endpoint():
    assert requests is not None, "requests package is not installed"

    payload = {
        "raw_tasks": ["Finish spec", "Reply recruiter"],
        "raw_task_text": None,
    }

    resp = requests.post(
        "http://127.0.0.1:8000/workspace/generate",
        json=payload,
        timeout=10,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] in {"rules", "llm"}
    assert "task_cards" in data
    assert isinstance(data["task_cards"], list)
    assert len(data["task_cards"]) >= 2
