from fastapi.testclient import TestClient

import pytest
from bs4 import BeautifulSoup

from plyder.app import app
from plyder.config import config


def dummy_download(url, target_dir):
    # don't download, only pretend by touching
    (target_dir / url).touch()
    print("Created file", url)


@pytest.fixture(scope="function")
def client(mocker, tmp_path_factory):
    mocker.patch.dict(
        "plyder.config.config",
        {**config, "download_directory": tmp_path_factory.mktemp("plyder_downloads")},
        clear=True,
    )

    mocker.patch("plyder.download_handlers.get_provider_dict", lambda config: {})
    mocker.patch.dict(
        "plyder.download_handlers.DEFAULT_PROVIDER",
        {"name": "test_dummy", "function": dummy_download},
        clear=True,
    )

    with TestClient(app) as client:
        return client


def test_app(client):
    # test empty display
    resp = client.get("/")
    assert resp.status_code == 200


def test_invalid_download(client):
    resp = client.post(
        "/submit_job",
        json={
            "package_name": "",  # empty name
            "url_field": "",  # empty urls
        },
    )
    assert resp.status_code == 422


def test_download(client):
    # test download
    resp = client.post(
        "/submit_job",
        json={
            "package_name": "current_package",
            "url_field": "first_url\nsecond_url\n something with spaces \nlast_url",
        },
    )
    assert resp.status_code == 200

    dw_dir = config["download_directory"]
    assert (dw_dir / "current_package").is_dir()

    assert (dw_dir / "current_package" / "first_url").is_file()
    assert (dw_dir / "current_package" / "second_url").is_file()
    assert (dw_dir / "current_package" / "something with spaces").is_file()
    assert (dw_dir / "current_package" / "last_url").is_file()

    assert (
        '"status": "done"'
        in (dw_dir / "current_package" / ".plyder.status").read_text()
    )
    assert (
        dw_dir / "current_package" / ".download.log"
    ).read_text() == "Created file first_url\nCreated file second_url\nCreated file something with spaces\nCreated file last_url\n"

    # test display after download
    resp = client.get("/")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.text, "html.parser")
    entries = (
        soup.find("div", attrs={"class": "container"})
        .find("div", attrs={"class": "col-lg-8"})
        .find_all("div", attrs={"class": "border rounded m-3 p-1"})
    )

    assert len(entries) == 1
    entry = entries[0]
    assert entry.find("h3").find(text=True).strip() == "current_package"
