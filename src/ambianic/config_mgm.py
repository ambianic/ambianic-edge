"""Centralized configuration manager."""

import os
import logging
from time import sleep
import threading
import yaml
from inotify_simple import INotify, flags


class ConfigurationManager:
    """Configuration manager handles configuration centrally and
       notify via callbacks of changes
    """

    def __init__(self, work_dir=None):

        self.CONFIG_FILE = "config.yaml"
        self.SECRETS_FILE = "secrets.yaml"

        self.lock = threading.RLock()
        self.__config = None
        self.watch_thread = None
        self.watch_event = threading.Event()
        self.log = logging.getLogger()
        self.handlers = []

        if work_dir is not None:
            self.load(work_dir)

    def stop(self):
        """Stop the config manager"""
        self.handlers = []
        with self.lock:
            self.__config = None
        self.watch_stop()
        if self.watch_thread is not None:
            self.watch_thread.join()
            self.watch_thread = None

    def register_handler(self, callback):
        """Register a callback to trigger when there is a configuration update"""
        self.handlers.append(callback)

    def unregister_handler(self, callback):
        """Remove a callback from the configuration updates handlers"""
        self.handlers.remove(callback)

    def __watcher(self):
        """Watch for file changes"""
        inotify = INotify()
        wd = inotify.add_watch(self.work_dir, flags.MODIFY)
        while not self.watch_event.is_set():
            for event in inotify.read(timeout=100, read_delay=100):
                for filename in [self.CONFIG_FILE, self.SECRETS_FILE]:
                    if event.name == filename:
                        self.log.info("File change detected: %s", filename)
                        self.load(self.work_dir)
                        break
        # stop watching
        inotify.rm_watch(wd)

    def watch_start(self):
        """Start watching fs for changes"""
        if self.watch_thread is None:
            self.watch_event.clear()
            self.watch_thread = threading.Thread(target=self.__watcher)
            self.watch_thread.start()

    def watch_stop(self):
        """Stop watching fs for changes"""
        self.watch_event.set()

    def save(self, config):
        """Save configuration to file"""
        if config is not None:
            return

        with open(self.get_config_file(), 'w') as fh:
            yaml.dump(config, fh, default_flow_style=False)

    def get_config_file(self):
        """Return the config file path"""
        return os.path.join(self.work_dir, self.CONFIG_FILE)

    def get_secrets_file(self):
        """Return the secrets file path"""
        return os.path.join(self.work_dir, self.SECRETS_FILE)

    def load(self, work_dir):
        """Load configuration from file"""

        assert os.path.exists(work_dir), \
            'working directory invalid: {}'.format(work_dir)

        self.work_dir = work_dir
        self.watch_start()

        secrets_file = self.get_secrets_file()
        config_file = self.get_config_file()

        try:
            if os.path.isfile(secrets_file):
                with open(secrets_file) as sf:
                    secrets_config = sf.read()
            else:
                secrets_config = ""
                self.log.warning('Secrets file not found. '
                                 'Proceeding without it: %s',
                                 secrets_file)
            with open(config_file) as cf:
                base_config = cf.read()
                all_config = secrets_config + "\n" + base_config
            config = yaml.safe_load(all_config)

            self.log.debug('loaded config from %r: %r',
                           self.CONFIG_FILE, config)

            return self.set(config)

        except FileNotFoundError:
            self.log.warning('Configuration file not found: %s', config_file)
            self.log.warning(
                'Please provide a configuration file and restart.')
        except Exception as e:
            self.log.exception('Configuration Error!', exc_info=True)
        return None

    def get(self):
        """Get stored configuration.

        Parameters
        ----------

        Returns
        -------
        dictionary
            Returns a dictionary with current configurations.

        """
        with self.lock:
            return self.__config

    def set(self, new_config):
        """Set configuration

        :Parameters:
        ----------
        new_config : dictionary
            The new configurations to apply

        :Returns:
        -------
        config: dictionary
            Return the current configurations.

        """
        with self.lock:
            self.__config = new_config

        for handler in self.handlers:
            handler(self.__config)

        return self.__config
