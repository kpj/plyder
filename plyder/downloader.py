import sys
import json
from urllib.parse import urlparse
from contextlib import redirect_stdout

# from mega import Mega
import sh

from loguru import logger

from .config import config


STATUS_FILENAME = '.plyder.status'
LOG_FILENAME = '.download.log'


def download_mega(url: str, output_dir: str):
    # mega = Mega()
    # m = mega.login()
    # m.download_url(url=url, dest_path=output_dir)

    sh.megadl(
        '--path',
        output_dir,
        url,
        _out=sys.stdout,
        _err_to_out=True,
    )


def download_wget(url: str, output_dir: str):
    sh.wget(
        '--directory-prefix',
        output_dir,
        url,
        _out=sys.stdout,
        _err_to_out=True,
    )


PROVIDER_DICT = {'mega.nz': download_mega}


@logger.catch
def download_url(url: str, output_dir: str):
    o = urlparse(url)

    provider = PROVIDER_DICT.get(o.netloc)
    if provider is None:
        logger.warning(f'No provider for "{url}" found, using wget fallback')
        provider = download_wget

    logger.info(f'[{provider.__name__}] Downloading "{url}" to "{output_dir}"')

    try:
        provider(url, output_dir)
    except Exception as e:
        logger.exception(e)
        return False
    return True


def download_package(job: 'JobSubmission'):
    output_dir = config['download_directory'] / job.package_name
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f'Processing "{job.package_name}"')
    with (output_dir / STATUS_FILENAME).open('w') as fd:
        json.dump({'status': 'running'}, fd)

    with (output_dir / LOG_FILENAME).open('w') as fd:
        with redirect_stdout(fd):
            any_url_failed = False
            for url in job.url_field:
                success = download_url(url, output_dir)
                any_url_failed |= not success

    logger.info(f'Finished "{job.package_name}"')
    with (output_dir / STATUS_FILENAME).open('w') as fd:
        json.dump({'status': 'failed' if any_url_failed else 'done'}, fd)


def clean_packages():
    if not config['download_directory'].exists():
        logger.warning(
            f'Download directory ({config["download_directory"]}) does not exist.'
        )
        return

    for entry in config['download_directory'].iterdir():
        if not entry.is_dir():
            continue

        status_file = entry / STATUS_FILENAME
        if not status_file.exists():
            continue

        with status_file.open() as fd:
            info = json.load(fd)

        if info['status'] not in ('done', 'failed'):
            logger.warning(
                f'Package "{entry.name}" in inconsistent state, setting to failed'
            )

            with status_file.open('w') as fd:
                json.dump({'status': 'failed'}, fd)


def list_packages():
    if not config['download_directory'].exists():
        logger.warning(
            f'Download directory ({config["download_directory"]}) does not exist.'
        )
        return []

    res = []
    for entry in config['download_directory'].iterdir():
        # read log
        log_file = entry / LOG_FILENAME
        if log_file.exists():
            with log_file.open() as fd:
                log_text = fd.read()[-10000:]  # truncate
        else:
            log_text = ''

        # assemble information
        status_file = entry / STATUS_FILENAME
        if status_file.exists():
            with status_file.open() as fd:
                info = json.load(fd)
        else:
            info = {'status': 'unknown'}

        res.append({'name': entry.name, 'info': info, 'log': log_text})
    return res
