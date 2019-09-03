import os
from multiprocessing import Process
import logging
from flask import Flask
import flask
from werkzeug.serving import make_server
from .service import ServiceExit
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


def create_app(test_config=None):
    # create and configure the web app
    # set the project root directory as the static folder, you can set others.
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    app.config['DEBUG'] = True

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/')
    def hello():
        return 'Ambianic! Halpful AI for home and business automation.'

    # a simple page that says hello
    @app.route('/healthcheck')
    def health_check():
        return 'Ambianic is running in a cheerful healthy state!'

    @app.route('/html/<path:path>')
    def static_html(path):
        return flask.send_from_directory('../html/', path)

    return app
