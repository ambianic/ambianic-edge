import logging
import time
import os
import pathlib

import ambianic
from . import PipeElement

log = logging.getLogger(__name__)


class SaveSamples(PipeElement):
    """ Saves samples to an external storage location """

    def __init__(self, element_config=None):
        log.info('Loading pipe element: %s ', self.__class__.__name__)
        PipeElement.__init__(self)
        self.config = element_config
        self.output_directory = self.config.get('output_directory', None)
        assert self.output_directory, 'Pipe element %s: requires argument output_directory:' % self.__class__.__name__
        pathlib.Path(self.output_directory).mkdir(parents=True, exist_ok=True)
        os.makedirs(self.output_directory, exist_ok=True)  # succeeds even if directory exists.
        # by default save samples with detections every 2 seconds
        self.detections_interval = self.config.get('detections_interval', 2)
        # by default save samples without any detections every half an hour
        self.idle_interval = self.config.get('idle_interval', 60*30)

    def receive_next_sample(self, image, inferences[category, confidence, box]):
        log.info("Pipe element %s received new sample", self.__class__.__name__)
        # ... save samples to local disk
        ... pass notifications to flask server via cross-process queue or pipe or topic
        ... run flask web app in a separate process. It does not need to get in the way of pipeline processing
