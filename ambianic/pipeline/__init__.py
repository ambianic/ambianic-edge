import logging
import abc

log = logging.getLogger(__name__)

# Define pipe lifecycle states
PIPE_STATE_STOPPED = 0
PIPE_STATE_RUNNING = 10
PIPE_STATES = [PIPE_STATE_RUNNING, PIPE_STATE_STOPPED]


class PipeElement:
    """ The basic building block of an Ambianic pipeline """

    def __init__(self):
        self.state = PIPE_STATE_STOPPED
        self.next_element = None

    def start(self):
        self.state = PIPE_STATE_RUNNING

    def stop(self):
        self.state = PIPE_STATE_STOPPED

    def connect_to_next_element(self, next_element=None):
        """ Connect this element to the next element in the pipe """
        assert next_element
        assert isinstance(next_element, PipeElement)
        self.next_element = next_element

    @abc.abstractmethod
    def receive_next_sample(self, **sample):
        """ Receive next sample from a connected previous element
            :argument **kwargs a variable list of (key, value) pairs that represent the sample
        """
        pass
