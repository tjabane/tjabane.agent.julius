from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from krabs_application.http_routes import router  # noqa: E402
from krabs_observability import fastapi_app as observe_fastapi_app  # noqa: E402
from krabs_observability import initialize_observability  # noqa: E402


def create_app() -> FastAPI:
    app = FastAPI(title="Mr Krabs", version="0.1.0")
    telemetry = initialize_observability()
    observe_fastapi_app(app, telemetry)
    app.include_router(router)
    return app


app = create_app()
