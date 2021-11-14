import logging
import os
from argparse import ArgumentParser

import importlib_metadata as metadata
from dynaconf import Dynaconf, loaders
from dynaconf.utils.boxing import DynaBox

log = logging.getLogger()

parser = ArgumentParser()
parser.add_argument("-c", "--config", help="Specify config YAML file location.")
parser.add_argument(
    "-p",
    "--peerfile",
    help="Specify file location with peerfetch values such as current peerid.",
)

args, unknown = parser.parse_known_args()

# default path locations
DEFAULT_WORK_DIR: str = "/workspace"
DEFAULT_DATA_DIR: str = "./data"

CONFIG_FILE_PATH: str = args.config or "config.yaml"
PEER_FILE_PATH: str = args.peerfile or ".peerjsrc"
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
    """Return path to main config file for this instance.
    This is the file where config changes via API calls are saved."""
    return __config_file


def get_peerid_file():
    """Return path to the file where peerfetch Peer ID for this device is stored."""
    return __peer_file


def get_local_config_file() -> str:
    """Return path to local custom config file. E.g. config.local.yaml.
    This is the file where manual local changes are saved and override values from other config files."""
    (cfg_file_head, cfg_file_ext) = os.path.splitext(get_config_file())
    local_file_path = cfg_file_head + ".local." + cfg_file_ext
    return local_file_path


def get_secrets_file() -> str:
    if __secrets_file:
        return __secrets_file
    return os.path.join(get_work_dir(), SECRETS_FILE_PATH)


def init_config() -> Dynaconf:
    log.info("Configuration: begin init_config()")
    global __config
    __config = Dynaconf(
        settings_files=[
            get_config_defaults_file(),
            get_secrets_file(),
            get_peerid_file(),
            get_config_file(),
        ],
        merge=True,
        environments=False,
    )
    log.debug("Configuration: merging secrets into config string templates")
    return __config


def reload_config() -> Dynaconf:
    """Reloads settings with latest config file updates."""
    __config.reload()
    log.info("Configuration: reloaded.")


def load_config(filename: str, clean: bool = False) -> Dynaconf:
    """Loads configuration settings from the given filename."""
    root_config = get_root_config()
    if clean:
        root_config.clean()
    if filename:
        root_config.load_file(path=[filename, get_secrets_file()])
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
__peer_file = os.path.join(get_work_dir(), PEER_FILE_PATH)
