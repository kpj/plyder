import sys
import json
import shutil
import asyncio
import pathlib
import datetime
import threading
from urllib.parse import urlparse
from contextlib import redirect_stdout

import sh
import humanize

from loguru import logger

from pydantic import BaseModel, validator, field_serializer

from .config import config
from .utils import get_process_memory, get_process_cpu, get_current_time
from .download_handlers import DEFAULT_PROVIDER, get_provider_dict


STATUS_FILENAME = ".plyder.status"
LOG_FILENAME = ".download.log"

PROVIDER_DICT = get_provider_dict(config)

DOWNLOADER_SEMAPHORE = threading.Semaphore(config["max_parallel_downloads"])


class JobSubmission(BaseModel):
    package_name: str
    url_field: str

    @validator("package_name", "url_field")
    def is_nonempty(cls, value: str) -> str:
        if not value:
            raise ValueError("must be non-empty")
        return value

    @validator("url_field")
    def create_url_list(cls, value: str) -> list[str]:
        return [url.strip() for url in value.splitlines() if url.strip()]

    @field_serializer("url_field")
    def serialize_url_field(self, value: list[str]) -> str:
        return "\n".join(value)


@logger.catch
def download_url(url: str, output_dir: str) -> bool:
    o = urlparse(url)

    provider = PROVIDER_DICT.get(o.netloc)
    if provider is None:
        logger.warning(f'No provider for "{url}" found, using wget fallback')
        provider = DEFAULT_PROVIDER

    logger.info(f'[{provider["name"]}] Downloading "{url}" to "{output_dir}"')

    try:
        func = provider["function"]
        if isinstance(func, sh.Command):
            func(url, output_dir, _out=sys.stdout, _err_to_out=True)
        else:
            func(url, output_dir)
    except Exception as e:
        logger.exception(e)
        return False
    return True


def update_package_status(status: str, output_dir: pathlib.Path, **kwargs) -> None:
    status_file = output_dir / STATUS_FILENAME

    # current status data
    status_data = {}
    if status_file.exists():
        with (output_dir / STATUS_FILENAME).open() as fd:
            status_data = json.load(fd)

    # set fields
    status_data = {
        **status_data,
        "status": status,
        **kwargs,
    }

    # store result
    with status_file.open("w") as fd:
        json.dump(status_data, fd)


def download_package(job: "JobSubmission") -> None:
    # prepare environment
    output_dir = config["download_directory"] / job.package_name
    output_dir.mkdir(parents=True, exist_ok=True)

    update_package_status(
        "queued", output_dir, start_time=get_current_time(), job=job.model_dump()
    )
    logger.info(f'Added "{job.package_name}" to queue')

    # start download
    with DOWNLOADER_SEMAPHORE:
        update_package_status("running", output_dir, start_time=get_current_time())

        # download
        logger.info(f'Processing "{job.package_name}"')

        with (output_dir / LOG_FILENAME).open("w") as fd:
            with redirect_stdout(fd):
                any_url_failed = False
                for url in job.url_field:
                    success = download_url(url, output_dir)
                    any_url_failed |= not success

        logger.info(f'Finished "{job.package_name}"')

        # update final status
        update_package_status(
            "failed" if any_url_failed else "done",
            output_dir,
            end_time=get_current_time(),
        )


async def download_package_async(job: "JobSubmission") -> None:
    return download_package(job)


def clean_packages() -> None:
    if not config["download_directory"].exists():
        logger.warning(
            f'Download directory ({config["download_directory"]}) does not exist.'
        )
        return

    for entry in config["download_directory"].iterdir():
        if not entry.is_dir():
            continue

        status_file = entry / STATUS_FILENAME
        if not status_file.exists():
            continue

        with status_file.open() as fd:
            info = json.load(fd)

        if info["status"] in {"done", "failed"}:
            # download finished (succes or failure)
            pass
        elif info["status"] in {"running", "queued"}:
            # download was interrupted, resuming
            job = JobSubmission(**info["job"])
            logger.info(f'Resuming "{job.package_name}"')
            asyncio.create_task(download_package_async(job))
        else:
            logger.warning(
                f'Package "{entry.name}" in inconsistent state, setting to failed'
            )

            with status_file.open("w") as fd:
                json.dump({"status": "failed"}, fd)


def list_packages():
    if not config["download_directory"].exists():
        logger.warning(
            f'Download directory ({config["download_directory"]}) does not exist.'
        )
        return []

    res = []
    for entry in config["download_directory"].iterdir():
        if not entry.is_dir():
            continue

        # read log
        log_file = entry / LOG_FILENAME
        if log_file.exists():
            with log_file.open() as fd:
                log_text = fd.read()[-10000:]  # truncate
        else:
            log_text = ""

        # assemble information
        status_file = entry / STATUS_FILENAME
        try:
            with status_file.open() as fd:
                info = json.load(fd)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            # due to race conditions, the file may not contain valid JSON
            # even if it exists
            info = {"status": "unknown"}

        res.append({"name": entry.name, "info": info, "log": log_text})

    # sort packages by download started date
    return sorted(
        res,
        key=lambda x: datetime.datetime.strptime(
            x["info"].get("start_time", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S"
        ),
        reverse=True,
    )


def get_server_info():
    if config["download_directory"].exists():
        total, used, free = shutil.disk_usage(config["download_directory"])
    else:
        total, used, free = -1, -1, -1

    return {
        "download_directory": str(config["download_directory"]),
        "disk_usage": {
            "total": humanize.naturalsize(total),
            "used": humanize.naturalsize(used),
            "free": humanize.naturalsize(free),
        },
        "disk_usage_raw": {
            "total": total,
            "used": used,
            "free": free,
        },
        "process": {
            "memory": round(get_process_memory(), 2),
            "cpu": round(get_process_cpu(), 2),
        },
    }
