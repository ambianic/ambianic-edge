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
        PipeElement.__init__(self)
        self.config = element_config
        self.output_directory = self.config.get('output_directory', None)
        assert self.output_directory, 'Pipe element %s: requires argument output_directory:' % self.__class__.__name__

        pathlib.Path(self.output_directory).mkdir(parents=True, exist_ok=True)
        os.makedirs(self.output_directory, exist_ok=True)  # succeeds even if directory exists.

        assert os.path.isfile(model), 'AI model file does not exist: {}'.format(model)
        # by default save samples with detections every 2 seconds
        self.detections_interval = self.config.get('detections_interval', 2)
        # by default save samples without any detections every half an hour
        self.idle_interval = self.config.get('idle_interval', 60*30)

        labels = self.config.get('labels', None)
        assert os.path.isfile(labels), 'AI model labels file does not exist: {}'.format(labels)
        log.info("Loading AI model %s with labels %s", model, labels)
        self.engine = DetectionEngine(model)
        self.labels = load_labels(labels)
        self.last_time = time.monotonic()
        self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
        log.info("AI model confidence threshold: 0:.0f%", self.confidence_threshold)

    def receive_next_sample(self, image):
        log.info("AI inference received new sample")
        start_time = time.monotonic()
        log.info("Calling Coral engine for inference")
        objs = self.engine.DetectWithImage(image, threshold=self.confidence_threshold,
                                    keep_aspect_ratio=True, relative_coord=True,
                                    top_k=3)
        log.info("Coral engine returned inference results")
        end_time = time.monotonic()
        inf_time = (end_time - start_time) * 1000
        fps = 1.0/(end_time - self.last_time)
        inf_info = 'Inference: %.2f ms  FPS: %.2f fps'
        log.info(inf_info, inf_time, fps)
        self.last_time = end_time
        text_lines = inf_info % (inf_time, fps)
        # pass on the results to the next connected pipe element
        if self.next_element:
          self.next_element.receive_next_sample([objs, self.labels, text_lines]) # TODO: clean this up
        # generate_svg(svg_canvas, objs, labels, text_lines)
