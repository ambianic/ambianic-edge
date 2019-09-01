# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A demo which runs object detection on camera frames.

export TEST_DATA=/usr/lib/python3/dist-packages/edgetpu/test_data

Run face detection model:
python3 -m edgetpuvision.detect \
  --model ${TEST_DATA}/mobilenet_ssd_v2_face_quant_postprocess_edgetpu.tflite

Run coco model:
python3 -m edgetpuvision.detect \
  --model ${TEST_DATA}/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite \
  --labels ${TEST_DATA}/coco_labels.txt
"""
import time
import re
import os
import logging
from edgetpu.detection.engine import DetectionEngine
import ambianic
from .gstreamer import InputStreamProcessor
from .inference import AiInference

DEFAULT_IMAGE_DETECTION_MODEL = {
    'graph': 'mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite',
    'labels': 'coco_labels.txt',
}

log = logging.getLogger(__name__)

def load_labels(path):
    p = re.compile(r'\s*(\d+)(.+)')
    with open(path, 'r', encoding='utf-8') as f:
       lines = (p.match(line).groups() for line in f.readlines())
       return {int(num): text.strip() for num, text in lines}

def shadow_text(dwg, x, y, text, font_size=20):
    dwg.add(dwg.text(text, insert=(x+1, y+1), fill='black', font_size=font_size))
    dwg.add(dwg.text(text, insert=(x, y), fill='white', font_size=font_size))

def generate_svg(dwg, objs, labels, text_lines):
    width, height = dwg.attribs['width'], dwg.attribs['height']
    for y, line in enumerate(text_lines):
        shadow_text(dwg, 10, y*20, line)
    for obj in objs:
        x0, y0, x1, y1 = obj.bounding_box.flatten().tolist()
        x, y, w, h = x0, y0, x1 - x0, y1 - y0
        x, y, w, h = int(x * width), int(y * height), int(w * width), int(h * height)
        percent = int(100 * obj.score)
        label = '%d%% %s' % (percent, labels[obj.label_id])
        shadow_text(dwg, x, y - 5, label)
        dwg.add(dwg.rect(insert=(x,y), size=(w, h),
                        fill='red', fill_opacity=0.3, stroke='white'))
        #print("SVG canvas width: {w}, height: {h}".format(w=width,h=height))
        #dwg.add(dwg.rect(insert=(0,0), size=(width, height),
        #                fill='green', fill_opacity=0.2, stroke='white'))


class Pipe:
    def __init__(self, pipe_conf=None):
        assert pipe_conf, 'Pipe configuration required.'

class Pipeline:

    # valid pipeline operators
    PIPELINE_OPS = {
        'source': InputStreamProcessor,
        'ai': AiInference,
    }

    def __init__(self, pname=None, pdef=None):
        """ Load pipeline definition """
        assert pname, "Pipeline name required"
        self.name = pname
        assert pdef, "Pipeline definition required"
        self.definition = pdef
        assert self.definition[0]["source"], "Pipeline definition must begin with a source element"
        self.pipeline_ops = {}
        for op_def in self.definition[1:]:
            log.info('pipile loading next operator: %s', op_def)
            log.info('pipile operator *: %s', [*op_def])
            op_name = [*op_def][0]
            op_conf = op_def[op_name]
            op_class = self.PIPELINE_OPS.get(op_name, None)
            if op_class:
                log.info('pipeline %s adding operator %s', pname, op_name)
                op = op_class(op_def)
                self.pipeline_ops
            else:
                log.warning('unknown pipeline operation: %s ', op_name)
        return


    def start(self):
        log.info("Starting %s ", self.__class__.__name__)
        default_model_dir = ambianic.AI_MODELS_DIR
        default_model = '' # TODO: Read from config
        default_labels = '' # TODO: Read from config

        ai_models = self.config.get('ai_models', None)
        model = None
        if not ai_models:
            model = DEFAULT_IMAGE_DETECTION_MODEL
        else:
            model = ai_models.get('image_detection', None)
            if not model:
                model = DEFAULT_IMAGE_DETECTION_MODEL
        graph_file = model['graph']
        if not os.path.isfile(graph_file):
            ValueError('AI model %s graph file does not exist: %s')
        labels_file = model['labels']
        if not os.path.isfile(labels_file):
            ValueError('AI model %s labels file does not exist: %s')
        log.info("Loading AI model graph %s with labels %s", graph_file, labels_file)

        engine = DetectionEngine(graph_file)
        labels = load_labels(labels_file)

        last_time = time.monotonic()

        def inference_callback(image, svg_canvas):
          nonlocal last_time
          start_time = time.monotonic()
          objs = engine.DetectWithImage(image, threshold=args.threshold,
                                        keep_aspect_ratio=True, relative_coord=True,
                                        top_k=args.top_k)
          end_time = time.monotonic()
          inf_time = (end_time - start_time) * 1000
          fps = 1.0/(end_time - last_time)
          log.info('Inference: %.2f ms  FPS: %.2f fps', inf_time, fps)
          last_time = end_time
          generate_svg(svg_canvas, objs, labels, text_lines)

        result = self.input_processor.run_pipeline(inference_callback)
        log.info("Stopped %s", self.__class__.__name__)

    def stop(self):
        log.info("Stopping %s", self.__class__.__name__)
        self.input_processor.stop_pipeline()
