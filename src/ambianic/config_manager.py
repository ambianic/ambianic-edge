"""Centralized configuration manager."""

import yaml
import os
import logging
from time import sleep
from ambianic import get_work_dir
import threading

CONFIG_FILE = "config.yaml"
SECRETS_FILE = "secrets.yaml"


class ConfigurationManager:
    """Configuration manager handles configuration centrally and
       notify via callbacks of changes
    """

    def __init__(self, work_dir=None):
        self.__config = None
        self.watch_files = {}
        self.watch_thread = None
        self.watch_lock = threading.RLock()
        self.log = logging.getLogger()
        self.handlers = []
        if work_dir is not None:
            self.load(work_dir)

    def stop(self):
        """Stop the config manager"""
        self.unwatch_files()
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
        """Poll for file changes"""
        while True:
            if len(self.watch_files) == 0:
                break
            with self.watch_lock:
                try:
                    for filename, last_mtime in self.watch_files.items():
                        mtime = os.path.getmtime(filename)
                        if last_mtime is None:
                            self.watch_files[filename] = mtime
                            continue
                        if last_mtime != mtime:
                            self.log.info("File change detected: %s", filename)
                            self.watch_files[filename] = mtime
                            self.load(self.work_dir)
                except Exception as ex:
                    self.log.warning(
                        "Exception watching file %s: %s", filename, ex)
                    pass
        sleep(1)

    def watch_file(self, filename):
        """Add a file to the watch list"""

        if filename in self.watch_files.keys():
            return

        if not os.path.exists(filename):
            return

        with self.watch_lock:
            self.log.info("Watching %s for changes", filename)
            self.watch_files[filename] = None

        if self.watch_thread is None:
            self.watch_thread = threading.Thread(
                target=self.__watcher,
                # args=(self,)
            )
            self.watch_thread.start()

    def unwatch_files(self):
        """Remove a file from the watch list"""
        with self.watch_lock:
            self.watch_files = {}

    def save(self, config):
        """Save configuration to files"""
        if config is not None:
            return

        with self.watch_lock:
            with open(self.get_config_file(), 'w') as fh:
                yaml.dump(config, fh, default_flow_style=False)

    def get_config_file(self):
        """Return the config file path"""
        return os.path.join(self.work_dir, CONFIG_FILE)

    def get_secrets_file(self):
        """Return the secrets file path"""
        return os.path.join(self.work_dir, SECRETS_FILE)

    def load(self, work_dir):
        """Load configuration from file"""

        assert os.path.exists(work_dir), \
            'working directory invalid: {}'.format(work_dir)

        self.work_dir = work_dir

        secrets_file = self.get_secrets_file()
        self.watch_file(secrets_file)

        config_file = self.get_config_file()
        self.watch_file(config_file)

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

            self.log.debug('loaded config from %r: %r', CONFIG_FILE, config)
            return self.update(config)
        except FileNotFoundError:
            self.log.warning('Configuration file not found: %s', config_file)
            self.log.warning(
                'Please provide a configuration file and restart.')
        except Exception as e:
            self.log.exception('Configuration Error!', e, exc_info=True)
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
        return self.__config

    def update(self, new_config):
        """Update configurations

        :Parameters:
        ----------
        new_config : dictionary
            The new configurations to apply

        :Returns:
        -------
        config: dictionary
            Return the current configurations.

        """
        self.__config = new_config

        for handler in self.handlers:
            handler(self.__config)

        return self.__config


__config_manager = ConfigurationManager()


def get_config_manager():
    """Return the configuration manager singleton"""
    global __config_manager

    if __config_manager is None:
        __config_manager = ConfigurationManager()

    return __config_manager


def reset_config_manager():
    """Reset the configuration manager singleton"""
    global __config_manager

    if __config_manager is not None:
        __config_manager.stop()
        __config_manager = None

    return get_config_manager()


def get_config():
    """Return the current configuration"""
    return get_config_manager().get()


def save_config(new_config):
    """Update the current configuration"""
    return get_config_manager().save(new_config)
