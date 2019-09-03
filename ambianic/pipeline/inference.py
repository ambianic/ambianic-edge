import logging
import time
import re
import os

from edgetpu.detection.engine import DetectionEngine

from . import PipeElement

log = logging.getLogger(__name__)


def load_labels(path):
    p = re.compile(r'\s*(\d+)(.+)')
    with open(path, 'r', encoding='utf-8') as f:
        lines = (p.match(line).groups() for line in f.readlines())
        return {int(num): text.strip() for num, text in lines}


class AiInference(PipeElement):
    """ AiInference is a pipeline element responsible for applying AI (Tensorflow) model inference  """

    def __init__(self, element_config=None):
        PipeElement.__init__(self)

        self.config = element_config
        model = self.config.get('model', None)
        assert model, 'pipeline element ai: requires argument model:'
        assert os.path.isfile(model), 'AI model file does not exist: {}'.format(model)
        labels = self.config.get('labels', None)
        assert os.path.isfile(labels), 'AI model labels file does not exist: {}'.format(labels)
        log.info("Loading AI model %s with labels %s", model, labels)
        self.engine = DetectionEngine(model)
        self.labels = load_labels(labels)
        self.last_time = time.monotonic()
        self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
        log.info("AI model confidence threshold: %.0f%%", self.confidence_threshold*100)

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
        inference_result = []
        for obj in objs:
            x0, y0, x1, y1 = obj.bounding_box.flatten().tolist()
            confidence = obj.score
            label = '%d%% %s' % (percent, self.labels[obj.label_id])
            category = self.labels[obj.label_id]
            inference_result.append((category, confidence, (x0, y0, x1, y1)))
        # pass on the results to the next connected pipe element
        if self.next_element:
          self.next_element.receive_next_sample(image, inference_result)
        # generate_svg(svg_canvas, objs, labels, text_lines)
