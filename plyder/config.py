from pathlib import Path

import yaml
import jsonschema
from appdirs import user_config_dir

from loguru import logger


DEFAULT_CONFIG = {
    'download_directory': '~/Downloads/',
}


def get_config():
    config_file = Path(user_config_dir('plyder')) / 'config.yaml'

    # load config
    if config_file.exists():
        with config_file.open() as fd:
            config = yaml.safe_load(fd)
    else:
        logger.warning(
            'Could not find configuration file. '
            f'Create "{config_file}" to set your own options. '
            f'Using the default config for now: {DEFAULT_CONFIG}'
        )
        config = DEFAULT_CONFIG

    # validate config
    config_schema = {
        'properties': {'download_directory': {'type': 'string'}},
        'additionalProperties': False,
        'required': ['download_directory'],
    }
    jsonschema.validate(instance=config, schema=config_schema)

    # prepare some values
    config['download_directory'] = Path(config['download_directory'])

    return config


config = get_config()
