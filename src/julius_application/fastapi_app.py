from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

from julius_application.http_routes import router
from julius_application.scheduler import run_scheduler_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler_enabled = os.environ.get("SCHEDULER_ENABLED", "true").lower() == "true"
    stop_event = asyncio.Event()
    scheduler_task: asyncio.Task | None = None
    if scheduler_enabled:
        interval = int(os.environ.get("SCHEDULER_INTERVAL_SECONDS", "300"))
        scheduler_task = asyncio.create_task(
            run_scheduler_loop(interval_seconds=interval, stop_event=stop_event)
        )

    try:
        yield
    finally:
        stop_event.set()
        if scheduler_task:
            scheduler_task.cancel()
            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass


def create_app() -> FastAPI:
    app = FastAPI(title="Julius", version="0.1.0", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()
