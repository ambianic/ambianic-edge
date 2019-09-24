import os
import ambianic

global _svr
_svr = None


def main():
    global _svr
    env_work_dir = os.environ.get('AMBIANIC_DIR', os.getcwd())
    _svr = ambianic.server.AmbianicServer(work_dir=env_work_dir)
    _svr.start()


def stop():
    global _svr
    _svr.stop()


if __name__ == '__main__':  # pragma: no cover
    main()
