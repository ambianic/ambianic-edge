name = "ambianic"

import time
import logging
import threading
import signal
import os
import yaml
from ambianic.webapp.flaskr import FlaskServer
from .pipeline.interpreter import PipelineServer
from .service import ServiceExit, ThreadedJob

WORK_DIR = None
AI_MODELS_DIR = "ai_models"
CONFIG_FILE = "config.yaml"
SECRETS_FILE = "secrets.yaml"

log = logging.getLogger(__name__)


def _configure_logging(config=None):
    default_log_level = "WARNING"
    if not config:
        logging.basicConfig()
    log_level = config.get("level", default_log_level)
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        log.warning('Invalid log level: %s', log_level)
        log.warning('Defaulting log level to %s', default_log_level)
        numeric_level = getattr(logging, default_log_level)
    if numeric_level <= logging.INFO:
        format_cfg = '%(asctime)s %(levelname)-4s %(pathname)s.%(funcName)s(%(lineno)d): %(message)s'
        datefmt_cfg = '%Y-%m-%d %H:%M:%S'
    else:
        format_cfg = None
        datefmt_cfg = None

    log_filename = config.get('file', None)

    logging.basicConfig(
        format=format_cfg,
        level=numeric_level,
        datefmt=datefmt_cfg,
        filename=log_filename)

    log.info('Logging configured with level %s', logging.getLevelName(numeric_level))
    if numeric_level <= logging.DEBUG:
        log.debug('Configuration dump:')
        log.debug(yaml.dump(config))


def configure(env_work_dir):
    """ Load configuration settings

        :returns config if configuration was loaded without issues. None or a specific exception otherwise.
    """
    assert env_work_dir, 'Working directory required.'
    assert os.path.exists(env_work_dir), 'working directory invalid: {}'.format(env_work_dir)
    global WORK_DIR
    WORK_DIR = env_work_dir
    secrets_file = os.path.join(WORK_DIR, SECRETS_FILE)
    config_file = os.path.join(WORK_DIR, CONFIG_FILE)
    try:
        if os.path.isfile(secrets_file):
            with open(secrets_file) as sf:
                secrets_config = sf.read()
        else:
            secrets_config = ""
            log.warning("Secrets file not found. Proceeding without it: %s", secrets_file)
        with open(config_file) as cf:
            base_config = cf.read()
            all_config = secrets_config + "\n" + base_config
        config = yaml.safe_load(all_config)

        # configure logging
        logging_config = config.get('logging', None)
        _configure_logging(logging_config)

        return config
    except Exception as e:
        log.error("Failed to load configuration: %s", str(e))
        return None


def service_shutdown(signum, frame):
    log.info('Caught signal %d', signum)
    raise ServiceExit


def _stop_servers(servers):
    log.debug('Stopping servers...')
    for s in servers:
        s.stop()


def _healthcheck(servers):
    """ Check the health of managed servers """
    for s in servers:
        latest_heartbeat, status = s.healthcheck()
        now = time.monotonic()
        lapse = now - latest_heartbeat
        if lapse > 10:
            log.warning('Server "%s" is not responsive. Latest heart beat was %f seconds ago.', s.__class__.__name__, lapse)

def start(env_work_dir):
    """ Programmatic start of the main service """

    config = configure(env_work_dir)

    if not config:
        log.info('Cannot start. Valid configuration file required.')
        return False

    log.info('Starting Ambianic runtime...')
    # Register the signal handlers
    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)

    # AI inferencing server
    pipeline_server = None
    # web server
    flask_server = None

    servers = []

    # Start the job threads
    try:
        # start AI inference pipelines
        pipeline_server = PipelineServer(config)
# TODO: uncomment when done testing front end
#        pipeline_server.start()
#        servers.append(pipeline_server)

        # start web app server
        flask_server = FlaskServer(config)
        flask_server.start()
        servers.append(flask_server)

        last_time = time.monotonic()

        def _heartbeat():
            """ Notify external monitoring services that we are in good health """
            nonlocal last_time
            new_time = time.monotonic()
            # print a heartbeat message every so many seconds
            if new_time - last_time > 5:
                log.info("Main thread alive.")
                # this is where hooks to external monitoring services will come in
                last_time = new_time
            global _service_exit_requested
            if _service_exit_requested:
                raise ServiceExit

        # Keep the main thread running, otherwise signals are ignored.
        while True:
            time.sleep(1)
            _healthcheck(servers)
            _heartbeat()

    except ServiceExit as e:
        log.info('Service exit requested.')
        log.debug('Cleaning up before exit...')
        # Terminate the running threads.
        # Set the shutdown flag on each thread to trigger a clean shutdown of each thread.
        # j1.shutdown_flag.set()
        # j2.shutdown_flag.set()
        _stop_servers(servers)

    log.info('Exiting main program...')
    return True


_service_exit_requested = False


def stop():
    """ Programmatic stop of the main service """

    global _service_exit_requested
    _service_exit_requested = True
