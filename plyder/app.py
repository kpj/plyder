from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes import server


app = FastAPI()
app.mount('/static', StaticFiles(directory='plyder/static'), name='static')

app.include_router(server.router)
