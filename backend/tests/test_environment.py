import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Load .env early for local test environment
load_dotenv(BACKEND_ROOT / ".env")

from app.main import app

try:
    import requests
except ImportError:
    requests = None

EXTERNAL_TEST_FLAG = "RUN_EXTERNAL_TESTS"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def _require_env_var(name: str):
    value = os.environ.get(name)
    assert value is not None and value.strip() != "", f"Environment variable {name} is not set"
    return value


def _require_external_test_env(*names: str):
    if os.environ.get(EXTERNAL_TEST_FLAG) != "1":
        pytest.skip(f"Set {EXTERNAL_TEST_FLAG}=1 to run external environment smoke tests")

    missing = [name for name in names if not os.environ.get(name, "").strip()]
    if missing:
        pytest.skip(f"Missing external test environment variables: {', '.join(missing)}")


def test_required_env_vars_are_set():
    _require_external_test_env(
        "GOOGLE_CALENDAR_ID",
        "GOOGLE_CALENDAR_TOKEN_PATH",
        "GOOGLE_CALENDAR_TIMEZONE",
        "LLM_ENDPOINT_URL",
        "LLM_MODEL",
        "LLM_TIMEOUT",
    )
    _require_env_var("GOOGLE_CALENDAR_ID")
    _require_env_var("GOOGLE_CALENDAR_TOKEN_PATH")
    _require_env_var("GOOGLE_CALENDAR_TIMEZONE")
    _require_env_var("LLM_ENDPOINT_URL")
    _require_env_var("LLM_MODEL")
    _require_env_var("LLM_TIMEOUT")


def test_google_token_file_exists():
    _require_external_test_env("GOOGLE_CALENDAR_TOKEN_PATH")
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


def test_backend_health_endpoint(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"


def test_vllm_models_endpoint():
    assert requests is not None, "requests package is not installed"
    _require_external_test_env("LLM_ENDPOINT_URL")
    llm_endpoint = _require_env_var("LLM_ENDPOINT_URL")
    url = f"{llm_endpoint.rstrip('/')}/models"
    resp = requests.get(url, timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("data"), list)
    assert len(data["data"]) > 0


def test_direct_vllm_chat_completion():
    from openai import OpenAI

    _require_external_test_env("LLM_ENDPOINT_URL", "LLM_MODEL")
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


def test_workspace_generation_endpoint(client: TestClient):
    payload = {
        "raw_tasks": ["Finish spec", "Reply recruiter"],
        "raw_task_text": None,
    }

    resp = client.post("/workspace/generate", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] in {"rules", "llm"}
    assert "task_cards" in data
    assert isinstance(data["task_cards"], list)
    assert len(data["task_cards"]) >= 2
