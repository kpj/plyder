import sys
from pathlib import Path
import importlib.resources as pkg_resources

import sh
from loguru import logger

from . import download_providers


def download_wget(url: str, output_dir: str) -> None:
    sh.wget(
        '--directory-prefix',
        output_dir,
        url,
        _out=sys.stdout,
        _err_to_out=True,
    )


def get_hosts_from_provider_script(path, host_line_prefix='# PLYDER_HOST:'):
    host_list = []
    with path.open() as fd:
        for line in fd.readlines():
            if not line.startswith(host_line_prefix):
                continue

            host = line[len(host_line_prefix) :].strip()
            host_list.append(host)
    return host_list


def get_provider_dict(config):
    handler_scripts = [
        *pkg_resources.files(download_providers).iterdir(),  # built-in handlers,
        *(Path(p).resolve() for p in config['download_handlers']),  # custom handlers
    ]

    # generate provider information
    provider_dict = {}

    for entry in handler_scripts:
        if entry.name.startswith('__'):
            continue

        host_list = get_hosts_from_provider_script(entry)
        if len(host_list) == 0:
            logger.warning(f'[{entry}] No hosts specified, skipping')

        for host in host_list:
            if host in provider_dict:
                logger.warning(f'[{entry}] Overriding downloader for {entry["host"]}')

            provider_dict[host] = {'name': host, 'function': sh.Command(entry)}

    return provider_dict


DEFAULT_PROVIDER = {'name': download_wget.__name__, 'function': download_wget}
