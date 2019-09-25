"""Tensorflow image detection wrapper."""
import logging
import time
import re
import os
import abc
import numpy as np
# from importlib import import_module
from tflite_runtime.interpreter import Interpreter
from tflite_runtime.interpreter import load_delegate
from ambianic.pipeline import PipeElement
from PIL import Image, ImageOps

log = logging.getLogger(__name__)

class TFImageDetection(PipeElement):
    """Applies Tensorflow image detection."""

    def __init__(self, element_config=None):
        """Initialize detector with config parameters.

        :Parameters:
        ----------
        element_config : dict from yaml config
            Example:
                model: ai_models/mobilenet_ssd_v2_face.tflite
                labels: ai_models/coco_labels.txt
                confidence_threshold: 0.6
                top-k: 3

        """
        super()
        self._tfengine = TFInferenceEngine(*element_config)
        self._labels = load_labels(self.labels_path())
        self.last_time = time.monotonic()

    def load_labels(self, path):
        p = re.compile(r'\s*(\d+)(.+)')
        with open(path, 'r', encoding='utf-8') as f:
            lines = (p.match(line).groups() for line in f.readlines())
            return {int(num): text.strip() for num, text in lines}

    def resize_to_fit(self, image=None, desired_size=None):
        """Resizes original image to size expected by input tensor.

        :Parameters:
        ----------
        image : PIL.Image
            Input Image for AI model detection.

        desired_size : (width, height)
            Size expected by the AI model.

        Preserves aspect ratio to avoid confusing the AI model with
        an unnatural distortion. Pads resulting image
        with solid black color pixels as necessary.

        Does not modify the original image.

        :Returns:
        -------
        PIL.Image
            Resized image fitting for the AI model input tensor.

        """
        assert image
        assert desired_size
        # old_size[0] is in (width, height) format
        log.debug('current image size = %r', image.size)
        thumb = image.copy()
        thumb.thumbnail(desired_size)
        log.debug('thmubnail image size = %r', thumb.size)
        delta_w = desired_size[0] - thumb.size[0]
        delta_h = desired_size[1] - thumb.size[1]
        padding = (0, 0, delta_w, delta_h)
        new_im = ImageOps.expand(thumb, padding)
        log.debug('new image size = %r', new_im.size)
        assert new_im.size == desired_size
        return new_im

    def detect(self, image):
        """Detect objects in image.

        :Parameters:
        ----------
        image : PIL.Image
            Input image in raw RGB format.

        :Returns:
        -------
        list of tuples
            List of top-k detections above confidence_threshold.
            Each detection is a tuple of:
            (category, confidence, (x0, y0, x1, y1))

        """
        start_time = time.monotonic()
        log.debug("Calling TF engine for inference")

        # NxHxWxC, H:1, W:2
        height = input_details[0]['shape'][1]
        width = input_details[0]['shape'][2]

        img = Image.open(args.image)
        new_im = self.resize_to_fit(image=img, desired_size=(width, height))

        # add N dim
        input_data = np.expand_dims(new_im, axis=0)

        if not self.is_quantized():
            input_data = (np.float32(input_data) - args.input_mean) / args.input_std

        interpreter.set_tensor(input_details[0]['index'], input_data)

        interpreter.invoke()

    	# get output tensor
    	boxes = interpreter.get_tensor(output_details[0]['index'])
    	labels = interpreter.get_tensor(output_details[1]['index'])
    	scores = interpreter.get_tensor(output_details[2]['index'])
    	num = interpreter.get_tensor(output_details[3]['index'])

    	for i in range(boxes.shape[1]):
    		if scores[0, i] > 0.5:
    			box = boxes[0, i, :]
    			x0 = int(box[1] * img_org.shape[1])
    			y0 = int(box[0] * img_org.shape[0])
    			x1 = int(box[3] * img_org.shape[1])
    			y1 = int(box[2] * img_org.shape[0])
    			box = box.astype(np.int)
    			cv2.rectangle(img_org, (x0, y0), (x1, y1), (255, 0, 0), 2)
    			cv2.rectangle(img_org, (x0, y0), (x0 + 100, y0 - 30), (255, 0, 0), -1)
    			cv2.putText(img_org,
    				   str(int(labels[0, i])),
    				   (x0, y0),
    				   cv2.FONT_HERSHEY_SIMPLEX,
    				   1,
    				   (255, 255, 255),
    				   2)

    #	cv2.imwrite('output.jpg', img_org)
    	cv2.imshow('image', img_org)
    	cv2.waitKey(0)
    	cv2.destroyAllWindows()



# Google's Coral classification example:
        output_data = interpreter.get_tensor(output_details[0]['index'])
        results = np.squeeze(output_data)

        top_k_ref = -1*self.top_k
        # sort in ascending score order and grab the last top_k elements
        # starting from the largest score towards the smallest
        # (hence step -1)
        top_k_results = results.argsort()[top_k_ref:][::-1]
        for i in top_k_results:
            if floating_model:
              print('{:08.6f}: {}'.format(float(results[i]), labels[i]))
            else:
              print('{:08.6f}: {}'.format(float(results[i] / 255.0), labels[i]))

#        objs = self.engine.DetectWithImage(
#            image,
#            threshold=self.confidence_threshold,
#            keep_aspect_ratio=True,
#            relative_coord=True,
#            top_k=3)
        log.debug("TF engine returned inference results")
        end_time = time.monotonic()
        inf_time = (end_time - start_time) * 1000
        fps = 1.0/(end_time - self.last_time)
        inf_info = 'Inference: %.2f ms  FPS: %.2f fps'
        log.debug(inf_info, inf_time, fps)
        self.last_time = end_time
        inference_result = []
        for obj in objs:
            x0, y0, x1, y1 = obj.bounding_box.flatten().tolist()
            confidence = obj.score
            category = self.labels[obj.label_id]
            inference_result.append((category, confidence, (x0, y0, x1, y1)))
        return inference_result

    @abc.abstractmethod
    def receive_next_sample(self, image):
        pass
