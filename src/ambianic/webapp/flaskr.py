import os
from multiprocessing import Process
import logging
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask.logging import default_handler
import flask
from requests import get
from werkzeug.serving import make_server
from ambianic.service import ServiceExit, ThreadedJob, ManagedService
from .server import samples
log = logging.getLogger(__name__)

# configuration
DEBUG = True


class FlaskJob(ManagedService):

    def __init__(self, config):
        self.config = config
        self.srv = None
        app = create_app()
        self.srv = make_server('0.0.0.0', 8778, app)
        ctx = app.app_context()
        ctx.push()
        self.flask_stopped = True
        log.debug('Flask process created')

    def start(self):
        log.debug('Flask starting main loop')
        self.flask_stopped = False
        try:
            self.srv.serve_forever()
        except ServiceExit:
            log.info('Service exit requested')
        self.flask_stopped = True
        log.debug('Flask ended main loop')

    def stop(self):
        if not self.flask_stopped:
            log.debug('Flask stopping main loop')
            self.srv.shutdown()
            log.debug('Flask main loop ended')


class FlaskServer(ManagedService):
    """ Thin wrapper around Flask constructs.

    Allows controlled start and stop of the web app server
    in a separate process.

    Parameters
    ----------
    config : yaml
        reference to the yaml configuration file

    """

    def __init__(self, config):
        self.config = config
        self.flask_job = None

    def start(self):
        log.info('Flask server job starting...')
        f = FlaskJob(self.config)
        self.flask_job = ThreadedJob(f)
        self.flask_job.start()
        log.info('Flask server job started')

    def healthcheck(self):
        # TODO: Implement actual health check for Flask
        # See if the /healthcheck URL returns a 200 quickly
        return time.monotonic(), True

    def heal():
        """Heal the server.

        TODO: Keep an eye for potential scenarios that cause this server to
         become unresponsive.
        """
        pass

    def stop(self):
        if self.flask_job:
            log.info('Flask server job stopping...')
            self.flask_job.stop()
            self.flask_job.join()
            log.info('Flask server job stopped.')

def create_app():
    log.debug('Creating Flask app...')

    # if Ambianic is in INFO or DEBUG mode, pass that info on to Flask
    if log.level <= logging.INFO:
        os.environ['FLASK_ENV'] = 'development'

    # create and configure the web app
    # set the project root directory as the static folder, you can set others.
    app = Flask(__name__, instance_relative_config=True)
    app.logger.removeHandler(default_handler)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # enable CORS for development
    CORS(app, resources={r'/*': {'origins': '*'}})

    # [Sitemap]
    # sitemap definitions follow

    # a simple page that says hello
    @app.route('/')
    def hello():
        return 'Ambianic! Halpful AI for home and business automation.'

    # healthcheck page available to docker-compose
    # and other health monitoring tools
    @app.route('/healthcheck')
    def health_check():
        return 'Ambianic is running in a cheerful healthy state!'

    # live view of ambianic pipelines
    @app.route('/pipelines')
    def view_pipelines():
        return flask.render_template('pipelines.html')

    @app.route('/api/samples', methods=['GET', 'POST'])
    def get_samples():
        response_object = {'status': 'success'}
        if request.method == 'POST':
            post_data = request.get_json()
            new_sample = {
                'title': post_data.get('title'),
                'author': post_data.get('author'),
                'read': post_data.get('read')
            }
            samples.add_sample(new_sample)
            response_object['message'] = 'Sample added!'
            log.debug('Sample added: %s ', new_sample)
        else:
            req_page = request.args.get('page', default=1, type=int)
            resp = samples.get_samples(page=req_page)
            response_object['samples'] = resp
            log.debug('Returning %d samples', len(resp))
        # log.debug('Returning samples: %s ', response_object)
        resp = jsonify(response_object)
        return resp

    @app.route('/api/samples/<sample_id>', methods=['PUT', 'DELETE'])
    def update_sample(sample_id):
        response_object = {'status': 'success'}
        if request.method == 'PUT':
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
        if request.method == 'DELETE':
            samples.delete_sample(sample_id)
            response_object['message'] = 'Sample removed!'
        return jsonify(response_object)

    # sanity check route
    @app.route('/api/ping', methods=['GET'])
    def ping():
        response_object = 'pong'
        return jsonify(response_object)

    @app.route('/static/<path:path>')
    def static_file(path):
        return flask.send_from_directory('static', path)

    @app.route('/api/data/<path:path>')
    def data_file(path):
        return flask.send_from_directory('../../data', path)

    @app.route('/client', defaults={'path': 'index.html'})
    @app.route('/client/', defaults={'path': 'index.html'})
    @app.route('/client/<path:path>')
    def client_file(path):
        if log.level <= logging.DEBUG:  # development mode
            hostname = flask.request.host.split(':')[0]
            base_uri = 'http://{host}:1234/'.format(host=hostname)
            return get(f'{base_uri}{path}').content
        else:  # production mode
            return flask.send_from_directory('client/dist', path)

#    @app.errorhandler(404)
#    def page_not_found(e):
#        return flask.send_from_directory('client/dist', 'index.html')

#    @app.route('/', defaults={'path': 'index.html'})
#    @app.route('/<path:path>')
#    def client_all(path):
#        return flask.send_from_directory('client/dist', path)

    log.debug('Flask url map: %s', str(app.url_map))
    log.debug('Flask config map: %s', str(app.config))
    log.debug('Flask running in %s mode',
              'development' if app.config['DEBUG'] else 'production')

    log.debug('Flask app created.')
    return app
