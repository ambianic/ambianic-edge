import os
from argparse import ArgumentParser
from typing import Union

import importlib_metadata as metadata
from dynaconf import Dynaconf, loaders
from dynaconf.utils.boxing import DynaBox

parser = ArgumentParser()
parser.add_argument("-c", "--config", help="Specify config YAML file location")

args, unknown = parser.parse_known_args()

# default path locations
DEFAULT_WORK_DIR: str = "/workspace"
DEFAULT_DATA_DIR: str = "./data"

CONFIG_FILE_PATH: str = args.config or "config.yaml"
SECRETS_FILE_PATH: str = "secrets.yaml"

CONFIG_DEFAULTS_FILE_PATH: str = "config.defaults.yaml"

# actual local file locations
__config_file: str = None
__secrets_file: str = None

# package version
__version__: str = metadata.version("ambianic-edge")

# refernce to system global config instance
__config: Dynaconf = "Not Initialized Yet!"


def get_root_config() -> Dynaconf:
    return __config


def get_config_defaults_file() -> str:
    return CONFIG_DEFAULTS_FILE_PATH


def get_config_file() -> str:
    return __config_file


def get_secrets_file() -> str:
    if __secrets_file:
        return __secrets_file
    return os.path.join(get_work_dir(), SECRETS_FILE_PATH)


def __merge_secrets(config: Union[Dynaconf, DynaBox], src_config: Dynaconf = None):
    if src_config is None:
        src_config = config
    for key, val in config.items():
        if isinstance(val, dict):
            __merge_secrets(val, src_config)
            continue
        # NOTE value must be an exact match to avoid interfering
        # with other templates
        if isinstance(val, str) and (val[0:2] == "${" and val[-1] == "}"):
            ref_key = val[2:-1]
            ref_val = src_config.get(ref_key, None)
            if ref_val is not None:
                config[key] = ref_val
            continue


def init_config() -> Dynaconf:
    global __config
    __config = Dynaconf(
        settings_files=[
            get_config_defaults_file(),
            get_config_file(),
            get_secrets_file(),
        ],
        # secrets=[],
        merge=True,
        environments=False,
    )
    __merge_secrets(__config)
    return __config


def load_config(filename: str, clean: bool = False) -> Dynaconf:
    """Loads configuration settings from the given filename.
    If file_to_save is provided then consequent calls to save() will persist settings to the given file path.
    Otherwise save() will persist to the filename path (where the settings are to be loaded from)."""
    root_config = get_root_config()
    if clean:
        root_config.clean()
    if filename:
        root_config.load_file(
            path=[get_config_defaults_file(), filename, get_secrets_file()]
        )
        __merge_secrets(root_config)
        global __config_file
        __config_file = filename
    return root_config


def save_config():
    """Persist configuration settings to disk."""
    # ref: https://dynaconf.readthedocs.io/en/docs_223/guides/advanced_usage.html#exporting
    # ref: https://dynaconf.readthedocs.io/en/docs_223/reference/dynaconf.loaders.html#module-dynaconf.loaders.yaml_loader
    file_to_save = get_config_file()
    root_config = get_root_config()
    data = root_config.as_dict()
    loaders.write(file_to_save, DynaBox(data).to_dict())


def get_work_dir() -> str:
    """Retrieve the ambianic working directory"""
    env_work_dir = os.environ.get("AMBIANIC_DIR", os.getcwd())
    if not env_work_dir:
        env_work_dir = DEFAULT_WORK_DIR
    return env_work_dir


__config_file = os.path.join(get_work_dir(), CONFIG_FILE_PATH)
