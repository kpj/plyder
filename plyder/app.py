import importlib.resources as pkg_resources

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from loguru import logger

from . import static
from .routes import server

from .config import config
from .downloader import clean_packages


app = FastAPI()

with pkg_resources.path(static, 'styles.css') as static_file:
    app.mount('/static', StaticFiles(directory=static_file.parent), name='static')

app.include_router(server.router)


@app.on_event('startup')
def startup_event():
    config['download_directory'].mkdir(parents=True, exist_ok=True)
    clean_packages()
    logger.info(f'Server {config["ip_host"]}:{config["port"]} started')
