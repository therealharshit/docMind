from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.storage.files import FileUploadManager
from app.storage.jobs import JobStore
from app.worker import Worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.result_dir.mkdir(parents=True, exist_ok=True)

    app.state.settings = settings
    app.state.job_store = JobStore(settings.sqlite_path)
    app.state.upload_manager = FileUploadManager(settings)
    app.state.worker = Worker(settings, app.state.job_store)
    app.state.worker.start()
    try:
        yield
    finally:
        await app.state.worker.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()
