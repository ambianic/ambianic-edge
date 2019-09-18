import os
import ambianic

name = "ambianic"


def main():
    env_work_dir = os.environ.get('AMBIANIC_DIR', os.getcwd())
    ambianic.start(env_work_dir)


if __name__ == '__main__':
    main()
