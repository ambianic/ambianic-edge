import os
from ambianic import config_util

DEFAULT_WORK_DIR = '/workspace'
DEFAULT_DATA_DIR = './data'

server_instance = None

config = config_util.get_default_config()

def get_work_dir():
    """Retrieve the ambianic working directory"""
    env_work_dir = os.environ.get('AMBIANIC_DIR', os.getcwd())
    if not env_work_dir:
        env_work_dir = DEFAULT_WORK_DIR
    return env_work_dir
