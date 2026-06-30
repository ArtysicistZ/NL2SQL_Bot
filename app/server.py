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

    # The Next.js app (web/) is the primary UI and is served separately. The
    # legacy static frontend is only mounted when SERVE_STATIC is enabled, so
    # the backend image is API-only by default.
    if _serve_static() and FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    return app


def _serve_static() -> bool:
    return os.getenv("SERVE_STATIC", "").lower() in {"1", "true", "yes"}


app = create_app()


def _print_banner() -> None:
    if _serve_static() and (FRONTEND_DIR / "index.html").exists():
        print(f"Serving legacy static frontend from {FRONTEND_DIR / 'index.html'}")
    else:
        print("Running API-only (Next.js web/ serves the UI).")


if __name__ == "__main__":
    import uvicorn

    _print_banner()
    uvicorn.run(
        "app.server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        reload=os.getenv("RELOAD", "").lower() in {"1", "true", "yes"},
    )
