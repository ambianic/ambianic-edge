"""Centralized configuration manager."""

import yaml
import os
import logging
from ambianic import get_work_dir

CONFIG_FILE = "config.yaml"
SECRETS_FILE = "secrets.yaml"


class ConfigurationManager:
    """Configuration manager handles configuration centrally and
       notify via callbacks of changes
    """

    def __init__(self, work_dir=None):

        self.__config = None
        self.log = logging.getLogger()
        self.handlers = []
        if work_dir is not None:
            self.load(work_dir)

    def register_handler(self, callback):
        """Register a callback to trigger when there is a configuration update"""
        self.handlers.append(callback)

    def unregister_handler(self, callback):
        """Remove a callback from the configuration updates handlers"""
        self.handlers.remove(callback)

    def load(self, work_dir=None):
        """Load configuration from file"""

        assert os.path.exists(work_dir), \
            'working directory invalid: {}'.format(work_dir)

        secrets_file = os.path.join(work_dir, SECRETS_FILE)
        config_file = os.path.join(work_dir, CONFIG_FILE)

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
    return __config_manager


def get_config():
    """Return the current configuration"""
    return __config_manager.get()


def update_config(new_config):
    """Update the current configuration"""
    return __config_manager.update(new_config)
