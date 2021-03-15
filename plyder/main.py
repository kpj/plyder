import uvicorn

from loguru import logger

from .__version__ import __version__
from .config import config


def main():
    logger.info(f'plyder v{__version__}')

    config['download_directory'].mkdir(parents=True, exist_ok=True)

    uvicorn.run(
        'plyder.app:app', host='0.0.0.0', port=5000, log_level='warning', reload=False
    )


if __name__ == '__main__':
    main()
