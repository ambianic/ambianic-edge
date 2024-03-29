"""FASTAPI OpenAPI/REST app."""
import logging
from pathlib import Path
from typing import List

import pkg_resources
import yaml
from ambianic.configuration import (
    DEFAULT_DATA_DIR,
    __version__,
    get_all_config_files,
    get_root_config,
    init_config,
    save_config,
)
from ambianic.device import DeviceInfo
from ambianic.notification import Notification, NotificationHandler
from ambianic.webapp.server import config_sources, timeline_dao
from ambianic.webapp.server.config_sources import SensorSource
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

log = logging.getLogger("uvicorn.error")

description = """
Ambianic Edge API provides OpenAPI(REST) functions for management and access to detection events.
This API is mainly intended for secure remote access via [peer.fetch()](https://github.com/ambianic/peerfetch).
This API is not intended to be exposed as a public web service.
🚀
"""

app = FastAPI(
    # FastAPI OpenAPI docs metadata
    # ref: https://fastapi.tiangolo.com/tutorial/metadata/
    title="Ambianic Edge OpenAPI",
    description=description,
    version=__version__,
    # terms_of_service="http://example.com/terms/",
    # contact={
    #    "name": "Deadpoolio the Amazing",
    #    "url": "http://x-force.example.com/contact/",
    #    "email": "dp@x-force.example.com",
    # },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)


class BaseResponse(BaseModel):
    status: str = "OK"


def _mount_data_dir(data_dir: str):
    # serve static files from the data directory
    data_path = Path(data_dir).resolve()
    data_path.mkdir(parents=True, exist_ok=True)
    log.info(f"Serving /api/data from {data_path.as_posix()}")
    app.mount("/api/data", StaticFiles(directory=data_path), name="static")


def set_data_dir(data_dir: str = None) -> None:
    app.data_dir = data_dir
    _mount_data_dir(data_dir=data_dir)


# CORS (Cross-Origin Resource Sharing) Section
# ref: https://fastapi.tiangolo.com/tutorial/cors/
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# [Sitemap]
# sitemap definitions follow


@app.on_event("startup")
async def startup_event():
    init_config()
    conf_files = get_all_config_files()
    log.info(f"Loaded config from files: {conf_files}")
    # set an initial data dir location
    root_config = get_root_config()
    if root_config:
        cfg_data_dir = root_config.get("data_dir", DEFAULT_DATA_DIR)
        set_data_dir(data_dir=cfg_data_dir)
    if not app.data_dir:
        set_data_dir(data_dir=DEFAULT_DATA_DIR)


# a simple page that says hello
@app.get("/", include_in_schema=False)
def hello():
    return "Ambianic Edge! Helpful AI for home and business automation."


# Deprecated healthcheck page available to docker-compose
# and other health monitoring tools.
# /api/status is the new preferred method.
@app.get("/healthcheck", include_in_schema=False)
def health_check():
    return "Ambianic Edge is running in a cheerful healthy state!"


class StatusResponse(BaseResponse, DeviceInfo):
    """Combines API status response and device info to reduce remote calls in common use cases."""


@app.get("/api/status", response_model=StatusResponse)
def get_status():
    """Returns overall status of the Ambianic Edge device along with
    other device details such as release version."""
    root_config = get_root_config()
    name = root_config.get("display_name", "My Ambianic Edge device")
    notifications_config = root_config.get("notifications", {})
    default_config = notifications_config.get("default", {})
    notify_enabled = default_config.get("enabled", True)
    response_object = StatusResponse(
        status="OK",
        version=__version__,
        display_name=name,
        notifications_enabled=notify_enabled,
    )
    return response_object


# Method under development for future support of premium instant notifications
@app.get("/api/auth/premium-notification", include_in_schema=False)
def initialize_premium_notification(userId: str, notification_endpoint: str):
    userAuth0Id = userId
    endpoint = notification_endpoint
    auth_file = {
        "name": "AMBIANIC-EDGE-PREMIUM",
        "credentials": {
            "USER_AUTH0_ID": userAuth0Id,
            "NOTIFICATION_ENDPOINT": endpoint,
        },
    }
    directory = pkg_resources.resource_filename("ambianic.webapp", "premium.yaml")
    file = open(directory, "w+")
    yaml.dump(auth_file, file)
    file.close()
    return {"status": "OK", "message": "AUTH0_ID SAVED"}


class TimelineResponse(BaseResponse):
    timeline: List[dict] = Field(None, description="List of detection events")


@app.get("/api/timeline.json", response_model=TimelineResponse, include_in_schema=False)
@app.get("/api/timeline", response_model=TimelineResponse)
def get_timeline(page: int = 1):
    """
    Get timeline items in groups of 5 in reverse chronographical order.

    For example **page**=1 returns the latest 5 detected events, **page**=2 gets the previous 5 and so on.
    """
    response_object = {"status": "success"}
    log.debug('Requested timeline events page" %d', page)
    resp = timeline_dao.get_timeline(page=page, data_dir=app.data_dir)
    response_object["timeline"] = resp
    log.debug("Returning %d timeline events", len(resp))
    # log.debug('Returning samples: %s ', response_object)
    return response_object


@app.get("/api/config", response_model=dict)
def get_config():
    """
    Get the root level configuration settings for this Ambianic Edge device.
    """
    root_config = get_root_config()
    return root_config.as_dict()


@app.get("/api/device/display_name", response_model=str)
def get_device_display_name():
    """
    Get the user friendly display name for this Ambianic Edge device.
    """
    root_config = get_root_config()
    display_name = root_config.get("display_name", None)
    return display_name


@app.put(
    "/api/device/display_name/{display_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def set_device_display_name(display_name: str):
    """
    Set a user friendly dispaly name for this Ambianic Edge device.
    """
    if display_name:
        root_config = get_root_config()
        root_config["display_name"] = display_name
        save_config()
        log.debug(f"saved device display_name: {display_name}")
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Empty string not allowed as device display name value.",
        )


@app.get("/api/notifications/test", response_model=str)
def test_notifications():
    """
    Run a live test with configured notification providers and return status result.
    """
    notification_envelope = {
        "message": "Ambianic Test Event",
        "priority": logging.getLevelName(logging.INFO),
        "args": {
            "id": "test_id",
            "inference_meta": {"display": "Test Detection"},
            "inference_result": [{"label": "test_person"}],
        },
    }
    notifier = NotificationHandler()
    notification = Notification(envelope=notification_envelope, providers=["default"])
    notifier.send(notification)
    log.info("Test notification sent.")


@app.put(
    "/api/integrations/ifttt/api_key/{api_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def set_ifttt_api_key(api_key: str):
    """
    Set API_KEY for the IFTTT integration.
    """
    if api_key:
        root_config = get_root_config()
        root_config["ifttt_webhook_id"] = api_key
        notifications_config = root_config.get("notifications", {})
        default_config = notifications_config.get("default", {})
        default_config["providers"] = [f"ifttt://{api_key}@ambianic"]
        notifications_config["default"] = default_config
        root_config.set("notifications", notifications_config)
        save_config()
        log.debug(f"saved IFTTT API_KEY (WebhookID): {api_key}")
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Empty string not allowed for IFTTT Webhooks API_KEY.",
        )


@app.put(
    "/api/notifications/enable/{enable}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def enable_notifications(enable: bool):
    """
    Enable or disable all notifications.
    """
    root_config = get_root_config()
    notifications_config = root_config.get("notifications", {})
    default_config = notifications_config.get("default", {})
    default_config["enabled"] = enable
    notifications_config["default"] = default_config
    root_config.set("notifications", notifications_config)
    save_config()
    log.debug(f"Saved notifications enabled setting: {enable}")
    return


@app.get("/api/config/source/{source_id}", include_in_schema=False)
def get_config_source(source_id: str):
    return config_sources.get(source_id)


@app.put("/api/config/source", include_in_schema=False)
def update_config_source(source: SensorSource):
    config_sources.save(source=source)
    return config_sources.get(source.id)


@app.delete("/api/config/source/{source_id}", include_in_schema=False)
def delete_config_source(source_id: str):
    config_sources.remove(source_id)
    return {"status": "success"}


# sanity check route
@app.get("/api/ping", include_in_schema=False)
def ping():
    return "pong"


log.info("Ambianc Edge OpenAPI deployed via fastapi/uvicorn.")
