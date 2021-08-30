import json
import yaml
import pytest
import pkg_resources
from fastapi.testclient import TestClient
import logging
import os
import sys
from pathlib import Path
from ambianic.webapp.fastapi_app import app, set_data_dir
from ambianic import config, __version__, load_config

log = logging.getLogger(__name__)

def reset_config():
    config.reload()

# session scoped test setup 
# ref: https://docs.pytest.org/en/6.2.x/fixture.html#autouse-fixtures-fixtures-you-don-t-have-to-request
@pytest.fixture(autouse=True, scope="session")
def setup_session(tmp_path_factory):
    """ setup any state specific to the execution of the given module."""
    reset_config()
    data_dir = tmp_path_factory.mktemp("data")
    # convert from Path object to str
    data_dir_str = data_dir.as_posix()
    set_data_dir(data_dir=data_dir_str)

@pytest.fixture
def client():
    test_client = TestClient(app)
    return test_client


def test_hello(client):
    rv = client.get('/')
    assert 'Ambianic Edge!' in rv.json()


def test_health_check(client):
    rv = client.get('/healthcheck')
    assert 'is running' in rv.json()


def test_status(client):
    rv = client.get('/api/status')
    data = rv.json()
    assert (data["status"], data["version"]) == ("OK", __version__)


def test_get_timeline(client):
    rv = client.get('/api/timeline')
    assert rv.json()["status"] == "success"


def test_initialize_premium_notification(client):
    testId = 'auth0|123456789abed'
    endpoint = 'https://localhost:5050'

    request = client.get(
        '/api/auth/premium-notification?userId={0}&notification_endpoint={1}'.format(testId, endpoint))
    response = request.json()

    assert isinstance(response, dict)
    configDir = pkg_resources.resource_filename(
        "ambianic.webapp", "premium.yaml")

    with open(configDir, "r") as file:
        file_data = yaml.safe_load(file)
        config_provider = file_data["credentials"]["USER_AUTH0_ID"]
        email_endpoint = file_data["credentials"]["NOTIFICATION_ENDPOINT"]

        assert isinstance(config_provider, str)
        assert config_provider == testId

        assert isinstance(email_endpoint, str)
        assert email_endpoint == endpoint

    assert os.path.isfile(configDir)
    assert isinstance(response["status"], str)
    assert isinstance(response["message"], str)
    assert response["status"] == "OK"
    assert response["message"] == "AUTH0_ID SAVED"


def test_get_config(client):
    _dir = os.path.dirname(os.path.abspath(__file__))
    load_config(os.path.join(_dir, 'test-config.yaml'), True)
    rv = client.get('/api/config')
    data = rv.json()
    # dynaconf conversts to uppercase all root level json keys
    log.debug(f'config: {data}')
    assert data['pipelines'.upper()] is not None
    assert data['ai_models'.upper()] is not None
    assert data['sources'.upper()] is not None


def test_save_source(client):
    src_target = {
        "id": "test1",
        "uri": "test",
        "type": "video",
        "live": True
    }    
    rv = client.put('/api/config/source', json=src_target)
    data = rv.json()
    log.debug(f"JSON response: {data}")
    assert data
    assert data["id"] == "test1" 
    assert data["uri"] == "test"
    assert data["type"] == "video"
    assert data["live"] == True
    # changes to data should be saved correctly
    src_target["uri"] = "test1.2"
    src_target["type"] = "image"
    src_target["live"] = False
    rv = client.put('/api/config/source', json=src_target)
    data = rv.json()
    assert data
    assert data["id"] == "test1" 
    assert data["uri"] == "test1.2"
    assert data["type"] == "image"
    assert data["live"] == False


def test_delete_source(client):
    src_target = {
        "id": "test1",
        "uri": "test",
        "type": "video",
        "live": True
    }
    rv = client.put('/api/config/source', json=src_target)
    assert rv.json()["id"] == "test1"
    rv = client.delete('/api/config/source/test1')
    assert rv.json()["status"] == "success"
    # attempting to delete the same source again should fail
    rv = client.delete('/api/config/source/test1')
    assert rv.status_code == 404
    assert rv.json() == {"detail": "source id not found"}


def test_ping(client):
    rv = client.get('/api/ping')
    assert rv.json() == 'pong'
