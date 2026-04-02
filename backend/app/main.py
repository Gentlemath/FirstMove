import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

env_path = Path(__file__).resolve().parents[1] / ".env"
print(f"DEBUG: Trying to load .env from: {env_path}")
print(f"DEBUG: .env exists: {env_path.exists()}")
load_dotenv(env_path)
print(f"DEBUG: After load_dotenv, LLM_MODEL={os.getenv('LLM_MODEL')}")
print(f"DEBUG: After load_dotenv, LLM_ENDPOINT_URL={os.getenv('LLM_ENDPOINT_URL')}")


def create_app() -> FastAPI:
    from app.routes.calendar import router as calendar_router
    from app.routes.workspace import router as workspace_router

    app = FastAPI(title="First Move API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(calendar_router)
    app.include_router(workspace_router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
