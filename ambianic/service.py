
import threading
import logging

log = logging.getLogger(__name__)


class ThreadedJob(threading.Thread):
    """ A job that runs in its own python thread. """

    # Reminder: even though multiple processes can work well for pipelines, since they are mostly independent,
    # Google Coral does not allow access to it from different processes yet.

    def __init__(self, job):
        threading.Thread.__init__(self, daemon=True)

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


class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.

    Method for controlled multi-threaded Python app exit suggested by George Notaras:
    https://www.g-loaded.eu/2016/11/24/how-to-terminate-running-python-threads-using-signals/
    """
    pass

