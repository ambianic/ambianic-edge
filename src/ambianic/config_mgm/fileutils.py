
from .config_diff import Config
import yaml


def save(filename: str, config: Config):
    """Save configuraion to file"""
    with open(filename, 'w') as fh:
        yaml.dump(config, fh, default_flow_style=False)
