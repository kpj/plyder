import json
from pathlib import Path
from urllib.parse import urlparse

# from mega import Mega
import sh

from loguru import logger


DOWNLOAD_DIRECTORY = Path('plyder_downloads')
DOWNLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


def download_mega(url: str, output_dir: str):
    # mega = Mega()
    # m = mega.login()
    # m.download_url(url=url, dest_path=output_dir)

    sh.megadl(
        '--path',
        output_dir,
        url,
        _fg=True,
        # _err_to_out=True, _tee=True
    )


def download_wget(url: str, output_dir: str):
    sh.wget(
        '--directory-prefix',
        output_dir,
        url,
        _fg=True,
    )


PROVIDER_DICT = {'mega.nz': download_mega}


@logger.catch
def download_url(job: 'JobSubmission'):
    for url in job.url_field:
        o = urlparse(url)
        logger.info(f'Processing "{url}"')

        provider = PROVIDER_DICT.get(o.netloc)
        if provider is None:
            logger.warning(f'No provider for "{url}" found, using wget fallback')
            provider = download_wget

        output_dir = DOWNLOAD_DIRECTORY / job.package_name
        output_dir.mkdir(parents=True, exist_ok=True)

        with (output_dir / 'plyder.status').open('w') as fd:
            json.dump({'status': 'running'}, fd)

        logger.info(f'[{provider.__name__}] Downloading "{url}" to "{output_dir}"')
        provider(url, output_dir)

        with (output_dir / 'plyder.status').open('w') as fd:
            json.dump({'status': 'done'}, fd)


def clean_packages():
    for entry in DOWNLOAD_DIRECTORY.iterdir():
        with (entry / 'plyder.status').open() as fd:
            info = json.load(fd)

        if info['status'] not in ('done', 'failed'):
            logger.warning(
                f'Package "{entry.name}" in inconsistent state, setting to failed'
            )

            with (entry / 'plyder.status').open('w') as fd:
                json.dump({'status': 'failed'}, fd)


def list_packages():
    res = []
    for entry in DOWNLOAD_DIRECTORY.iterdir():
        with (entry / 'plyder.status').open() as fd:
            res.append({'name': entry.name, 'info': json.load(fd)})
    return res
