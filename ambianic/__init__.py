name = "ambianic"

import time
import logging
import threading
import signal
import os
import yaml
from ambianic.webapp.flaskr import FlaskServer
from .pipeline.interpreter import get_pipelines
from .service import ServiceExit

WORK_DIR = None
AI_MODELS_DIR = "ai_models"
CONFIG_FILE = "config.yaml"
SECRETS_FILE = "secrets.yaml"

log = logging.getLogger(__name__)


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
        default_log_level = "WARNING"
        log_level = config.get("log_level", default_log_level)
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            log.warning('Invalid log level: %s', log_level)
            log.warning('Defaulting log level to %s', default_log_level)
            numeric_level = getattr(logging, default_log_level)
        if numeric_level <= logging.INFO:
            logging.basicConfig(
                format='%(asctime)s %(levelname)-4s %(pathname)s.%(funcName)s(%(lineno)d): %(message)s',
                level=numeric_level,
                datefmt='%Y-%m-%d %H:%M:%S')
        log.info('Logging configured with level %s', logging.getLevelName(numeric_level))
        if numeric_level <= logging.DEBUG:
            log.debug('Configuration dump:')
            log.debug(yaml.dump(config))

        return config
    except Exception as e:
        log.error("Failed to load configuration: %s", str(e))
        return None


class ThreadedJob(threading.Thread):
    """ A job that runs in its own python thread. """

    # Reminder: even though multiple processes can work well for pipelines, since they are mostly independent,
    # Google Coral does not allow access to it from different processes yet.

    def __init__(self, job):
        threading.Thread.__init__(self)

        self.job = job
        # The shutdown_flag is a threading.Event object that
        # indicates whether the thread should be terminated.
        # self.shutdown_flag = threading.Event()
        # ... Other thread setup code here ...
        self.stopping = False

    def run(self):
        log.info('Thread #%s started with job: %s', self.ident, self.job.__class__.__name__)

        self.job.start()
        # the following technique is helpful when the job is not stoppable
        # while not self.shutdown_flag.is_set():
        #    # ... Job code here ...
        #    time.sleep(0.5)

        # ... Clean shutdown code here ...
        log.info('Thread #%s for job %s stopped', self.ident, self.job.__class__.__name__)

    def stop(self):
        log.info('Thread #%s for job %s is signalled to stop', self.ident, self.job.__class__.__name__)
        self.job.stop()


def service_shutdown(signum, frame):
    log.info('Caught signal %d', signum)
    raise ServiceExit


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

    mpjobs = []

    # Start the job threads
    try:
        # start AI inference pipeline
        pipeline_processors = []
# TODO: uncomment        pipeline_processors = get_pipelines(config)
        for pp in pipeline_processors:
            pj = ThreadedJob(pp)
            mpjobs.append(pj)

        # start web app server
        flask_server = FlaskServer(config)
        fj = ThreadedJob(flask_server)
        mpjobs.append(fj)

        for j in mpjobs:
            j.start()

        last_time = time.monotonic()

        def heartbeat():
            nonlocal last_time
            new_time = time.monotonic()
            # print a heartbeat message every so many seconds
            if new_time - last_time > 5:
                log.info("Main thread alive.")
                last_time = new_time
            global _service_exit_requested
            if _service_exit_requested:
                raise ServiceExit

        # Keep the main thread running, otherwise signals are ignored.
        while True:
            time.sleep(1)
            heartbeat()

    except ServiceExit:
        # Terminate the running threads.
        # Set the shutdown flag on each thread to trigger a clean shutdown of each thread.
        # j1.shutdown_flag.set()
        # j2.shutdown_flag.set()
        for j in mpjobs:
            j.stop()
        # Wait for the threads to close...
        for j in mpjobs:
            j.join()

    log.info('Exiting main program...')
    return True


_service_exit_requested = False


def stop():
    """ Programmatic stop of the main service """

    global _service_exit_requested
    _service_exit_requested = True
