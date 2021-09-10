import os
from argparse import ArgumentParser
from typing import Union

import importlib_metadata as metadata
from dynaconf import Dynaconf, loaders
from dynaconf.utils.boxing import DynaBox


class AmbianicConfig(Dynaconf):

    """Configuration settings loading and persistence."""

    def __init__(self, file_to_save: str, **kwargs):
        super().__init__(**kwargs)
        self.file_to_save: str = file_to_save

    def save(self):
        """Persist configuration settings to disk."""
        # ref: https://dynaconf.readthedocs.io/en/docs_223/guides/advanced_usage.html#exporting
        # ref: https://dynaconf.readthedocs.io/en/docs_223/reference/dynaconf.loaders.html#module-dynaconf.loaders.yaml_loader
        assert self.file_to_save, "file_to_save path must be provided."
        data = self.as_dict()
        loaders.write(self.file_to_save, DynaBox(data).to_dict())


parser = ArgumentParser()
parser.add_argument("-c", "--config", help="Specify config YAML file location")

args, unknown = parser.parse_known_args()

DEFAULT_WORK_DIR: str = "/workspace"
DEFAULT_DATA_DIR: str = "./data"

DEFAULT_CONFIG_FILE: str = args.config or "config.yaml"
DEFAULT_SECRETS_FILE: str = "secrets.yaml"

__CONFIG_FILE: str = None
__SECRETS_FILE: str = None
__version__: str = metadata.version("ambianic-edge")


def get_config_file() -> str:
    return __CONFIG_FILE


def get_secrets_file() -> str:
    if __SECRETS_FILE:
        return __SECRETS_FILE
    return os.path.join(get_work_dir(), DEFAULT_SECRETS_FILE)


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


def __init_config() -> Dynaconf:
    config = AmbianicConfig(
        settings_files=[get_config_file(), get_secrets_file()],
        # secrets=[],
        merge=True,
        environments=False,
        file_to_save=get_config_file(),
    )
    __merge_secrets(config)
    return config


def load_config(filename: str, clean: bool = False) -> Dynaconf:
    if clean:
        config.clean()
    if filename:
        config.load_file(path=[filename, get_secrets_file()])
        __merge_secrets(config)
        global __CONFIG_FILE
        __CONFIG_FILE = filename
    return config


def get_work_dir() -> str:
    """Retrieve the ambianic working directory"""
    env_work_dir = os.environ.get("AMBIANIC_DIR", os.getcwd())
    if not env_work_dir:
        env_work_dir = DEFAULT_WORK_DIR
    return env_work_dir


# initialization
server_instance = None

__CONFIG_FILE = os.path.join(get_work_dir(), DEFAULT_CONFIG_FILE)
config: AmbianicConfig = __init_config()
