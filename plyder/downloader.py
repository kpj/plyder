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


PROVIDER_DICT = {'mega.nz': download_mega}


@logger.catch
def download_url(job: 'JobSubmission'):
    for url in job.url_field:
        o = urlparse(url)
        logger.info(f'Processing "{url}"')

        provider = PROVIDER_DICT.get(o.netloc)
        if provider is None:
            logger.error(f'No provider for "{url}"')
            continue

        output_dir = DOWNLOAD_DIRECTORY / job.package_name
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f'[{provider.__name__}] Downloading "{url}" to "{output_dir}"')
        provider(url, output_dir)
