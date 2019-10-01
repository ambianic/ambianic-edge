import logging
import datetime
import os
import pathlib
import json
import uuid

from ambianic.pipeline import PipeElement

log = logging.getLogger(__name__)


class SaveDetectionSamples(PipeElement):
    """Saves AI detection samples to an external storage location."""

    def __init__(self,
                 output_directory='./',
                 positive_interval=2,
                 idle_interval=600,
                 **kwargs):
        """Create SaveDetectionSamples element with the provided arguments.

        :Parameters:
        ----------
        output_directory: *object_detect_dir
        positive_interval: 2 # how often (in seconds) to save samples
                with ANY results above the confidence threshold.
                Default is 2 seconds.
        idle_interval: 600 # how often (in seconds) to save samples
                with NO results above the confidence threshold.
                Default it 10 minutes (600 seconds.)

        """
        super().__init__()
        log.info('Loading pipe element %r ', self.__class__.__name__)
        self._output_directory = output_directory
        assert self._output_directory, \
            'Pipe element %s: requires argument output_directory:' \
            % self.__class__.__name__
        self._output_directory = pathlib.Path(self._output_directory)
        self._output_directory.mkdir(parents=True, exist_ok=True)
        # succeeds even if directory exists.
        os.makedirs(self._output_directory, exist_ok=True)
        # by default save samples with detections every 2 seconds
        di = positive_interval
        self._positive_interval = datetime.timedelta(seconds=di)
        # set the clock to sufficiently outdated timestamp to ensure
        # that we won't miss saving the very first sample
        self._time_latest_saved_detection = \
            datetime.datetime.now() - datetime.timedelta(days=1)
        # by default save samples without any detections every ten minutes
        ii = idle_interval
        self._idle_interval = datetime.timedelta(seconds=ii)
        self._time_latest_saved_idle = self._time_latest_saved_detection

    def _save_sample(self, now, image, inference_result):
        time_prefix = now.strftime("%Y%m%d-%H%M%S-{ftype}.{fext}")
        image_file = time_prefix.format(ftype='image', fext='jpg')
        image_path = self._output_directory / image_file
        json_file = time_prefix.format(ftype='json', fext='txt')
        json_path = self._output_directory / json_file
        inf_json = []
        for category, confidence, box in inference_result:
            log.info('category: %s , confidence: %.0f, box: %s',
                     category,
                     confidence,
                     box)
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
            'id': uuid.uuid4().hex,
            'datetime': now.isoformat(),
            'image': image_file,
            'inference_result': inf_json,
        }
        image.save(image_path)
        # save samples to local disk
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(ai_json, f, ensure_ascii=False, indent=4)
        return image_path, json_path

    def process_sample(self, image=None, inference_result=None, **sample):
        log.debug("Pipe element %s received new sample with keys %s.",
                  self.__class__.__name__,
                  str([*sample]))
        if not image:
            # pass through empty samples to next element
            yield None
        else:
            try:
                log.debug("sample detections: %r", inference_result)
                now = datetime.datetime.now()
                if inference_result:
                    # non-empty result, there is a detection
                    # let's save it if its been longer than
                    # the user specified positive_interval
                    if now - self._time_latest_saved_detection >= \
                      self._positive_interval:
                        self._save_sample(now, image, inference_result)
                        self._time_latest_saved_detection = now
                else:
                    # non-empty result, there is a detection
                    # let's save it if its been longer than
                    #  the user specified positive_interval
                    if now - self._time_latest_saved_idle >= \
                      self._idle_interval:
                        self._save_sample(now, image, inference_result)
                        self._time_latest_saved_idle = now
            except Exception as e:
                log.warning('Error %r while saving sample %r',
                            e, sample)
            finally:
                # pass on the sample to the next pipe element if there is one
                processed_sample = {
                    'image': image,
                    'inference_result': inference_result
                }
                log.debug('Passing sample on: %r ', processed_sample)
                yield processed_sample
