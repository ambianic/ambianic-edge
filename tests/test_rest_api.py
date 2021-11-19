import logging
import os
from pathlib import Path

import pkg_resources
import pytest
import yaml
from ambianic.configuration import (
    __version__,
    get_root_config,
    init_config,
    reload_config,
)
from ambianic.notification import NotificationHandler
from ambianic.webapp.fastapi_app import app, set_data_dir
from fastapi import status
from fastapi.testclient import TestClient

log = logging.getLogger(__name__)

my_dir = os.path.dirname(os.path.abspath(__file__))


# session scoped test setup
# ref: https://docs.pytest.org/en/6.2.x/fixture.html#autouse-fixtures-fixtures-you-don-t-have-to-request
@pytest.fixture(autouse=True, scope="session")
def setup_session(tmp_path_factory):
    """setup any state specific to the execution of the given module."""
    data_dir = tmp_path_factory.mktemp("data")
    # convert from Path object to str
    data_dir_str = data_dir.as_posix()
    set_data_dir(data_dir=data_dir_str)


@pytest.fixture(scope="function")
def change_test_dir(request):
    """ "
    Change to the test case directory, run the test (yield), then change back to the calling directory to avoid side-effects
    https://stackoverflow.com/a/62055409/12015435
    """
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)


# test setup and teardown
# ref: https://docs.pytest.org/en/6.2.x/fixture.html#autouse-fixtures-fixtures-you-don-t-have-to-request
@pytest.fixture(autouse=True, scope="function")
def setup(request, tmp_path):
    """setup any state specific to the execution of the given module."""
    # save original env settings
    saved_amb_load = os.environ.get("AMBIANIC_CONFIG_FILES", "")
    saved_amb_dir = os.environ.get("AMBIANIC_DIR", "")
    saved_amb_config_save = os.environ.get("AMBIANIC_SAVE_CONFIG_TO", "")
    # change env settings
    save_config_path = str(Path(tmp_path / "test-restapi-config.save.yaml"))
    os.environ["AMBIANIC_CONFIG_FILES"] = (
        str(Path(request.fspath.dirname) / "test-restapi-config.yaml")
        + ","
        + save_config_path
    )
    os.environ["AMBIANIC_SAVE_CONFIG_TO"] = save_config_path
    log.debug(
        f'os.environ["AMBIANIC_CONFIG_FILES"] = {os.environ["AMBIANIC_CONFIG_FILES"]}'
    )
    init_config()
    yield
    # restore env settings
    os.environ["AMBIANIC_CONFIG_FILES"] = saved_amb_load
    os.environ["AMBIANIC_SAVE_CONFIG_TO"] = saved_amb_config_save
    os.environ["AMBIANIC_DIR"] = saved_amb_dir
    init_config()


@pytest.fixture
def client():
    test_client = TestClient(app)
    return test_client


@pytest.fixture(scope="function")
def config():
    return get_root_config()


def test_hello(client):
    rv = client.get("/")
    assert "Ambianic Edge!" in rv.json()


def test_health_check(client):
    rv = client.get("/healthcheck")
    assert "is running" in rv.json()


def test_status(client):
    rv = client.get("/api/status")
    data = rv.json()
    log.debug(data)
    assert (data["status"], data["version"], data["display_name"]) == (
        "OK",
        __version__,
        "My Ambianic Edge device",
    )


def test_get_timeline(client):
    rv = client.get("/api/timeline")
    assert rv.json()["status"] == "success"


def test_initialize_premium_notification(client):
    testId = "auth0|123456789abed"
    endpoint = "https://localhost:5050"

    request = client.get(
        "/api/auth/premium-notification?userId={}&notification_endpoint={}".format(
            testId, endpoint
        )
    )
    response = request.json()

    assert isinstance(response, dict)
    configDir = pkg_resources.resource_filename("ambianic.webapp", "premium.yaml")

    with open(configDir) as file:
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
    rv = client.get("/api/config")
    data = rv.json()
    # dynaconf conversts to uppercase all root level json keys
    log.debug(f"config: {data}")
    assert data["pipelines".upper()] is not None
    assert data["ai_models".upper()] is not None
    assert data["sources".upper()] is not None


