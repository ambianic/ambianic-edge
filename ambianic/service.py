

class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.

    Method for controlled multi-threaded Python app exit suggested by George Notaras:
    https://www.g-loaded.eu/2016/11/24/how-to-terminate-running-python-threads-using-signals/
    """
    pass

