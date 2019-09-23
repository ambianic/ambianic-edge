import os
import ambianic

name = "ambianic.main"


def main():
    env_work_dir = os.environ.get('AMBIANIC_DIR', os.getcwd())
    server = ambianic.AmbianicServer(work_dir=env_work_dir)
    server.start()


if __name__ == '__main__':
    main()
