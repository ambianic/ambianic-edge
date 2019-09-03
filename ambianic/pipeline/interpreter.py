import logging
from .gstreamer import InputStreamProcessor
from ambianic.pipeline.ai.object_detect import ObjectDetect
from ambianic.pipeline.ai.face_detect import FaceDetect
from .store import SaveSamples
from . import PipeElement

log = logging.getLogger(__name__)


def get_pipelines(config):
    pps = config['pipelines']
    pipelines = []
    for pname, pdef in pps.items():
        log.info("loading %s pipeline configuration", pname)
        proc = Pipeline(pname=pname, pconfig=pdef)
        pipelines.append(proc)
    return pipelines


class Pipeline:
    """ The main Ambianic processing structure. Data flow is arranged in independent pipelines. """

    # valid pipeline operators
    PIPELINE_OPS = {
        'source': InputStreamProcessor,
        'detect_objects': ObjectDetect,
        'save_samples': SaveSamples,
        'detect_faces': FaceDetect,
    }

    def __init__(self, pname=None, pconfig=None):
        """ Load pipeline config """
        assert pname, "Pipeline name required"
        self.name = pname
        assert pconfig, "Pipeline config required"
        self.config = pconfig
        assert self.config[0]["source"], "Pipeline config must begin with a source element"
        self.pipe_elements = []
        self.state = False
        for element_def in self.config:
            log.info('Pipeline %s loading next element: %s', pname, element_def)
            element_name = [*element_def][0]
            element_config = element_def[element_name]
            element_class = self.PIPELINE_OPS.get(element_name, None)
            if element_class:
                log.info('Pipeline %s adding element %s with config %s', pname, element_name, element_config)
                element = element_class(element_config)
                self.pipe_elements.append(element)
            else:
                log.warning('Pipeline definition has unknown pipeline element: %s .'
                            ' Ignoring element and moving forward.', element_name)
        return

    def start(self):
        """
            Starts a thread that iteratively and in order of definitions feeds
            each element the output of the previous one. Stops the pipeline when a stop signal is received.
        """

        log.info("Starting %s main pipeline loop", self.__class__.__name__)

        if not self.pipe_elements:
            return

        # connect pipeline elements as defined by user
        for i in range(1, len(self.pipe_elements)):
            e = self.pipe_elements[i-1]
            assert isinstance(e, PipeElement)
            e_next = self.pipe_elements[i]
            assert isinstance(e_next, PipeElement)
            e.connect_to_next_element(e_next)

        self.pipe_elements[0].start()

        log.info("Stopped %s", self.__class__.__name__)
        return

    def stop(self):
        log.info("Stopping %s", self.__class__.__name__)
        self.pipe_elements[0].stop()
        return
