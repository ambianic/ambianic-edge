"""Service classes for OS interaction and multithreading."""
import threading
import logging
from abc import abstractmethod

log = logging.getLogger(__name__)


class ManagedJob:
    """A managed job is able to start(), stop() and heal()."""

    @abstractmethod
    def start(self):
        """Start and run until asked to stop() or job completion."""
        pass

    @abstractmethod
    def stop(self):
        """Exit start() method."""
        pass

    @abstractmethod
    def heal(self):
        pass


class ThreadedJob(threading.Thread):
    """A job that runs in its own python thread.

    Jobs managed by Threaded Job must have a start(), stop() method.
    """
    # Reminder: even though multiple processes can work well for pipelines,
    # since they are mostly independent,
    # Google Coral does not allow access to it from different processes yet.
    # Consider moving access to coral in a separate process that can serve
    # an inference task queue from multiple pipelines.

    def __init__(self, job):
        """Inititalize with job .

        Parameters
        ----------
        job : type
            Description of parameter `job`.

        Returns
        -------
        type
            Description of returned object.

        """
        threading.Thread.__init__(self, daemon=True)

        self.job = job
        # The shutdown_flag is a threading.Event object that
        # indicates whether the thread should be terminated.
        # self.shutdown_flag = threading.Event()
        # ... Other thread setup code here ...
        self._stop_requested = threading.Event()

    def run(self):
        log.info('Thread #%s started with job: %s', self.ident, self.job.__class__.__name__)
        while not self._stop_requested.is_set():
            self.job.start()
        # the following technique is helpful when the job is not stoppable
        # while not self.shutdown_flag.is_set():
        #    # ... Job code here ...
        #    time.sleep(0.5)

        # ... Clean shutdown code here ...
        log.info('Thread #%s for job %s stopped', self.ident, self.job.__class__.__name__)

    def stop(self):
        log.info('Thread #%s for job %s is signalled to stop', self.ident, self.job.__class__.__name__)
        self._stop_requested.set()
        self.job.stop()

    def heal(self):
        log.info('Thread #%s for job %s is signalled to heal', self.ident, self.job.__class__.__name__)
        # stop the job and start it again in the run() loop without exiting the thread
        self.job.heal()
        log.info('Thread #%s for job %s completed heal request.', self.ident, self.job.__class__.__name__)


class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.

    Method for controlled multi-threaded Python app exit suggested by George Notaras:
    https://www.g-loaded.eu/2016/11/24/how-to-terminate-running-python-threads-using-signals/
    """
    pass
