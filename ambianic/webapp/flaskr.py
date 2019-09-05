import os
from multiprocessing import Process
import logging
from flask import Flask
import flask
from flask_bower import Bower
from werkzeug.serving import make_server
from ambianic.service import ServiceExit

log = logging.getLogger(__name__)


class FlaskProcess(Process):

    def __init__(self, config):
        super(FlaskProcess, self).__init__(name='flask_web_server')
        self.config = config
        self.srv = None
        app = create_app()
        self.srv = make_server('0.0.0.0', 8778, app)
        ctx = app.app_context()
        ctx.push()
        self.flask_stopped = True
        log.debug('Flask process created')

    def run(self):
        log.debug('Flask starting main loop')
        log.debug('Flask process id: %d', self.pid)
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


class FlaskServer:
    """
        Thin wrapper around Flask constructs that allows
        controlled start and stop of the web app server in a separate process.

        :argument config section of the configuration file
    """

    def __init__(self, config):
        self.config = config
        self.flask_process = None

    def start(self):
        log.info('Starting Flask server')
        self.flask_process = FlaskProcess(self.config)
        self.flask_process.start()
        self.flask_process.join()
        log.info('Flask server stopped')

    def stop(self):
        if self.flask_process:
            self.flask_process.stop()
            self.flask_process.join()


def create_app():
    log.debug('Creating Flask app...')

    # if Ambianic is in INFO or DEBUG mode, pass that info on to Flask
    if log.level <= logging.INFO:
        os.environ['FLASK_ENV'] = 'development'

    # create and configure the web app
    # set the project root directory as the static folder, you can set others.
    app = Flask(__name__, instance_relative_config=True)
    # Turn on Bower version of js file names to avoid browser cache using outdated files
    app.config['BOWER_QUERYSTRING_REVVING'] = True
    # register Bower file handler with Flask
    Bower(app)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/')
    def hello():
        return 'Ambianic! Halpful AI for home and business automation.'

    # healthcheck page available to docker-compose and other health monitoring tools
    @app.route('/healthcheck')
    def health_check():
        return 'Ambianic is running in a cheerful healthy state!'

    # live view of ambianic pipelines
    @app.route('/pipelines')
    def view_pipelines():
        return flask.render_template('pipelines.html')

    @app.route('/static/<path:path>')
    def static_file(path):
        return flask.send_from_directory('static', path)


    @app.route('/data/<path:path>')
    def data_file(path):
        return flask.send_from_directory('../../data', path)


    log.debug('Flask url map: %s', str(app.url_map))
    log.debug('Flask config map: %s', str(app.config))
    log.debug('Flask running in %s mode', 'development' if app.config['DEBUG'] else 'production')

    log.debug('Flask app created.')
    return app
