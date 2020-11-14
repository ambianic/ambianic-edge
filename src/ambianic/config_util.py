from dynaconf import Dynaconf

def get_default_config():
    return get_config('config.yaml')

def get_config(filename: str):
    return Dynaconf(
        settings_files=[
            filename
        ],
        merge=True,
        environments=False,
    )
