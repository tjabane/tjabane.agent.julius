from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from krabs_application.http_routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Mr Krabs", version="0.1.0")
    app.include_router(router)
    return app


app = create_app()
