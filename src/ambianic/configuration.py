import logging
import os
from argparse import ArgumentParser

import importlib_metadata as metadata
from dynaconf import Dynaconf, loaders

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
    This is typically the file with baseline configuration settings
    across a fleet of similar devices.
    """
    return __config_file


def get_local_config_file() -> str:
    """Return path to local custom config file. E.g. config.local.yaml.
    This is the file where config changes via API calls are saved.
    This is also the file where manual local changes can be applied and saved to override values from other config files."""
    (cfg_file_head, cfg_file_ext) = os.path.splitext(get_config_file())
    local_file_path = cfg_file_head + ".local" + cfg_file_ext
    return local_file_path


def get_peerid_file():
    """Return path to the file where peerfetch Peer ID for this device is stored."""
    return __peer_file


def get_secrets_file() -> str:
    if __secrets_file:
        return __secrets_file
    return os.path.join(get_work_dir(), SECRETS_FILE_PATH)


def get_all_config_files():
    conf_files = os.environ.get("AMBIANIC_CONFIG_FILES")
    if conf_files:
        file_list = conf_files.split(",")
        file_list = list(map(lambda s: s.strip(), file_list))
        return file_list


def init_config() -> Dynaconf:
    log.debug("Configuration: begin init_config()")
    global __config
    conf_files = os.environ.get("AMBIANIC_CONFIG_FILES", None)
    if conf_files is None:
        conf_files = ",".join(
            [
                get_config_defaults_file(),
                get_secrets_file(),
                get_peerid_file(),
                get_config_file(),
            ]
        )
    os.environ["AMBIANIC_CONFIG_FILES"] = conf_files
    os.environ["SETTINGS_FILE_FOR_DYNACONF"] = conf_files
    log.info(f"Loading config settings from: {conf_files}")
    __config = Dynaconf(
        # settings_files=conf_files.split(','), # passed via SETTINGS_FILE_FOR_DYNACONF instead
        environments=False,
    )
    return __config


def reload_config() -> Dynaconf:
    """Reloads settings with latest config file updates."""
    conf_files = get_all_config_files()
    log.info(f"Reloading config settings from: {conf_files}")
    __config.reload()
    log.info("Configuration: reloaded.")


def load_config(filename: str, clean: bool = False) -> Dynaconf:
    """Loads configuration settings from the given filename."""
    root_config = get_root_config()
    if clean:
        root_config.clean()
    if filename:
        files = [get_secrets_file(), filename]
        log.debug(f"Loading config from files: {files}")
        root_config.load_file(path=get_secrets_file())
        root_config.load_file(path=filename)
        global __config_file
        __config_file = filename
    return root_config


def save_config():
    """Persist configuration settings to local config file."""
    # ref: https://dynaconf.readthedocs.io/en/docs_223/guides/advanced_usage.html#exporting
    # ref: https://dynaconf.readthedocs.io/en/docs_223/reference/dynaconf.loaders.html#module-dynaconf.loaders.yaml_loader
    file_to_save = os.environ.get("AMBIANIC_SAVE_CONFIG_TO", None)
    if not file_to_save:
        file_to_save = get_local_config_file()
    root_config = get_root_config()
    data = root_config.as_dict()
    log.info(f"Saving config settings to: {file_to_save}")
    loaders.write(file_to_save, data)


def get_work_dir() -> str:
    """Retrieve the ambianic working directory"""
    env_work_dir = os.environ.get("AMBIANIC_DIR", os.getcwd())
    if not env_work_dir:
        env_work_dir = DEFAULT_WORK_DIR
    return env_work_dir


__config_file = os.path.join(get_work_dir(), CONFIG_FILE_PATH)
__peer_file = os.path.join(get_work_dir(), PEER_FILE_PATH)


# initial config init
init_config()
