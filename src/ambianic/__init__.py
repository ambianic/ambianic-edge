import os
from dynaconf import Dynaconf
DEFAULT_WORK_DIR = '/workspace'

server_instance = None

config = Dynaconf(
    settings_files=['config.yaml', 'secrets.yaml'],
    environments=False,
)


def get_work_dir():
    """Retrieve the ambianic working directory"""
    env_work_dir = os.environ.get('AMBIANIC_DIR', os.getcwd())
    if not env_work_dir:
        env_work_dir = DEFAULT_WORK_DIR
    return env_work_dir
