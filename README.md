# plyder

[![PyPI](https://img.shields.io/pypi/v/plyder.svg?style=flat)](https://pypi.python.org/pypi/plyder)
[![Tests](https://github.com/kpj/plyder/workflows/Tests/badge.svg)](https://github.com/kpj/plyder/actions)

Download manager with web-interface.

<img src="gallery/web-interface.png" width="100%">


## Installation

```python
$ pip install plyder
```


## Usage

```bash
$ plyder
```

`plyder` works out of the box. Though you might want to adapt the configuration to your taste.

### Custom download scripts

Custom download scripts can be specified in the configuration file:

```yaml
download_handlers:
    - ./github_downloader.sh
```

`./github_downloader.sh` needs to be an executable script of the following form:

```bash
#!/usr/bin/env bash
# PLYDER_HOST: <host to match>

url="$1"
output_dir="$2"

<custom logic>
```

See `plyder/download_providers/` for built-in examples.

### Prometheus integration

`plyder` exposes the `/metric` resource which allows monitoring download counts and system usage using [Prometheus](https://prometheus.io/) and, e.g., [Grafana](https://grafana.com/).