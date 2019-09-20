
import pytest
import ambianic


def test_no_work_dir():
    with pytest.raises(AssertionError):
        ambianic.start(env_work_dir=None)


def test_bad_work_dir():
    with pytest.raises(AssertionError):
        ambianic.start(env_work_dir='/_/_/_dir_does_not_exist___')


def test_no_config():
    conf = ambianic.configure('/')
    assert not conf
