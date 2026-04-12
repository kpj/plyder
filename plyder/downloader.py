import asyncio
import datetime
import json
import os
import pathlib
import shutil
import sys
import threading
from concurrent import futures
from contextlib import redirect_stdout
from typing import Any
from urllib.parse import urlparse

import humanize
import sh
from loguru import logger
from pydantic import BaseModel, field_serializer, field_validator

from .download_handlers import DEFAULT_PROVIDER, get_provider_dict
from .utils import get_current_time, get_process_cpu, get_process_memory


class JobSubmission(BaseModel):
    package_name: str
    url_field: list[str]

    @field_validator("package_name")
    @classmethod
    def is_nonempty(cls, v: str) -> str:
        if not v:
            raise ValueError("must be non-empty")
        return v

    @field_validator("url_field", mode="before")
    @classmethod
    def create_url_list(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [url.strip() for url in v.splitlines() if url.strip()]
        return v

    @field_serializer("url_field")
    def serialize_url_field(self, value: list[str]) -> str:
        return "\n".join(value)


class Downloader:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

        self.provider_dict = get_provider_dict(self.config["download_handlers"])
        self.semaphore = threading.Semaphore(self.config["max_parallel_downloads"])

        self.status_filename = ".plyder.status"
        self.log_filename = ".download.log"

        self.config["download_directory"].mkdir(parents=True, exist_ok=True)

    @logger.catch
    def download_url(self, url: str, output_dir: str) -> bool:
        o = urlparse(url)

        provider = self.provider_dict.get(o.netloc)
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

    def update_package_status(
        self, status: str, output_dir: pathlib.Path, **kwargs
    ) -> None:
        status_file = output_dir / self.status_filename

        # current status data
        status_data = {}
        if status_file.exists():
            with status_file.open() as fd:
                status_data = json.load(fd)

        # set fields
        status_data = {
            **status_data,
            "status": status,
            **kwargs,
        }

        # store result atomically
        temp_file = status_file.with_suffix(".tmp")
        with temp_file.open("w") as fd:
            json.dump(status_data, fd)
        temp_file.replace(status_file)

    def download_package(self, job: "JobSubmission") -> None:
        # prepare environment
        output_dir = self.config["download_directory"] / job.package_name
        output_dir.mkdir(parents=True, exist_ok=True)

        self.update_package_status(
            "queued", output_dir, start_time=get_current_time(), job=job.model_dump()
        )
        logger.info(f'Added "{job.package_name}" to queue')

        # start download
        with self.semaphore:
            self.update_package_status(
                "running", output_dir, start_time=get_current_time()
            )

            # download
            logger.info(f'Processing "{job.package_name}"')

            with (output_dir / self.log_filename).open("w") as fd:
                with redirect_stdout(fd):
                    any_url_failed = False
                    for url in job.url_field:
                        success = self.download_url(url, output_dir)
                        any_url_failed |= not success

            logger.info(f'Finished "{job.package_name}"')

            # update final status
            self.update_package_status(
                "failed" if any_url_failed else "done",
                output_dir,
                end_time=get_current_time(),
            )

    def clean_packages(self) -> None:
        if not self.config["download_directory"].exists():
            logger.warning(
                f"Download directory ({self.config['download_directory']}) does not exist."
            )
            return

        for entry in self.config["download_directory"].iterdir():
            if not entry.is_dir():
                continue

            status_file = entry / self.status_filename
            if not status_file.exists():
                continue

            with status_file.open() as fd:
                info = json.load(fd)

            if info["status"] in {"done", "failed"}:
                # download finished (success or failure)
                pass
            elif info["status"] in {"running", "queued"}:
                # download was interrupted, resuming
                job = JobSubmission(**info["job"])
                logger.info(f'Resuming "{job.package_name}"')

                loop = asyncio.get_running_loop()
                loop.run_in_executor(
                    futures.ThreadPoolExecutor(), lambda: self.download_package(job)
                )
            else:
                logger.warning(
                    f'Package "{entry.name}" in inconsistent state, setting to failed'
                )

                self.update_package_status("failed", entry)

    def list_packages(self) -> list[dict[str, Any]]:
        if not self.config["download_directory"].exists():
            logger.warning(
                f"Download directory ({self.config['download_directory']}) does not exist."
            )
            return []

        res = []
        for entry in self.config["download_directory"].iterdir():
            if not entry.is_dir():
                continue

            # read log (last 10000 bytes)
            log_file = entry / self.log_filename
            log_text = ""
            if log_file.exists():
                file_size = log_file.stat().st_size
                offset = min(10000, file_size)
                with log_file.open("rb") as fd:
                    fd.seek(-offset, os.SEEK_END)
                    log_text = fd.read().decode("utf-8", errors="replace")

            # assemble information
            status_file = entry / self.status_filename
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

    def get_server_info(self) -> dict[str, Any]:
        if self.config["download_directory"].exists():
            total, used, free = shutil.disk_usage(self.config["download_directory"])
        else:
            total, used, free = -1, -1, -1

        return {
            "download_directory": str(self.config["download_directory"]),
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
