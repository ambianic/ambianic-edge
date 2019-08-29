name = "ambianic"

import time
import logging
import threading
import signal
import ambianic.flaskr
from ambianic.cameras.detect import CameraStreamProcessor


AI_MODELS_DIR = "ai_models"
CONFIG_DIR = "config"

is_configured = False

log = logging.getLogger(__name__)


def configure():
    # TODO: read from an environment configured config file
    logging.basicConfig(level=logging.INFO)
    logging.info('configured')
    return


class ThreadedJob(threading.Thread):

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
        #while not self.shutdown_flag.is_set():
        #    # ... Job code here ...
        #    time.sleep(0.5)

        # ... Clean shutdown code here ...
        log.info('Thread #%s for job %s stopped', self.ident, self.job.__class__.__name__)

    def stop(self):
        log.info('Thread #%s for job %s is signalled to stop', self.ident, self.job.__class__.__name__)
        self.job.stop()


class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.

    Method for controlled multi-threaded Python app exit suggested by George Notaras:
    https://www.g-loaded.eu/2016/11/24/how-to-terminate-running-python-threads-using-signals/
    """
    pass


def service_shutdown(signum, frame):
    log.info('Caught signal %d', signum)
    raise ServiceExit


def start():
    if not is_configured:
        configure()

    # Register the signal handlers
    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)

    log.info('Starting main program...')

    # Start the job threads
    try:
        # start AI inference loop on camera streams
        cams = CameraStreamProcessor()
        j1 = ThreadedJob(cams)

        # start web app server
        flask_server = flaskr.FlaskServer()
        j2 = ThreadedJob(flask_server)

        j1.start()
        j2.start()

        last_time = time.monotonic()

        def heartbeat():
            nonlocal last_time
            new_time = time.monotonic()
            # print a heartbeat message every 2 seconds
            if new_time - last_time > 2:
                log.info("Main thread alive.")
                last_time = new_time

        # Keep the main thread running, otherwise signals are ignored.
        while True:
            time.sleep(1)
            heartbeat()

    except ServiceExit:
        # Terminate the running threads.
        # Set the shutdown flag on each thread to trigger a clean shutdown of each thread.
        # j1.shutdown_flag.set()
        j1.stop()
        # j2.shutdown_flag.set()
        j2.stop()
        # Wait for the threads to close...
        j1.join()
        j2.join()

    log.info('Exiting main program...')

