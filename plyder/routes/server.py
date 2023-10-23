import importlib.resources as pkg_resources

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from ..__version__ import __version__
from .. import templates
from ..downloader import JobSubmission
from ..metrics import assemble_metrics


router = APIRouter(tags=["server"])

with pkg_resources.path(templates, "index.html") as template_file:
    templates = Jinja2Templates(directory=template_file.parent)


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "version": __version__,
            "package_list": request.app.state.downloader.list_packages(),
            "server_info": request.app.state.downloader.get_server_info(),
        },
    )


@router.post("/submit_job")
async def submit_job(
    request: Request, background_tasks: BackgroundTasks, job: JobSubmission
):
    background_tasks.add_task(request.app.state.downloader.download_package, job=job)
    return {"status": "good"}


@router.get("/metrics")
async def metrics(request: Request):
    return Response(
        content=assemble_metrics(request.app.state.downloader), media_type="text/plain"
    )
