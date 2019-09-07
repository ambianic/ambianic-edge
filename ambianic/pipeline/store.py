import logging
import datetime
import os
import pathlib
import json

from . import PipeElement

log = logging.getLogger(__name__)


class SaveSamples(PipeElement):
    """ Saves samples to an external storage location """

    def __init__(self, element_config=None):
        super()
        log.info('Loading pipe element: %s with config %s', self.__class__.__name__, element_config)
        PipeElement.__init__(self)
        self.config = element_config
        self.output_directory = self.config.get('output_directory', None)
        assert self.output_directory, 'Pipe element %s: requires argument output_directory:' % self.__class__.__name__
        self.output_directory = pathlib.Path(self.output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        os.makedirs(self.output_directory, exist_ok=True)  # succeeds even if directory exists.
        # by default save samples with detections every 2 seconds
        di = float(self.config.get('positive_interval', 2))
        self.positive_interval = datetime.timedelta(seconds=di)
        # set the clock to sufficiently outdated timestamp to ensure that we won't miss saving the very first sample
        self.time_latest_saved_detection = datetime.datetime.now() - datetime.timedelta(days=1)
        # by default save samples without any detections every ten minutes
        ii = float(self.config.get('idle_interval', 600))
        self.idle_interval = datetime.timedelta(seconds=ii)
        self.time_latest_saved_idle = self.time_latest_saved_detection

    def _save_sample(self, now, image, inference_result):
        time_prefix = now.strftime("%Y%m%d-%H%M%S-{ftype}.{fext}")
        image_file = time_prefix.format(ftype='image', fext='jpg')
        image_path = self.output_directory / image_file
        json_file = time_prefix.format(ftype='json', fext='txt')
        json_path = self.output_directory / json_file
        inf_json = []
        for category, confidence, box in inference_result:
            log.info('category: %s , confidence: %.0f, box: %s', category, confidence, box)
            one_inf = {
                'category': category,
                'confidence': float(confidence),
                'box': {
                    'xmin': float(box[0]),
                    'ymin': float(box[1]),
                    'xmax': float(box[2]),
                    'ymax': float(box[3]),
                }
            }
            inf_json.append(one_inf)

        ai_json = {
            'datetime': now.isoformat(),
            'image': image_file,
            'inference_result': inf_json,
        }
        image.save(image_path)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(ai_json, f, ensure_ascii=False, indent=4)
        # ... save samples to local disk

    def receive_next_sample(self, **sample):
        log.debug("Pipe element %s received new sample with keys %s.", self.__class__.__name__, str([*sample]))
        if not sample:
            # pass through empty samples to next element
            if self.next_element:
                self.next_element.receive_next_sample()
        else:
            try:
                image = sample['image']
                inference_result = sample.get('inference_result', None)
                log.debug("sample: %s", str(inference_result))
                now = datetime.datetime.now()
                if inference_result:
                    # non-empty result, there is a detection
                    # let's save it if its been longer than the user specified positive_interval
                    if now - self.time_latest_saved_detection >= self.positive_interval:
                        self._save_sample(now, image, inference_result)
                        self.time_latest_saved_detection = now
                else:
                    # non-empty result, there is a detection
                    # let's save it if its been longer than the user specified positive_interval
                    if now - self.time_latest_saved_idle >= self.idle_interval:
                        self._save_sample(now, image, inference_result)
                        self.time_latest_saved_idle = now
                # pass on the sample to the next pipe element if there is one
                if self.next_element:
                    log.debug('Pipe element %s passing sample to next pipe element %s',
                              self.__class__.__name__, self.next_element.__class__.__name__)
                    self.next_element.receive_next_sample(image=image, inference_result=inference_result)
            except Exception as e:
                log.warning('Error "%s" while processing sample. Dropping sample: %s', str(e), str(sample))



