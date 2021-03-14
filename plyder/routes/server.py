import importlib.resources as pkg_resources

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, validator

from .. import templates
from ..downloader import download_url, list_packages


router = APIRouter(tags=['server'])

with pkg_resources.path(templates, 'index.html') as template_file:
    templates = Jinja2Templates(directory=template_file.parent)


class JobSubmission(BaseModel):
    package_name: str
    url_field: str

    @validator('package_name', 'url_field')
    def is_nonempty(cls, value):
        if not value:
            raise ValueError('must be non-empty')
        return value

    @validator('url_field')
    def create_url_list(cls, value):
        return [url.strip() for url in value.splitlines() if url.strip()]


@router.get('/', response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        'index.html', {'request': request, 'package_list': list_packages()}
    )


@router.post('/submit_job')
async def submit_job(background_tasks: BackgroundTasks, job: JobSubmission):
    background_tasks.add_task(download_url, job=job)
    return {'status': 'good'}
