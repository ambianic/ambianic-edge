from .. import PipeElement
from . import gst_process

import logging
import time
import threading
import traceback
import multiprocessing
import queue
from PIL import Image


log = logging.getLogger(__name__)


MIN_HEALING_INTERVAL = 5


class AVSourceElement(PipeElement):
    """
    Pipe element that handles a wide range of media input sources.

    Detects media input source, processes and passes on normalized raw
    samples to the next pipe element.
    """

    def __init__(self, **source_conf):
        """Create an av source element with given configuration.

        :Parameters:
        ----------
        source_conf : dict
            uri: string (example rtsp://somehost/ipcam/channel0)
            type: string (video, audio or image)
        """
        super().__init__()
        assert source_conf
        # pipeline source info
        self._source_conf = source_conf
        self._gst_process = None
        self._gst_out_queue = None
        self._gst_process_stop_signal = None
        # protects access to gstreamer resources in rare cases
        # such as supervised healing requests
        self._healing_in_progress = threading.RLock()
        # ensure healing requests are reasonably spaced out
        self._latest_healing = time.monotonic()

    def _on_new_sample(self, sample=None):
        log.info('Input stream received new gst sample.')
        assert sample
        type = sample['type']
        # only image type supported at this time
        assert type == 'image'
        # make sure the sample is in RGB format
        format = sample['format']
        assert format == 'RGB'
        width = sample['width']
        height = sample['height']
        bytes = sample['bytes']
        img = Image.frombytes(format, (width, height),
                              bytes, 'raw')
        # pass image sample to next pipe element, e.g. ai inference
        log.info('Input stream sending sample to next element.')
        self.receive_next_sample(image=img)

    def _run_gst_service(self):
        log.debug("Starting Gst service process...")
        self._gst_out_queue = multiprocessing.Queue(10)
        self._gst_process_stop_signal = multiprocessing.Event()
        self._gst_process = multiprocessing.Process(
            target=gst_process.start_gst_service,
            name='Gstreamer Service Process',
            daemon=True,
            kwargs={'source_conf': self._source_conf,
                    'out_queue': self._gst_out_queue,
                    'stop_signal': self._gst_process_stop_signal,
                    }
            )
        self._gst_process.daemon = True
        self._gst_process.start()
        gst_proc = self._gst_process
        while not self._stop_requested and gst_proc.is_alive():
            # do not use process.join() to avoid deadlock due to shared queue
            try:
                next_sample = self._gst_out_queue.get(timeout=1)
                self._on_new_sample(sample=next_sample)
            except queue.Empty:
                log.debug('no new sample available yet in gst out queue')
            except Exception as e:
                log.warning('AVElement loop caught an error: %s. ',
                            str(e))
                formatted_lines = traceback.format_exc().splitlines()
                log.warning('Exception stack trace: %s',
                            "\n".join(formatted_lines))

    def _clear_gst_out_queue(self):
        log.debug("Clearing _gst_out_queue.")
        try:
            while not self._gst_out_queue.empty():
                self._gst_out_queue.get_nowait()
        except queue.Empty:
            pass
        log.debug("Cleared _gst_out_queue.")

    def _stop_gst_service(self):
        log.debug("Stopping Gst service process.")
        gst_proc = self._gst_process
        stop_signal = self._gst_process_stop_signal
        if gst_proc and gst_proc.is_alive():
            # tell the OS we won't use this queue any more
            log.debug('GST process still alive. Shutting it down.')
            # log.debug('Closing out queue shared with GST proces.')
            # self._gst_out_queue.close()
            # send a polite request to the process to stop
            log.debug('Sending stop signal to GST process.')
            stop_signal.set()
            log.debug('Signalled gst process to stop')
            # make sure a non-empty queue doesn't block
            # the gst process from stopping
            self._clear_gst_out_queue()
            # give it a few seconds to stop cleanly
            for i in range(10):
                time.sleep(1)
                if not gst_proc.is_alive():
                    break
            # process did not stop, we need to be a bit more assertive
            if gst_proc.is_alive():
                log.debug('Gst proess did not stop. Terminating.')
                gst_proc.terminate()
                # do not call join() because it may cause a deadlock
                # due to the shared queue
                # give it a few seconds to terminate cleanly
                for i in range(10):
                    time.sleep(1)
                    if not gst_proc.is_alive():
                        break
                # last resort, force kill the process
                if gst_proc.is_alive():
                    log.debug('Gst proess did not terminate.'
                              ' Resorting to force kill.')
                    gst_proc.kill()
                    # while gst_proc.is_alive():
                    #     time.sleep(1)
                    log.debug('Gst process killed.')
                else:
                    log.debug('Gst process stopped after terminate signal.')
            else:
                log.debug('Gst process stopped after stop signal.')

    def start(self):
        """Start processing input from the configured audio or video source."""
        super().start()
        log.info("Starting %s", self.__class__.__name__)
        self._stop_requested = False
        while not self._stop_requested:
            self._run_gst_service()
        self._stop_gst_service()
        log.info("Stopped %s", self.__class__.__name__)

    def heal(self):
        """Attempt to heal a damaged AV source processing service."""
        log.debug("Entering healing method... %s", self.__class__.__name__)
        log.debug('Healing waiting for lock.')
        self._healing_in_progress.acquire()
        try:
            logging.debug('Healing lock acquired.')
            now = time.monotonic()
            # Space out healing attempts.
            # No point in back to back healing runs when there are
            # blocking dependencies on external resources.
            log.warning('latest healing ts: %r, now-MIN_HEALING_INTERVAL: %r',
                        self._latest_healing,
                        now - MIN_HEALING_INTERVAL)
            if self._latest_healing < now - MIN_HEALING_INTERVAL:
                # cause gst loop to exit and repair
                self._latest_healing = now
                self._stop_gst_service()
                # lets give external resources a chance to recover
                # for example wifi connection is down temporarily
                time.sleep(1)
                log.debug("AVElement healing completed.")
            else:
                log.debug("Healing request ignored. "
                          "Too soon after previous healing request.")
        finally:
            logging.debug('Healing lock released.')
            self._healing_in_progress.release()
        log.debug("Exiting healing method. %s", self.__class__.__name__)

    def stop(self):
        """Stop the AV source processing loop."""
        log.info("Entering stop method ... %s", self.__class__.__name__)
        self._stop_requested = True
        super().stop()
        log.info("Exiting stop method. %s", self.__class__.__name__)
