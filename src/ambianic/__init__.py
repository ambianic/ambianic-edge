
import os
from ambianic.config_mgm import ConfigurationManager

DEFAULT_WORK_DIR = '/workspace'

config_manager = ConfigurationManager()
server_instance = None


def get_work_dir():
    """Retrieve the ambianic working directory"""
    env_work_dir = os.environ.get('AMBIANIC_DIR', os.getcwd())
    if not env_work_dir:
        env_work_dir = DEFAULT_WORK_DIR
    return env_work_dir
