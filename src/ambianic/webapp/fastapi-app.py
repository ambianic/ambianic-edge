"""FASTAPI web/REST app."""
import os
import logging
import time
import pkg_resources
from pathlib import Path
from requests import get
import yaml
from ambianic import config, DEFAULT_DATA_DIR, __version__
from ambianic.util import ServiceExit, ThreadedJob, ManagedService
from ambianic.webapp.server import samples, config_sources
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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
    resp = jsonify(response_object)
    return resp

@app.get('/api/auth/premium-notification')
def initialize_premium_notification():
    userAuth0Id = request.args.get('userId')
    endpoint = request.args.get('notification_endpoint')
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

@app.get('/api/timeline', methods=['GET'])
@app.get('/api/timeline.json', methods=['GET'])
def get_timeline():
    response_object = {'status': 'success'}
    req_page = request.args.get('page', default=1, type=int)
    log.debug('Requested timeline events page" %d', req_page)
    nonlocal data_dir
    resp = samples.get_timeline(page=req_page, data_dir=data_dir)
    response_object['timeline'] = resp
    log.debug('Returning %d timeline events', len(resp))
    # log.debug('Returning samples: %s ', response_object)
    resp = jsonify(response_object)
    return resp

@app.get('/api/samples')
def get_samples():
    response_object = {'status': 'success'}
    req_page = request.args.get('page', default=1, type=int)
    resp = samples.get_samples(page=req_page)
    response_object['samples'] = resp
    log.debug('Returning %d samples', len(resp))
    # log.debug('Returning samples: %s ', response_object)
    resp = jsonify(response_object)
    return resp


@app.post('/api/samples')
def add_samples():
    response_object = {'status': 'success'}
    post_data = request.get_json()
    new_sample = {
        'title': post_data.get('title'),
        'author': post_data.get('author'),
        'read': post_data.get('read')
    }
    samples.add_sample(new_sample)
    response_object['message'] = 'Sample added!'
    response_object['sample_id'] = new_sample["id"]
    log.debug('Sample added: %s ', new_sample)
    # log.debug('Returning samples: %s ', response_object)
    resp = jsonify(response_object)
    return resp


@app.put('/api/samples/<sample_id>')
def update_sample(sample_id):
    response_object = {'status': 'success'}
    post_data = request.get_json()
    sample = {
        'id': sample_id,
        'title': post_data.get('title'),
        'author': post_data.get('author'),
        'read': post_data.get('read')
    }
    log.debug('update_sample %s', sample)
    samples.update_sample(sample)
    response_object['message'] = 'Sample updated!'
    return jsonify(response_object)

@app.delete('/api/samples/<sample_id>')
def delete_sample(sample_id):
    response_object = {'status': 'success'}
    samples.delete_sample(sample_id)
    response_object['message'] = 'Sample removed!'
    return jsonify(response_object)

@app.get('/api/config')
def get_config():
    return jsonify(config.as_dict())

@app.get('/api/config/source/<source_id>')
def get_config_source(source_id):
    return jsonify(config_sources.get(source_id))

@app.put('/api/config/source/<source_id>')
def update_config_source(source_id):
    source = request.get_json()
    config_sources.save(source_id, source)
    return jsonify(config_sources.get(source_id))

@app.delete('/api/config/source/<source_id>')
def delete_config_source(source_id):
    config_sources.remove(source_id)
    return jsonify({'status': 'success'})


# sanity check route
@app.get('/api/ping')
def ping():
    response_object = 'pong'
    return jsonify(response_object)

@app.get('/static/<path:path>')
def get_static_file(path):
    return fastapi.send_from_directory('static', path)

@app.get('/api/data/<path:path>')
def get_data_file(path):
    data_path = Path(DEFAULT_DATA_DIR).resolve()
    log.info('Serving static data file from: %r', data_path / path)
    return fastapi.send_from_directory(data_path, path)

@app.get('/client', defaults={'path': 'index.html'})
@app.get('/client/', defaults={'path': 'index.html'})
@app.get('/client/<path:path>')
def get_client_file(path):
    if log.level <= logging.DEBUG:  # development mode
        hostname = fastapi.request.host.split(':')[0]
        base_uri = 'http://{host}:1234/'.format(host=hostname)
        return get(f'{base_uri}{path}').content
    # production mode
    return fastapi.send_from_directory('client/dist', path)

log.debug('Fastapi url map: %s', str(app.url_map))
log.debug('Fastapi config map: %s', str(app.config))
log.debug('Fastapi running in %s mode',
            'development' if app.config['DEBUG'] else 'production')

log.debug('Fastapi app created.')

