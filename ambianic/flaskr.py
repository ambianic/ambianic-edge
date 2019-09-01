import os
import threading
import logging
from flask import Flask
import flask
from werkzeug.serving import make_server

log = logging.getLogger(__name__)


class FlaskServer:
    """ Thin wrapper around Flask constructs that allows controlled start and stop of the web app server. """

    def __init__(self, config):
        self.app = create_app()
        self.srv = make_server('0.0.0.0', 8778, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.config = config

    def start(self):
        log.info('starting Flask server')
        log.info('Flask server started')
        self.srv.serve_forever()

    def stop(self):
        self.srv.shutdown()


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
