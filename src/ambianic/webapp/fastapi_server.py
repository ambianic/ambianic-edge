"""Fastapi based Web services."""
import os
import logging
import time
import pkg_resources
import uvicorn
from pathlib import Path
from requests import get
import yaml
import asyncio
from ambianic import config, DEFAULT_DATA_DIR, __version__
from ambianic.util import ServiceExit, ThreadedJob, ManagedService
from ambianic.webapp.server import timeline_dao, config_sources
from ambianic.webapp.fastapi_app import set_data_dir
from multiprocessing import Process

log = logging.getLogger(__name__)

# configuration
DEBUG = True


class FastapiJob(ManagedService):
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
        # if Ambianic is in DEBUG mode, start FASTAPI/uvicorn in dev mode
        if log.level <= logging.DEBUG:
            self.uvi_reload=True
            self.uvi_debug=True

        set_data_dir(data_dir=data_dir)
        self.fastapi_stopped = True
        log.debug('Fastapi process created')

    def start(self, **kwargs):
        """Start service."""
        log.debug('Fastapi starting main loop')
        self.fastapi_stopped = False
        log.info(f'starting fastapi/uvicorn web server on {self.uvi_ip_address}:{self.uvi_port}')
        # there are open discussions on programmtically starting and shutting down uvicorn
        # ref: https://github.com/encode/uvicorn/discussions/1103
        # ref: https://stackoverflow.com/questions/57412825/how-to-start-a-uvicorn-fastapi-in-background-when-testing-with-pytest
        self.uvi = Process(target=uvicorn.run,
                        args=('ambianic.webapp.fastapi_app',),
                        kwargs={
                            "host": self.uvi_ip_address, 
                            "port": self.uvi_port, 
                            "reload": self.uvi_reload, 
                            "reload_dirs": "src",
                            "debug": self.uvi_debug,
                            "log_level": log.level, 
                            "workers": 3},
                        daemon=False)
        self.uvi.start()            

    def stop(self):
        """Stop service."""
        self.fastapi_stopped = True
        self.uvi.terminate()
        log.debug('Fastapi/uvicorn exited. $$$$$$$\n$$$$$$$\n$$$$$$$\n$$$$$$$\n$$$$$$$\n$$$$$$$\n')
        pass


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
        self.fastapi_job = FastapiJob(self.config)
        # not using thread due to uvicorn multi-threading startup issue
        # ref: https://github.com/encode/uvicorn/issues/506
        # self.fastapi_job = ThreadedJob(job=f)
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
            # not running a threaded job due to uvicorn issue. See above.
            # self.fastapi_job.join()
            log.info('Fastapi server job stopped.')
