"""Main Ambianic server module."""
import logging
import logging.handlers
import os
import pathlib
import time
from watchdog.observers import Observer

from ambianic.pipeline import timeline
from ambianic.pipeline.interpreter import PipelineServer
from ambianic.util import ServiceExit
from ambianic import logger, config, get_config_file, get_secrets_file, load_config
from ambianic.webapp.flaskr import FlaskServer

log = logging.getLogger(__name__)

AI_MODELS_DIR = "ai_models"
MANAGED_SERVICE_HEARTBEAT_THRESHOLD = 180  # seconds
MAIN_HEARTBEAT_LOG_INTERVAL = 5
ROOT_SERVERS = {
    'pipelines': PipelineServer,
    'web': FlaskServer,
}

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
        self.init()

    def init(self):
        # array of managed specialized servers
        self._servers = {}
        self._service_exit_requested = False
        self._service_restart_requested = False
        self._latest_heartbeat = time.monotonic()
        self.config_observer = None
        self.watching_config = False

    def stop_watch_config(self):
        if self.watching_config:
            self.config_observer.stop()
            self.config_observer.join()
        self.watching_config = False
        self.config_observer = None

    def start_watch_config(self):
        if self.watching_config:
            self.stop_watch_config()
        self.config_observer = Observer()
        config_paths = [
            get_config_file(),
            get_secrets_file(),
        ]
        for filepath in config_paths:
            if not os.path.exists(filepath):
                log.warning(
                    "File %s not found, it will not be watched for changes." %
                    filepath
                )
                continue
            self.config_observer.schedule(
                self,
                filepath,
                recursive=False
            )

        self.config_observer.start()
        self.watching_config = True

    def _stop_servers(self, servers):
        log.debug('Stopping servers...')
        for name, srv in servers.items():
            srv.stop()
            srv = None
            servers[name] = None
        self.stop_watch_config()

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

    def dispatch(self, event):
        """Callback called when a config file changes"""
        log.info("Configuration file changed, stopping Ambianic server")
        self.restart()

    def restart(self):
        self._service_restart_requested = True
        self.stop()

    def start(self):
        """Programmatic start of the main service."""

        assert os.path.exists(self._env_work_dir)

        self.start_watch_config()

        logger.configure(config.get("logging"))
        timeline.configure_timeline(config.get("timeline"))

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

            if self._service_restart_requested:
                self._service_restart_requested = False
                self.init()
                load_config(get_config_file())
                return self.start()

        log.info('Exiting Ambianic server.')
        return True

    def stop(self):
        """Programmatic stop of the main service."""
        log.info("Stopping server...")
        self._service_exit_requested = True
