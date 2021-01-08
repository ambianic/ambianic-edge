"""Pipeline sample storage elements."""
import logging
import datetime
import pathlib
import json
import uuid
from typing import Iterable

from ambianic import DEFAULT_DATA_DIR
from ambianic.pipeline import PipeElement
from ambianic.notification import Notification, NotificationHandler

log = logging.getLogger(__name__)


class SaveDetectionSamples(PipeElement):
    """Saves AI detection samples to an external storage location."""

    def __init__(self,
                 positive_interval=2,
                 idle_interval=600,
                 notify=None,
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
        super().__init__(**kwargs)

        log.info('Loading pipe element %r ', self.__class__.__name__)
        if self.context:
            self._sys_data_dir = self.context.data_dir
        else:
            self._sys_data_dir = DEFAULT_DATA_DIR
        self._output_directory = pathlib.Path(self._sys_data_dir)
        assert self._output_directory, \
            'Pipe element %s: requires argument output_directory:' \
            % self.__class__.__name__
        # mkdir succeeds even if directory exists.
        self._output_directory.mkdir(parents=True, exist_ok=True)
        # add unique suffix to output dir to avvoid collisions
        now = datetime.datetime.now()
        dir_prefix = 'detections/'
        dir_time = now.strftime("%Y%m%d-%H%M%S.%f%z")
        self._rel_data_dir = dir_prefix + dir_time
        self._output_directory = self._output_directory / self._rel_data_dir
        self._output_directory.mkdir(parents=True, exist_ok=True)
        self._output_directory = self._output_directory.resolve()
        log.debug('output_directory: %r', self._output_directory)
        # os.makedirs(self._output_directory, exist_ok=True)
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
        
        # setup notification handler
        self.notification = None
        self.notification_config = notify        
        if self.notification_config is not None and self.notification_config.get("providers"):
            self.notification = NotificationHandler()

    def _save_sample(self,
                     inf_time=None,
                     image=None,
                     thumbnail=None,
                     inference_result=None,
                     inference_meta=None):
        time_prefix = inf_time.strftime("%Y%m%d-%H%M%S.%f%z-{suffix}.{fext}")
        image_file = time_prefix.format(suffix='image', fext='jpg')
        image_path = self._output_directory / image_file
        thumbnail_file = time_prefix.format(suffix='thumbnail', fext='jpg')
        thumbnail_path = self._output_directory / thumbnail_file
        json_file = time_prefix.format(suffix='inference', fext='json')
        json_path = self._output_directory / json_file
        inf_json = []
        if inference_result:
            for inf in inference_result:
                label, confidence = inf[0:2]

                if isinstance(inf[2], (list, tuple)):
                    # Process inference for person/object detection model
                    box = inf[2]
                    log.info('label: %s , confidence: %.0f, box: %s',
                            label,
                            confidence,
                            box)
                    one_inf = {
                        'label': label,
                        'confidence': float(confidence),
                        'box': {
                            'xmin': float(box[0]),
                            'ymin': float(box[1]),
                            'xmax': float(box[2]),
                            'ymax': float(box[3]),
                        }
                    }
                    inf_json.append(one_inf)
                else:
                    # Process inference for Fall detection model
                    angle_diff_posenet = inf[2]
                    log.info('label: %s , confidence: %.0f, angle difference: %s',
                            label,
                            confidence,
                            angle_diff_posenet)
                    one_inf = {
                        'label': label,
                        'confidence': float(confidence),
                        'angle_diff': angle_diff_posenet
                    }
                    inf_json.append(one_inf)

        save_json = {
            'id': uuid.uuid4().hex,
            'datetime': inf_time.isoformat(),
            'image_file_name': image_file,
            'thumbnail_file_name': thumbnail_file,
            'json_file_name': json_file,
            # rel_dir is relative to system data dir
            # this will be important when resloving REST API data
            # file serving
            'rel_dir': self._rel_data_dir,
            'inference_result': inf_json,
            'inference_meta': inference_meta
        }
        image.save(image_path)
        thumbnail.save(thumbnail_path)
        # save samples to local disk
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(save_json, f, ensure_ascii=False, indent=4)
        # e = PipelineEvent('Detected Objects', type='ObjectDetection')
        self.event_log.info('Detection Event', save_json)
        log.debug("Saved sample (detection event): %r ", save_json)
        self.notify(save_json)
        return image_path, json_path

    def process_sample(self, **sample) -> Iterable[dict]:
        """Process next detection sample."""
        image = sample.get('image', None)
        thumbnail = sample.get('thumbnail', None)
        inference_result = sample.get('inference_result', None)
        inference_meta = sample.get('inference_meta', None)
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
                        self._save_sample(inf_time=now,
                                          image=image,
                                          thumbnail=thumbnail,
                                          inference_result=inference_result,
                                          inference_meta=inference_meta)
                        self._time_latest_saved_detection = now
                else:
                    # empty result, there is no detection
                    # let's save a sample if its been longer than
                    #  the user specified idle_interval
                    if now - self._time_latest_saved_idle >= \
                      self._idle_interval:
                        self._save_sample(inf_time=now,
                                          image=image,
                                          thumbnail=thumbnail,
                                          inference_result=inference_result,
                                          inference_meta=inference_meta)
                        self._time_latest_saved_idle = now
            except Exception as e:
                log.exception('Error %r while saving sample %r',
                              e, sample)
            finally:
                # pass on the sample to the next pipe element if there is one
                processed_sample = {
                    'image': image,
                    'inference_result': inference_result
                }
                log.debug('Passing sample on: %r ', processed_sample)
                yield processed_sample

    def notify(self, save_json: dict):
        if self.notification is None:
            return
        log.debug("Sending notification(s)..")
        # TODO extract inference data
        for inference_result in save_json['inference_result']:
            data = {
                'id': save_json['id'],
                'label': inference_result['label'],
                'confidence': inference_result['confidence'],
                'datetime': save_json['datetime'],
            }
            notification = Notification(data=data, providers=self.notification_config["providers"])
            self.notification.send(notification)