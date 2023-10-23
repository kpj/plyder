from contextlib import asynccontextmanager
import importlib.resources as pkg_resources

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from loguru import logger

from . import static
from .routes import server

from .config import config
from .downloader import Downloader


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup code
    app.state.downloader = Downloader(config)

    app.state.downloader.clean_packages()
    logger.info(f'Server {config["ip_host"]}:{config["port"]} started')

    yield

    # shutdown code
    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)

with pkg_resources.path(static, "styles.css") as static_file:
    app.mount("/static", StaticFiles(directory=static_file.parent), name="static")

app.include_router(server.router)
