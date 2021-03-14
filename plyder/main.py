import uvicorn


def main():
    uvicorn.run(
        'plyder.app:app', host='0.0.0.0', port=5000, log_level='info', reload=False
    )


if __name__ == '__main__':
    main()
