import uvicorn


def main():
    uvicorn.run(
        'plyder.app:app', host='127.0.0.1', port=5000, log_level='info', reload=True
    )


if __name__ == '__main__':
    main()
