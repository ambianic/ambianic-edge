import os
from dynaconf import Dynaconf

DEFAULT_WORK_DIR : str = '/workspace'
DEFAULT_DATA_DIR : str = './data'

DEFAULT_CONFIG_FILE : str = 'config.yaml'
DEFAULT_SECRETS_FILE : str = 'secrets.yaml'

__CONFIG_FILE : str = None

def get_config_file():
    return __CONFIG_FILE

def __init_config() -> Dynaconf:
    return Dynaconf(
        settings_files=[get_config_file()],
        merge=True,
        environments=False,
    )

def load_config(filename : str, clean : bool = False) -> Dynaconf:
    if clean:
        config.clean()
    if filename:
        config.load_file(path=filename)
        global __CONFIG_FILE
        __CONFIG_FILE = filename

    return config

def get_work_dir() -> str:
    """Retrieve the ambianic working directory"""
    env_work_dir = os.environ.get('AMBIANIC_DIR', os.getcwd())
    if not env_work_dir:
        env_work_dir = DEFAULT_WORK_DIR
    return env_work_dir

# initialization
server_instance = None

__CONFIG_FILE = os.path.join(get_work_dir(), DEFAULT_CONFIG_FILE)
config : Dynaconf = __init_config()

