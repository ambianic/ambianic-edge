"""Main module for Ambianic AI pipelines."""
import logging
import abc
import time
from ambianic.service import ManagedService

log = logging.getLogger(__name__)

# Define pipe lifecycle states
PIPE_STATE_STOPPED = 0
PIPE_STATE_RUNNING = 10
PIPE_STATES = [PIPE_STATE_RUNNING, PIPE_STATE_STOPPED]


class PipeElement(ManagedService):
    """The basic building block of an Ambianic pipeline."""

    def __init__(self):
        # log.warning('PipeElement __init__ invoked')
        super().__init__()
        self._state = PIPE_STATE_STOPPED
        self._next_element = None
        self._latest_heartbeat = time.monotonic()

    @property
    def state(self):
        return self._state

    def start(self):
        self._state = PIPE_STATE_RUNNING

    @abc.abstractmethod
    def heal(self):  # pragma: no cover
        pass

    def healthcheck(self):
        """Check the health of this element.

        :returns: (timestamp, status) tuple with most recent heartbeat
        timestamp and health status code ('OK' normally).
        """
        oldest_heartbeat = self._latest_heartbeat
        status = 'OK'  # At some point status may carry richer information
        return oldest_heartbeat, status

    def heartbeat(self):
        """Set the heartbeat timestamp to time.monotonic()."""
        log.debug('Pipeline element %s heartbeat signal.',
                  self.__class__.__name__)
        now = time.monotonic()
        lapse = now - self._latest_heartbeat
        log.debug('Pipeline element %s heartbeat lapse %f',
                  self.__class__.__name__, lapse)
        self._latest_heartbeat = now

    def stop(self):
        """Receive stop signal and act accordingly.

        Subclasses should override this method by
        first invoking their super class implementation and then running
        through steps specific to stopping their ongoing sample processing.

        """
        self._state = PIPE_STATE_STOPPED

    def connect_to_next_element(self, next_element=None):
        """Connect this element to the next element in the pipe.

        Subclasses should not have to override this method.

        """
        assert next_element
        assert isinstance(next_element, PipeElement)
        self._next_element = next_element

    def receive_next_sample(self, **sample):
        """Receive next sample from a connected previous element.

        Subclasses should not have to override this method.

        :Parameters:
        ----------
        **sample : dict
            A dict of (key, value) pairs that represent the sample.
            It is left to specialized implementations of PipeElement to specify
            their in/out sample formats and enforce compatibility with
            adjacent connected pipe elements.

        """
        self.heartbeat()
        # NOTE: A future implementation could maximize hardware
        # resources by launching each sample processing into
        # a separate thread. For example if an AI element
        # returns 10 person boxes which then need to be
        # scanned by the next element for faces, and the
        # underlying architecture provides 16 available CPU cores
        # or 10 EdgeTPUs, then each face detection in a person box
        # can be launched independently from the others as soon as
        # the person boxes come in from the object detection
        # process_sample generator.
        for processed_sample in self.process_sample(**sample):
            if self._next_element:
                if (processed_sample):
                    self._next_element.receive_next_sample(**processed_sample)
                else:
                    self._next_element.receive_next_sample()
                self.heartbeat()

    @abc.abstractmethod  # pragma: no cover
    def process_sample(self, **sample):
        """Implement processing in subclass as a generator function.

        Invoked by receive_next_sample() when the previous element
        (or pipeline source) feeds another data input sample.

        Implementing subclasses should process input samples and yield
        output samples for the next element in the pipeline.

        :Parameters:
        ----------
        **sample : dict
            A dict of (key, value) pairs that represent the sample.
            It is left to specialized implementations of PipeElement to specify
            their in/out sample formats and enforce compatibility with
            adjacent connected pipe elements.

        :Returns:
        processed_sample: dict
            Processed sample that will be passed to the next pipeline element.

        """
        yield sample


class HealthChecker(PipeElement):
    """Monitor overall pipeline throughput health.

    Attaches at the end of a pipeline to monitor its health status
    based on received output samples and their frequency.
    """

    def __init__(self, health_status_callback=None):
        """Create instance given health status callback.

        The health status call back will be invoked each time
        the sample_process method is invoked.

        :Parameters:
        ----------
        health_status_callback : function
            Method that is expected to measure the overall pipeline throughput
            health.
        """
        super().__init__()
        assert health_status_callback
        self._health_status_callback = health_status_callback

    def process_sample(self, **sample):
        """Call health callback and pass on sample as is."""
        log.debug('%s received sample from the connected '
                  'preceding pipe element.',
                  self.__class__.__name__
                  )
        self._health_status_callback()
        yield sample
