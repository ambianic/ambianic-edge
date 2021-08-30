"""FASTAPI web/REST app."""
import os
import logging
import time
import pkg_resources
from pathlib import Path
from requests import get
import yaml
from ambianic import config, __version__, DEFAULT_DATA_DIR
from ambianic.util import ServiceExit, ThreadedJob, ManagedService
from ambianic.webapp.server import timeline_dao, config_sources
from ambianic.webapp.server.config_sources import SensorSource
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

def set_data_dir(data_dir: str = None) -> None:
    app.data_dir = data_dir
    # serve static files from the data directory
    data_path = Path(data_dir).resolve()
    app.mount("/api/data", StaticFiles(directory=data_path), name="static")

# set an initial data dir location
if config:
    data_dir = config.get('data_dir', None)
if not data_dir:
    data_dir = DEFAULT_DATA_DIR

log = logging.getLogger(__name__)

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

# a simple page that says hello
@app.get('/')
def hello():
    return 'Ambianic Edge! Helpful AI for home and business automation.'

# healthcheck page available to docker-compose
# and other health monitoring tools
@app.get('/healthcheck')
def health_check():
    return 'Ambianic Edge is running in a cheerful healthy state!'

# healthcheck page available to docker-compose
# and other health monitoring tools
@app.get('/api/status')
def get_status():
    response_object = {'status': 'OK', 'version': __version__}
    return response_object

@app.get('/api/auth/premium-notification')
def initialize_premium_notification(userId: str, notification_endpoint: str):
    userAuth0Id = userId
    endpoint = notification_endpoint
    auth_file = {
        'name': 'AMBIANIC-EDGE-PREMIUM',
        'credentials': {
            'USER_AUTH0_ID': userAuth0Id,
            'NOTIFICATION_ENDPOINT': endpoint,
        }}

    directory = pkg_resources.resource_filename(
        "ambianic.webapp", "premium.yaml")

    file = open(directory, 'w+')
    yaml.dump(auth_file, file)
    file.close()

    return {"status": "OK", "message": "AUTH0_ID SAVED"}

@app.get('/api/timeline')
@app.get('/api/timeline.json')
def get_timeline(page: int=1):
    response_object = {'status': 'success'}
    log.debug('Requested timeline events page" %d', page)
    resp = timeline_dao.get_timeline(page=page, data_dir=app.data_dir)
    response_object['timeline'] = resp
    log.debug('Returning %d timeline events', len(resp))
    # log.debug('Returning samples: %s ', response_object)
    return response_object

@app.get('/api/config')
def get_config():
    return config.as_dict()

@app.get('/api/config/source/{source_id}')
def get_config_source(source_id: str):
    return config_sources.get(source_id)

@app.put('/api/config/source')
def update_config_source(source: SensorSource):
    config_sources.save(source=source)
    return config_sources.get(source.id)

@app.delete('/api/config/source/{source_id}')
def delete_config_source(source_id: str):
    config_sources.remove(source_id)
    return {'status': 'success'}


# sanity check route
@app.get('/api/ping')
def ping():
    return 'pong'


log.info('REST API deployed (as a Fastapi app).')
