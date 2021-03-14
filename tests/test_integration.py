from fastapi.testclient import TestClient

import pytest

from plyder.app import app


@pytest.fixture(scope='module')
def client():
    return TestClient(app)


def test_app(client):
    response = client.get('/')
    assert response.status_code == 200
