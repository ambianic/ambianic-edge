import os
from ambianic import start


def main():
    env_work_dir = os.environ.get('AMBIANIC_DIR', os.getcwd())
    start(env_work_dir)


if __name__ == '__main__':
    main()
