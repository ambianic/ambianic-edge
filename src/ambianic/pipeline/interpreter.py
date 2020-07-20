"""Ambianic pipeline interpreter module."""
import logging
from .avsource.av_element import AVSourceElement
import time
import threading
import copy

from ambianic.pipeline.ai.object_detect import ObjectDetector
from ambianic.pipeline.ai.face_detect import FaceDetector
from ambianic.pipeline.store import SaveDetectionSamples
from ambianic.pipeline import PipeElement, HealthChecker
from ambianic.pipeline import timeline
from ambianic import config_mgm, config_manager
from ambianic.util import ThreadedJob, ManagedService, stacktrace


log = logging.getLogger(__name__)

# Pipeline class, overridden by test
PIPELINE_CLASS = None


def get_pipelines(pipelines_config, data_dir=None):
    """Initialize and return pipelines given config parameters.

    :Parameters:
    ----------
    pipelines_config : dict
        Example:
        daytime_front_door_watch:
        - source: *src_front_door_cam
          ...
        - detect_objects: # run ai inference on the input data
          ...

    :Returns:
    -------
    list
        List of configured pipelines.

    """
    pipelines = []
    if pipelines_config:
        for pname, pdef in pipelines_config.items():
            log.debug("PROCESSING START: pipeline: %s", pname)
            pipeline_class = Pipeline if PIPELINE_CLASS is None else PIPELINE_CLASS
            pipe = pipeline_class(pname=pname, pconfig=pdef, data_dir=data_dir)
            log.debug("PROCESSING COMPLETE: pipeline: %s; pipe: %r", pname, pipe)
            pipelines.append(pipe)
    else:
        log.warning('No pipelines configured.')
    log.debug("ALL PIPELINES: %r", pipelines)
    return pipelines


class PipelineServer(ManagedService):
    """Main pipeline interpreter class.

    Responsible for loading, running and overseeing the health
    of all Ambianic pipelines.

    """

    MAX_HEARTBEAT_INTERVAL = 40
    TERMINAL_HEALTH_INTERVAL = MAX_HEARTBEAT_INTERVAL*3

    def __init__(self, config=None):
        """Initialize and configure a PipelineServer.

        :Parameters:
        ----------
        config : dict
            Python representation of the yaml configuration file. Example:
            pipelines:
              # sequence of piped operations for use on front door cam
              daytime_front_door_watch:
                - source: *src_front_door_cam
                  ...
                - detect_objects: # run ai inference on the input data
                  ...
                - save_detections: # save samples from the inference results
                  ...

        """
        self._config = config
        self._threaded_jobs = []
        self._pipelines = []
        if config:
            pipelines_config = config.get('pipelines', None)
            if pipelines_config:
                data_dir = config.get('data_dir', None)
                if not data_dir:
                    log.error('NO "data_dir" in configuration')
                else:
                    log.debug('READING pipelines: data: %s; config: %r',data_dir,pipelines_config)
                    self._pipelines = get_pipelines(pipelines_config,data_dir=data_dir)
                    log.debug('READ pipelines: result: %r',self._pipelines)
                    for pp in self._pipelines:
                        pj = ThreadedJob(pp)
                        self._threaded_jobs.append(pj)
            else:
                log.warning('No "pipelines" in configuration')
        else:
            log.error('NO CONFIGURATION FOUND')

    def _on_terminal_pipeline_health(self, pipeline=None, lapse=None):
        log.error('Pipeline %s in terminal condition. '
                  'Unable to recover.'
                  'Latest heartbeat was %f seconds ago. ',
                  pipeline.name, lapse)

    def _on_pipeline_job_ended(self, threaded_job=None):
        p = threaded_job.job
        log.debug('Pipeline "%s" has ended. '
                  'Removing from health watch.',
                  p.name)
        self._threaded_jobs.remove(threaded_job)

    def healthcheck(self):
        """Check the health of all managed pipelines.

        Return the oldest heartbeat among all managed pipeline heartbeats.
        Try to heal pipelines that haven't reported a heartbeat and awhile.

        :returns: (timestamp, status) tuple with most outdated heartbeat
            and worst known status among managed pipelines
        """
        oldest_heartbeat = time.monotonic()
        # iterate over a copy of jobs, because
        # we may need to remove dead jobs in the loop
        for j in list(self._threaded_jobs):
            # get the pipeline object out of the threaded job wrapper
            p = j.job
            if j.is_alive():
                latest_heartbeat, status = p.healthcheck()
                now = time.monotonic()
                lapse = now - latest_heartbeat
                if lapse > self.TERMINAL_HEALTH_INTERVAL:
                    self._on_terminal_pipeline_health(p, lapse)
                    # more than a reasonable amount of time has passed
                    # since the pipeline reported a heartbeat.
                    # Let's recycle it
                elif lapse > self.MAX_HEARTBEAT_INTERVAL:
                    log.warning('Pipeline "%s" is not responsive. '
                                'Latest heartbeat was %f seconds ago. '
                                'Will attempt to heal it.', p.name, lapse)
                    self.heal_pipeline_job(j)
                if oldest_heartbeat > latest_heartbeat:
                    oldest_heartbeat = latest_heartbeat
            else:
                self._on_pipeline_job_ended(threaded_job=j)
        status = True  # At some point status may carry richer information
        return oldest_heartbeat, status

    def heal(self):
        """Heal the PipelineServer.

        PipelineServer manages its own health as best possible.
        Not much to do here at this time.
        """

    def heal_pipeline_job(self, threaded_job=None):
        assert threaded_job
        pipeline = threaded_job.job
        log.debug('HEALING: pipeline: %r', self)
        threaded_job.heal()
        log.debug('HEALED: pipeline: %r', self)

    def start(self):
        # Start pipeline interpreter threads
        log.debug('STARTING: pipeline: %r', self)
        for tj in self._threaded_jobs:
            tj.start()
        log.debug('STARTED: pipeline: %r', self)

    def stop(self):
        log.debug('STOPPING: pipeline: %r', self)
        # Signal pipeline interpreter threads to close
        for tj in self._threaded_jobs:
            tj.stop()
        # Wait for the pipeline interpreter threads to close...
        for tj in self._threaded_jobs:
            tj.join()
        log.debug('STOPPED: pipeline: %r', self)