def test_save_source(client):
    src_target = {"id": "test1", "uri": "test", "type": "video", "live": True}
    rv = client.put("/api/config/source", json=src_target)
    data = rv.json()
    log.debug(f"JSON response: {data}")
    assert data
    assert data["id"] == "test1"
    assert data["uri"] == "test"
    assert data["type"] == "video"
    assert data["live"] is True
    # changes to data should be saved correctly
    src_target["uri"] = "test1.2"
    src_target["type"] = "image"
    src_target["live"] = False
    rv = client.put("/api/config/source", json=src_target)
    data = rv.json()
    assert data
    assert data["id"] == "test1"
    assert data["uri"] == "test1.2"
    assert data["type"] == "image"
    assert data["live"] is False


def test_delete_source(client):
    src_target = {"id": "test1", "uri": "test", "type": "video", "live": True}
    rv = client.put("/api/config/source", json=src_target)
    assert rv.json()["id"] == "test1"
    rv = client.delete("/api/config/source/test1")
    assert rv.json()["status"] == "success"
    # attempting to delete the same source again should fail
    rv = client.delete("/api/config/source/test1")
    assert rv.status_code == 404
    assert rv.json() == {"detail": "source id not found"}


def test_ping(client):
    rv = client.get("/api/ping")
    assert rv.json() == "pong"


def test_get_device_display_name(client, config):
    current_device_display_name = config.get("display_name", None)
    rv = client.get("/api/device/display_name")
    data = rv.json()
    log.debug(f"get -> /api/device/display_name: JSON response: {data}")
    assert data == current_device_display_name


def test_set_device_display_name(client, request, config):
    config["display_name"] = "Some Random Display Name"
    # this API call should change the display name in the saved config
    new_name = "Kitchen Device"
    rv = client.put(f"/api/device/display_name/{new_name}")
    assert rv.status_code == status.HTTP_204_NO_CONTENT
    # reload config and see if the value set through the API was persisted
    reload_config()
    assert config["display_name"] == new_name
    # now check that the API will return the new value
    rv = client.get("/api/device/display_name")
    data = rv.json()
    log.debug(f"get -> /api/device/display_name: JSON response: {data}")
    assert data == new_name


def test_set_device_display_name_empty(client):
    # this API call should NOT change the display name to empty
    rv = client.put("/api/device/display_name/")
    log.debug(f"put -> /api/device/display_name: JSON response: {rv})")
    # FASTPI responds with 307 when the path ends in a slash without any parameter value after it
    # Instead of the expected 422 error code. Both prevent successul put with empty display name.
    assert rv.status_code >= 300


def test_enable_notifications(client, config):
    # this API call should NOT change the display name to empty
    rv = client.put("/api/notifications/enable/true")
    log.debug(f"put -> /api/notifications/enable: JSON response: {rv})")
    assert rv.status_code == status.HTTP_204_NO_CONTENT
    # reload config and see if the value set through the API was persisted
    reload_config()
    assert config["notifications"]["default"]["enabled"] is True
    rv = client.put("/api/notifications/enable/false")
    log.debug(f"put -> /api/notifications/enable: JSON response: {rv})")
    assert rv.status_code == status.HTTP_204_NO_CONTENT
    # reload config and see if the value set through the API was persisted
    reload_config()
    assert config["notifications"]["default"]["enabled"] is False


def test_set_ifttt_api_key(client, config):
    # this API call should NOT change the display name to empty
    key = "1235"
    rv = client.put(f"/api/integrations/ifttt/api_key/{key}")
    log.debug(f"put -> /api/integrations/ifttt/api_key/: JSON response: {rv})")
    assert rv.status_code == status.HTTP_204_NO_CONTENT
    # reload config and see if the value set through the API was persisted
    reload_config()
    assert config["ifttt_webhook_id"] == key
    assert config["notifications"]["default"]["providers"] == [
        f"ifttt://{key}@ambianic"
    ]


def test_test_notifications(client, config):
    # this API call should NOT change the display name to empty
    sent = False

    def fake_send(_, notification):
        nonlocal sent
        sent = True

    orig_send = NotificationHandler.send
    NotificationHandler.send = fake_send
    rv = client.get("/api/notifications/test")
    log.debug(f"put -> /api/integrations/ifttt/api_key/: JSON response: {rv})")
    NotificationHandler.send = orig_send
    assert rv.status_code == status.HTTP_200_OK
    assert sent is True
