import uvicorn

from loguru import logger

from .__version__ import __version__
from .config import config


def main():
    logger.info(f'plyder v{__version__}')

    uvicorn.run(
        'plyder.app:app',
        host=config['ip_host'],
        port=config['port'],
        log_level='warning',
        reload=False,
    )


if __name__ == '__main__':
    main()