class HealingThread(threading.Thread):
    """ A thread focused on healing a broken pipeline. """

    def __init__(self, target=None, on_finished=None):
        assert target, 'Healing target required'
        assert on_finished, 'on_finished callback required'
        threading.Thread.__init__(self, daemon=True)
        self._target = target
        self._on_finished = on_finished

    def run(self):
        log.debug('invoking healing target method %r', self._target)
        try:
            self._target()
        except Exception as e:
            log.warning('Error %r while running healing method %r.',
                        e, self._target)
            log.warning(stacktrace())
        log.debug('invoking healing on_finished method %r', self._on_finished)
        try:
            self._on_finished()
        except Exception as e:
            log.warning('Error %r while calling on_finished method %r.',
                        e, self._on_finished)
            log.warning(stacktrace())


class Pipeline(ManagedService):
    """The main Ambianic data processing structure.

    Data flow is arranged in independent pipelines.
    """

    # valid pipeline operators
    PIPELINE_OPS = {
        'source': AVSourceElement,
        'detect_objects': ObjectDetector,
        'save_detections': SaveDetectionSamples,
        'detect_faces': FaceDetector,
    }

    def _on_unknown_pipe_element(self, name=None):
        log.warning('Pipeline definition has unknown '
                    'pipeline element: %s .'
                    ' Ignoring element and moving forward.',
                    name)

    def __init__(self, pname=None, pconfig=None, data_dir=None):
        """Init and load pipeline config."""
        assert pname, "Pipeline name required"
        self.name = pname
        assert pconfig, "Pipeline config required"
        self.config = pconfig
        self.data_dir = data_dir
        self._pipe_elements = []
        self._latest_heartbeat_time = time.monotonic()
        # in the future status may represent a spectrum of health issues
        self._latest_health_status = True
        self._healing_thread = None
        self._context = timeline.PipelineContext(
            unique_pipeline_name=self.name)
        self._context.data_dir = self.data_dir
        self._event_log = timeline.get_event_log(
            pipeline_context=self._context)
        self.load_elements()

    def load_elements(self):
        """load pipeline elements based on configuration"""
        log.debug('LOAD ELEMENTS: config: %r', self.config)

        source_element_key = [*self.config[0]][0]
        assert source_element_key == 'source', "Pipeline config must begin with a 'source' element instead of {}" .format(source_element_key)

        self._pipe_elements = []
        for _element_config in self.config:

            # copy the dictionary to not modify the configuration reference
            if isinstance(_element_config, (config_mgm.ConfigList, config_mgm.ConfigDict)):
                element_def = _element_config.to_values()
            else:
                # if it is a dict (eg. in tests)
                element_def = copy.deepcopy(_element_config)

            # source: accept just a source_id and take it from sources
            if "source" in element_def:
                is_valid = self.parse_source_config(element_def)
                if not is_valid:
                    log.warning('INVALID source; pipeline: %s; element: %s',self.name,element_def)
                    self._pipe_elements = []
                    break
                else:
                    log.debug('VALID source; pipeline: %s; element: %s',self.name,element_def)

            if "ai_model" in element_def:
                is_valid = self.parse_ai_model_config(element_def)
                if not is_valid:
                    log.warning('INVALID ai_model; pipeline: %s; element: %s',self.name,element_def)
                else:
                    log.debug('VALID ai_model; pipeline: %s; element: %s',self.name,element_def)

            element_name = [*element_def][0]
            assert element_name
            element_config = element_def[element_name]

            # if dealing with a static reference, pass the whole object
            # eg. { [source]: [source-name] }
            if isinstance(element_config, str):
                log.debug('Element config is string')
                element_config = {element_name: element_config}
            else:
                log.debug('Element config: %s',element_config)

            element_class = self.PIPELINE_OPS.get(element_name, None)
            if element_class:
                log.debug('ELEMENT SUCCESS: pipeline %s; name: %s; class: %s',self.name,element_name,element_class)
                element = element_class( **element_config, element_name=element_name, context=self._context, event_log=self._event_log)
                self._pipe_elements.append(element)
            else:
                log.warning('ELEMENT FAILED: pipeline: %s; name: %s; config: %r',self.name,element_name,element_config)
                self._on_unknown_pipe_element(name=element_name)

    def parse_ai_model_config(self, element_def: dict):
        """parse AI model configuration"""
        log.debug('AI MODEL: parsing "ai_model" configuration: %r', element_def)

        # its one
        ai_element = None
        for element_name in element_def:
            # ai_model: accept just a source_id and take it from sources
            if "ai_model" in element_def[element_name]:
                ai_element = element_def[element_name]
                log.debug('AI MODEL: ai_element: %r', ai_element)
                break

        if ai_element is None:
            log.warning('AI MODEL: no "ai_model" defined', element_def)
            return False
        else:
            log.debug('AI MODEL: name: %s; config: %r', element_name, ai_element)

        ai_model_id = None
        if isinstance(ai_element["ai_model"], str):
            ai_model_id = ai_element["ai_model"]
            log.debug('AI MODEL: named: %s', ai_model_id)

        if ai_element["ai_model"] is not None and "ai_model_id" in ai_element["ai_model"]:
            ai_model_id = ai_element["ai_model"]["ai_model_id"]
            log.debug('AI MODEL: existing: %s',ai_model_id)

        if ai_model_id is None:
            log.warning('AI MODEL: no model found')
            return False
        else:
            log.debug('AI MODEL: found model: %s', ai_model_id)

        ai_model = config_manager.get_ai_model(ai_model_id)
        if ai_model is None:
            log.warning('AI MODEL: failed to configure; id: %s',ai_model_id)
            return False
        else:
            log.debug('AI MODEL: configured: id: %s; config: %r',ai_model_id,ai_model)

        # merge the model config but keep the pipe element specific one
        for key, val in ai_model.to_values().items():
            if key not in ai_element:
                log.debug('AI MODEL: adding; model: %s; config: %r',key,val)
                ai_element[key] = val

        # track the id
        ai_element["ai_model_id"] = ai_model_id

        return True

    def parse_source_config(self, element_def: dict):
        """parse source configuration"""

        log.debug('SOURCE: config: %r', element_def)

        # source: accept just a source_id and take it from sources
        if "source" not in element_def:
            log.warning('SOURCE: not source; config: %r', element_def)
            return False

        source_id = None
        if isinstance(element_def["source"], str):
            source_id = element_def["source"]

        if "source_id" in element_def["source"]:
            source_id = element_def["source"]["source_id"]

        if source_id is None:
            log.warning('SOURCE: no "source_id" defined')
            return False
        else:
            log.debug('SOURCE: found: id: %s',source_id)

        # track the source_id
        source = config_manager.get_source(source_id)
        if source is None:
            log.warning('SOURCE: failed to configure; id: %s',source_id)
            return False
        else:
            log.debug('SOURCE: configured; id: %s; config: %r',source_id,source)

        element_def["source"] = source.to_values()
        element_def["source"]["source_id"] = source_id
        log.debug('SOURCE: added; id: %s',source_id)

        return True

    def on_config_change(self, event: config_mgm.ConfigChangedEvent):
        """Callback function invoked on pipeline configuration change"""

        restart = False
        paths = event.get_paths()
        if len(paths) > 0:

            if paths[0] == "sources":
                source = self.config[0]
                source_model = source["source"] if "source" in source else None
                if source_model is None:
                    source_model = source["source_id"] if "source_id" in source else None

                if source_model and (
                        event.get_name() == source_model
                        or len(paths) > 1 and paths[1] == source_model
                ):
                    restart = True

            if paths[0] == "pipelines" and (
                    event.get_name() == self.name
                    or (len(paths) > 1 and paths[1] == self.name)
            ):
                restart = True

            if paths[0] == "ai_models":

                i = 1
                while i < len(self.config):
                    model_type = self.config[i].keys()[0]
                    ai_element = self.config[i][model_type]

                    ai_model_id = ai_element["ai_model"] if "ai_model" in ai_element else None
                    if ai_model_id is None:
                        ai_model_id = ai_element["ai_model_id"] if "ai_model_id" in ai_element else None

                    if (
                        event.get_name() == ai_model_id
                        or (len(paths) > 1 and paths[1] == ai_model_id)
                    ):
                        restart = True
                        break

                    i += 1

        if restart:
            log.info("Pipeline configuration changed, restarting")
            self.restart()

    def restart(self):
        """Restart a pipeline"""
        self.stop()
        self.reset()
        self.start()
        log.info("Pipeline restarted")

    def reset(self):
        """Reset the pipeline elements"""
        self._pipe_elements = []

    def _heartbeat(self):
        """Set the heartbeat timestamp to time.monotonic()."""
        log.debug('Pipeline %s heartbeat signal.', self.name)
        now = time.monotonic()
        lapse = now - self._latest_heartbeat_time
        log.debug('Pipeline %s heartbeat lapse %f', self.name, lapse)
        self._latest_heartbeat_time = now

    def _on_start_no_elements(self):
        return

    def start(self):
        """Start the pipeline loop.

        Run until the pipeline has input from its configured source
        or until a stop() signal is received.
        """
        if len(self._pipe_elements) == 0:
            log.debug('PIPELINE: no pipelines; name: %s; attempting reload...',self.name)
            self.load_elements()

        self.watch_config()

        if len(self._pipe_elements) == 0:
            log.warning('PIPELINE: no pipeline elements; name: %s; class: %s', self.name,self.__class__.__name__)
            return self._on_start_no_elements()

        self._heartbeat()

        # connect pipeline elements as defined by user
        for i in range(1, len(self._pipe_elements)):
            e = self._pipe_elements[i-1]
            assert isinstance(e, PipeElement)
            e_next = self._pipe_elements[i]
            e.connect_to_next_element(e_next)

        # add healthcheck as last element in every pipeline
        last_element = self._pipe_elements[len(self._pipe_elements)-1]
        hc = HealthChecker(health_status_callback=self._heartbeat, element_name='health_check')
        last_element.connect_to_next_element(hc)

        log.debug('PIPELINE: starting pipeline; name: %s; class: %s',self.name,self.__class__.__name__)
        self._pipe_elements[0].start()
        log.debug('PIPELINE: started pipeline; name: %s; class: %s',self.name,self.__class__.__name__)

    def healthcheck(self):
        """Return health vitals status report.

        :Returns:
        -------
        (timestamp, status)
            a tuple of
                monotonically increasing timestamp of the last known healthy
                heartbeat and a status with additional health information.

        """
        return self._latest_heartbeat_time, self._latest_health_status

    def _on_healing_already_in_progress(self):
        log.debug('pipeline %s healing thread in progress.'
                  ' Skipping request. '
                  'Thread id: %d. ',
                  self.name, self._healing_thread.ident)

    def heal(self):
        """Nonblocking asynchronous heal function."""
        # register a heartbeat to prevent looping back
        # into heal while healing
        self._heartbeat()
        if self._healing_thread:
            self._on_healing_already_in_progress()
        else:
            log.debug('pipeline %s launching healing thread...', self.name)
            heal_target = self._pipe_elements[0].heal

            def healing_finished():
                log.debug('pipeline %s healing thread id: %d ended. ',
                          self.name,
                          self._healing_thread.ident)
                self._healing_thread = None
                # let's notify healthchecker that progress is being made
                self._heartbeat()

            # launch healing function in a non-blocking way
            self._healing_thread = HealingThread(target=heal_target,
                                                 on_finished=healing_finished)
            self._healing_thread.start()
            log.debug('pipeline %s launched healing thread.',
                      self.name)

    def stop(self):
        """Stop pipeline processing.

        Disconnect from the source and all other external resources.
        """
        self.unwatch_config()
        log.info("Requesting pipeline elements to stop... %s",
                 self.__class__.__name__)
        if len(self._pipe_elements) > 0:
            self._pipe_elements[0].stop()
        log.info("Completed request to pipeline elements to stop. %s",
                 self.__class__.__name__)

    def watch_config(self):
        """Watch for configuration changes"""

        if not isinstance(
                self.config,
                (config_mgm.ConfigList, config_mgm.ConfigDict)
        ):
            log.warning(
                "Configuration is not reactive, cannot watch for changes")
            return

        config = config_manager.get()
        if config is not None:
            config.add_callback(self.on_config_change)

    def unwatch_config(self):
        """Stop watching for configuration changes"""

        if not isinstance(
                self.config,
                (config_mgm.ConfigList, config_mgm.ConfigDict)
        ):
            return

        config = config_manager.get()
        if config is not None:
            config.remove_callback(self.on_config_change)
