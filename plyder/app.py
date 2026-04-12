from contextlib import asynccontextmanager
from importlib import resources

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from . import static
from .config import config
from .downloader import Downloader
from .routes import server


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup code
    app.state.downloader = Downloader(config)

    app.state.downloader.clean_packages()
    logger.info(f"Server {config['ip_host']}:{config['port']} started")

    yield

    # shutdown code
    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(resources.files(static))), name="static")

app.include_router(server.router)
