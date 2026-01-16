from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import router
from .settings import FRONTEND_DIR


def create_app() -> FastAPI:
    app = FastAPI(title="NL2SQL API")
    app.include_router(router)

    if os.getenv("ENABLE_CORS", "").lower() in {"1", "true", "yes"}:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    if FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    return app


app = create_app()


def _print_banner() -> None:
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        print(f"Serving frontend from {index_path}")
    else:
        print("Frontend index.html not found; API only.")


if __name__ == "__main__":
    import uvicorn

    _print_banner()
    uvicorn.run(
        "app.server:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8080")),
        reload=os.getenv("RELOAD", "").lower() in {"1", "true", "yes"},
    )
