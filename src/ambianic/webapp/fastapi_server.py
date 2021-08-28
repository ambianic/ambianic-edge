"""Fastapi based Web services."""
import os
import logging
import time
import pkg_resources
import uvicorn
from pathlib import Path
from requests import get
import yaml
from ambianic import config, DEFAULT_DATA_DIR, __version__
from ambianic.util import ServiceExit, ThreadedJob, ManagedService
from ambianic.webapp.server import samples, config_sources
from ambianic.webapp.fastapi_app import app

log = logging.getLogger(__name__)

# configuration
DEBUG = True


class FastApiJob(ManagedService):
    """A managed web service."""

    def __init__(self, config):
        """Create Fastapi based web service."""
        self.config = config
        data_dir = None
        if config:
            data_dir = config.get('data_dir', None)
        if not data_dir:
            data_dir = DEFAULT_DATA_DIR
        self.uvi_ip_address = '0.0.0.0' # bind to all local IP addresses
        self.uvi_port = 8778
        log.info('starting fastapi/uvicorn web server on %s:%d', ip_address, port)
        # if Ambianic is in DEBUG mode, start FASTAPI/uvicorn in dev mode
        if log.level <= logging.DEBUG:
            self.uvi_reload=True
            self.uvi_debug=True

        app.set_data_dir(data_dir=data_dir)
        self.fastapi_stopped = True
        log.debug('Fastapi process created')

    def start(self, **kwargs):
        """Start service."""
        log.debug('Fastapi starting main loop')
        self.fastapi_stopped = False
        try:
            uvicorn.run(
                app,
                host=self.uvi_ip_address, 
                port=self.uvi_port, 
                reload=self.uvi_reload, 
                debug=self.uvi_debug,
                log_level=log.level, 
                workers=3)
        except ServiceExit:
            log.info('Service exit requested')
        self.fastapi_stopped = True
        log.debug('Fastapi ended main loop')

    def stop(self):
        """Stop service."""
        if not self.fastapi_stopped:
            log.debug('Fastapi stopping main loop')
            self.srv.shutdown()
            log.debug('Fastapi main loop ended')

    def healthcheck(self):
        """Report health status."""
        return time.monotonic(), 'OK'


class FastapiServer(ManagedService):
    """ Thin wrapper around Fastapi constructs.

    Allows controlled start and stop of the web app server
    in a separate process.

    Parameters
    ----------
    config : yaml
        reference to the yaml configuration file

    """

    def __init__(self, config):
        self.config = config
        self.fastapi_job = None

    def start(self, **kwargs):
        log.info('Fastapi server job starting...')
        f = FastapiJob(self.config)
        self.fastapi_job = ThreadedJob(f)
        self.fastapi_job.start()
        log.info('Fastapi server job started')

    def healthcheck(self):
        # Note: Implement actual health check for Fastapi
        # See if the /healthcheck URL returns a 200 quickly
        return time.monotonic(), True

    def heal(self):
        """Heal the server.

        TODO: Keep an eye for potential scenarios that cause this server to
         become unresponsive.
        """

    def stop(self):
        if self.fastapi_job:
            log.info('Fastapi server job stopping...')
            self.fastapi_job.stop()
            self.fastapi_job.join()
            log.info('Fastapi server job stopped.')
