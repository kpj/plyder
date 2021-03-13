import pytest

import plyder


@pytest.fixture
def dummy(tmp_path):
    return tmp_path / 'dummy.txt'


def test_stub(dummy):
    assert True
