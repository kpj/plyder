import importlib.resources as pkg_resources

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import static
from .routes import server

from .downloader import clean_packages


app = FastAPI()

with pkg_resources.path(static, 'styles.css') as static_file:
    app.mount('/static', StaticFiles(directory=static_file.parent), name='static')

app.include_router(server.router)


@app.on_event('startup')
def startup_event():
    clean_packages()
