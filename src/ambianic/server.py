"""Main Ambianic server module."""
import logging
import logging.handlers
import os
import pathlib
import time

from ambianic.pipeline import timeline
from ambianic.pipeline.interpreter import PipelineServer
from ambianic.util import ServiceExit
from ambianic.config_mgm import ConfigChangedEvent
from ambianic import config_manager, logger
from ambianic.webapp.flaskr import FlaskServer

log = logging.getLogger(__name__)

AI_MODELS_DIR = "ai_models"
MANAGED_SERVICE_HEARTBEAT_THRESHOLD = 180  # seconds
MAIN_HEARTBEAT_LOG_INTERVAL = 5
ROOT_SERVERS = {
    'pipelines': PipelineServer,
    'web': FlaskServer,
}

def _configure(env_work_dir=None):
    """Load configuration settings.

    :returns config dict if configuration was loaded without issues.
            None or a specific exception otherwise.
    """
    assert env_work_dir, 'Working directory required.'
    assert os.path.exists(env_work_dir), \
        'working directory invalid: {}'.format(env_work_dir)

    config_manager.stop()

    config = config_manager.load(env_work_dir)
    if config is None:
        return None

    def logging_config_handler(event: ConfigChangedEvent):
        # configure logging
        log.info("Reconfiguring logging")
        logger.configure(config.get("logging"))

    def timeline_config_handler(event: ConfigChangedEvent):
        # configure pipeline timeline event log
        log.info("Reconfiguring pipeline timeline event log")
        timeline.configure_timeline(config.get("timeline"))

    # set callback to react to specific configuration changes
    if config.get("logging", None) is not None:
        config.get("logging").add_callback(logging_config_handler)

    if config.get("timeline", None) is not None:
        config.get("timeline").add_callback(timeline_config_handler)

    # initialize logging
    logging_config_handler(None)
    timeline_config_handler(None)

    return config


class AmbianicServer:
    """Ambianic main server."""

    def __init__(self, work_dir=None):
        """Inititalize server from working directory files.

        :Parameters:
        ----------
        work_dir : string
            The working directory where config and data reside.

        """
        assert work_dir
        self._env_work_dir = work_dir
        # array of managed specialized servers
        self._servers = {}
        self._service_exit_requested = False
        self._latest_heartbeat = time.monotonic()

    def _stop_servers(self, servers):
        log.debug('Stopping servers...')
        for srv in servers.values():
            srv.stop()
        config_manager.stop()

    def _healthcheck(self, servers):
        """Check the health of managed servers."""
        for s in servers.values():
            latest_heartbeat, status = s.healthcheck()
            now = time.monotonic()
            lapse = now - latest_heartbeat
            if lapse > 1:
                # log only if lapse is over 1 second long.
                # otherwise things are OK and we don't want
                # unnecessary log noise
                log.debug('lapse for %s is %f', s.__class__.__name__, lapse)
            if lapse > MANAGED_SERVICE_HEARTBEAT_THRESHOLD:
                log.warning('Server "%s" is not responsive. '
                            'Latest heart beat was %f seconds ago. '
                            'Will send heal signal.',
                            s.__class__.__name__, lapse)
                s.heal()

    def _log_heartbeat(self):
        log.info("Main thread alive.")

    def _heartbeat(self):
        new_time = time.monotonic()
        # print a heartbeat message every so many seconds
        if new_time - self._latest_heartbeat > MAIN_HEARTBEAT_LOG_INTERVAL:
            self._log_heartbeat()
            # this is where hooks to external
            # monitoring services will come in
        self._latest_heartbeat = new_time
        if self._service_exit_requested:
            raise ServiceExit

    def on_config_change(self, event: ConfigChangedEvent):

        root = event.get_root()

        # track changes on root elements
        if len(event.get_paths()) == 1 and (event.get_paths()[0] in ["sources", "ai_models", "pipelines"]):
            log.info("config.%s changed, restarting pipelines",
                     event.get_paths()[0])
            self._servers['pipelines'].trigger_event(event)

        if not root or not root.get_context():
            return

        log.info("Config change: %s", event)

        section_name = root.get_context().get_name()

        if section_name in ["data_dir"]:
            self.stop()
            self.start()

    def start(self):
        """Programmatic start of the main service."""
        print("Starting server...")
        config = _configure(self._env_work_dir)
        if not config:
            log.info('No startup configuration provided. '
                     'Proceeding with defaults.')
        else:
            config.add_callback(self.on_config_change)

        log.info('Starting Ambianic server...')

        # Register the signal handlers
        servers = {}
        # Start the job threads
        try:
            for s_name, s_class in ROOT_SERVERS.items():
                srv = s_class(config=config)
                srv.start()
                servers[s_name] = srv

            self._latest_heartbeat = time.monotonic()

            self._servers = servers
            # Keep the main thread running, otherwise signals are ignored.
            while True:
                time.sleep(0.5)
                self._healthcheck(servers)
                self._heartbeat()

        except ServiceExit:
            log.info('Service exit requested.')
            log.debug('Cleaning up before exit...')
            self._stop_servers(servers)

        log.info('Exiting Ambianic server.')
        return True

    def stop(self):
        """Programmatic stop of the main service."""
        print("Stopping server...")
        log.info("Stopping server...")
        self._service_exit_requested = True
