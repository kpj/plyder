import uvicorn

from .config import config


def main():
    config['download_directory'].mkdir(parents=True, exist_ok=True)

    uvicorn.run(
        'plyder.app:app', host='0.0.0.0', port=5000, log_level='info', reload=False
    )


if __name__ == '__main__':
    main()
