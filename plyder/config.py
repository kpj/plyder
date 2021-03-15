from pathlib import Path

import yaml
import jsonschema
from appdirs import user_config_dir

from loguru import logger


DEFAULT_CONFIG = {
    'download_directory': '~/Downloads/',
    'ip_host': '0.0.0.0',
    'port': 5000,
}

CONFIG_SCHEMA = {
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'properties': {
        'download_directory': {'type': 'string'},
        'ip_host': {'type': 'string'},
        'port': {'type': 'integer'},
    },
    'additionalProperties': False,
    'required': list(DEFAULT_CONFIG.keys()),
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
    jsonschema.validate(instance=config, schema=CONFIG_SCHEMA)

    # prepare some values
    config['download_directory'] = Path(config['download_directory'])

    return config


config = get_config()
