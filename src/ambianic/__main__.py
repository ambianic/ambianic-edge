"""Main Ambianic OS executable."""
import os
import ambianic
import ambianic.server
import signal

_svr = None


def main():
    """Start the main app executable in the hosting OS environment."""
    global _svr
    env_work_dir = os.environ.get('AMBIANIC_DIR', os.getcwd())
    _svr = ambianic.server.AmbianicServer(work_dir=env_work_dir)
    _svr.start()


def stop():
    """Stop a running app executable in the hosting OS environment."""
    global _svr
    _svr.stop()


def _service_shutdown(signum=None, frame=None):
    """Wrap system exit signal into an application exception.

    The ServiceExit exception will be caught in main process threads
    and handled gracefully.
    """
    print('Caught system shutdown signal (Ctrl+C or similar). '
          'Signal code: %d', signum)
    raise ambianic.util.ServiceExit


def _register_sys_handlers():  # pragma: no cover
    """Register system exit handler for graceful shutdown."""
    signal.signal(signal.SIGTERM, _service_shutdown)
    signal.signal(signal.SIGINT, _service_shutdown)


if __name__ == '__main__':  # pragma: no cover
    _register_sys_handlers()
    main()
