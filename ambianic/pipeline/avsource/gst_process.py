
import traceback
import logging
import signal
import threading
from ambianic.service import ServiceExit
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
from gi.repository import GObject, Gst, GLib

Gst.init(None)
# No need to call GObject.threads_init() since version 3.11
# GObject.threads_init()

log = logging.getLogger(__name__)


class GstService:
    """Streams audio/video samples from various network and local A/V sources.

    Runs in a separate OS process. Reads from vadious sources and
     formatts. Serves audio/video samples in a normalized format to its master
     AVElement, which then passes on to the next element in the Ambianic
     pipeline.

    Parameters
    ----------
    source_conf : URI
        Source configuration. At this time URI schemes are supported such as
        rtsp://host:ip/path_to_stream.

    out_queue : multiprocessing.Queue
        The queue where this service adds samples in a normalized format
        for its master AVElement to receive and pass on to the next Ambianic
        pipeline element.

    """

    class ImageShape:
        width = height = None
        pass

    class PipelineSource:
        def __init__(self, source_conf=None):
            assert source_conf, "pipeline source configuration required."
            assert source_conf['uri'], \
                "pipeline source config missing uri element"
            # rtsp://..., rtmp://..., http://..., file:///...
            self.uri = source_conf['uri']
            # video, image, audio, auto
            self.type = source_conf.get('type', 'auto')
        pass

    def __init__(self, source_conf=None, out_queue=None, stop_signal=None):
        assert source_conf
        assert out_queue
        assert stop_signal
        # pipeline source info
        log.debug('Initializing GstService with source: %s ', source_conf)
        self._out_queue = out_queue
        self._stop_signal = stop_signal
        self.source = self.PipelineSource(source_conf=source_conf)
        # Reference to Gstreamer main loop structure
        self.mainloop = None
        # Gstreamer pipeline for a given input source
        # (could be image, audio or video)
        self.gst_pipeline = None
        self.gst_video_source = None
        self._gst_video_source_connect_id = None
        # shape of the input stream image or video
        self.source_shape = self.ImageShape()
        self.gst_queue0 = None
        self.gst_vconvert = None
        self.gst_vconvert_connect_id = None
        self.gst_queue1 = None
        # gst_appsink handlies GStreamer callbacks
        # for new media samples which it passes on to the next pipe element
        self.gst_appsink = None
        self._gst_appsink_connect_id = None
        # indicates whether stop was requested via the API
        self._stop_requested = False
        self.gst_bus = None

    def on_autoplug_continue(self, src_bin, src_pad, src_caps):
        # print('on_autoplug_continue called for uridecodebin')
        # print('src_bin: {}'.format(str(src_bin)))
        # print('src_pad: {}'.format(str(src_pad)))
        # print('src_caps: {}'.format(str(src_caps)))
        struct = src_caps.get_structure(0)
        # print("src caps struct: {}".format(struct))
        self.source_shape.width = struct["width"]
        self.source_shape.height = struct["height"]
        if self.source_shape.width:
            log.info("Input source width: %d, height: %d",
                     self.source_shape.width, self.source_shape.height)
        return True

    def on_bus_message(self, bus, message, loop):
        t = message.type
        if t == Gst.MessageType.EOS:
            log.info('End of stream. Exiting gstreamer loop '
                     'for this video stream.')
            self._gst_cleanup()
            # loop.quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            log.warning('Warning: %s: %s', err, debug)
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            log.warning('Error: %s: %s', err, debug)
            self._gst_cleanup()
            # loop.quit()
        return True

    def on_new_sample(self, sink):
        log.info('Input stream received new image sample.')
        if self._out_queue.full():
            log.info('Out queue full, skipping sample.')
            return Gst.FlowReturn.OK
        if not (self.source_shape.width or self.source_shape.height):
            # source stream shape still unknown
            log.warning('New image sample received '
                        'but source shape still unknown?!')
            return Gst.FlowReturn.OK
        sample = sink.emit('pull-sample')
        buf = sample.get_buffer()
        caps = sample.get_caps()
        struct = caps.get_structure(0)
        # print("gst_appsink caps struct: {}".format(struct))
        app_width = struct["width"]
        app_height = struct["height"]
        # print("gst_appsink(inference image) width: {}, height: {}".
        #   format(app_width, app_height))
        result, mapinfo = buf.map(Gst.MapFlags.READ)
        if result:
            sample = {
                'type': 'image',
                'format': 'RGB',
                'width': app_width,
                'height': app_height,
                'bytes': mapinfo.data,
            }
            log.info('GstService adding sample to out_queue.')
            self._out_queue.put(sample)
        buf.unmap(mapinfo)
        return Gst.FlowReturn.OK

    def _get_pipeline_args(self):
        log.debug('Preparing Gstreamer pipeline args')
        PIPELINE = ' uridecodebin name=source latency=0 '
        PIPELINE += """
             ! {leaky_q0} ! videoconvert name=vconvert ! {sink_caps}
             ! {leaky_q1} ! {sink_element}
             """
        LEAKY_Q_ = 'queue max-size-buffers=10 leaky=downstream'
        LEAKY_Q0 = LEAKY_Q_ + ' name=queue0'
        LEAKY_Q1 = LEAKY_Q_ + ' name=queue1'
        # Ask gstreamer to format the images in a way that are close
        # to the TF model tensor.
        # Note: Having gstreamer resize doesn't appear to make
        # a big performance difference.
        # Need to look closer at hardware acceleration options where available.
        # ,width={width},pixel-aspect-ratio=1/1'
        SINK_CAPS = 'video/x-raw,format=RGB'
        SINK_ELEMENT = """
                appsink name=appsink sync=false
                emit-signals=true max-buffers=1 drop=true
                """
        pipeline_args = PIPELINE.format(leaky_q0=LEAKY_Q0,
                                        leaky_q1=LEAKY_Q1,
                                        sink_caps=SINK_CAPS,
                                        sink_element=SINK_ELEMENT)
        log.debug('Gstreamer pipeline args: %s', pipeline_args)
        return pipeline_args

    def _build_gst_pipeline(self):
        log.debug("Building new gstreamer pipeline")
        pipeline_args = self._get_pipeline_args()
        log.debug("Initializing gstreamer pipeline")
        self.gst_pipeline = Gst.parse_launch(pipeline_args)
        self.gst_video_source = self.gst_pipeline.get_by_name('source')
        self.gst_video_source.props.uri = self.source.uri
        self.gst_video_source_connect_id = self.gst_video_source.connect(
            'autoplug-continue', self.on_autoplug_continue)
        assert self.gst_video_source_connect_id
        self.gst_queue0 = self.gst_pipeline.get_by_name('queue0')
        self.gst_vconvert = self.gst_pipeline.get_by_name('vconvert')
        self.gst_queue1 = self.gst_pipeline.get_by_name('queue1')
        self.gst_appsink = self.gst_pipeline.get_by_name('appsink')
        log.debug("appsink: %s", str(self.gst_appsink))
        log.debug("appsink will emit signals: %s",
                  self.gst_appsink.props.emit_signals)
        # register to receive new image sample events from gst
        self._gst_appsink_connect_id = self.gst_appsink.connect(
            'new-sample', self.on_new_sample)
        self.mainloop = GObject.MainLoop()

        if log.getEffectiveLevel() <= logging.DEBUG:
            # set Gst debug log level
            Gst.debug_set_active(True)
            Gst.debug_set_default_threshold(3)

        # Set up a pipeline bus watch to catch errors.
        self.gst_bus = self.gst_pipeline.get_bus()
        self.gst_bus.add_signal_watch()
        self.gst_bus.connect('message', self.on_bus_message, self.mainloop)

    def _gst_loop(self):
        # build new gst pipeline
        self._build_gst_pipeline()
        # Run pipeline.
        self.gst_pipeline.set_state(Gst.State.PLAYING)
        log.debug("Entering main gstreamer loop")
        self.mainloop.run()
        log.debug("Exited main gstreamer loop")

    def _gst_cleanup(self):
        log.debug("GST cleaning up resources...")
        try:
            if self.mainloop and \
              self.mainloop.is_running() and \
              self.gst_pipeline and \
              self.gst_pipeline.get_state(timeout=1)[1] != Gst.State.NULL:
                # stop pipeline elements in reverse order (from last to first)
                log.debug("gst_bus.remove_signal_watch()")
                self.gst_bus.remove_signal_watch()
                self.gst_bus = None
                log.debug("gst_appsink.set_state(Gst.State.NULL)")
                self.gst_appsink.set_state(Gst.State.NULL)
                # self.gst_appsink.disconnect(self._gst_appsink_connect_id)
                self.gst_appsink = None
                log.debug("gst_queue0.set_state(Gst.State.NULL)")
                self.gst_queue1.set_state(Gst.State.NULL)
                # self.gst_queue.disconnect()
                self.gst_queue1 = None
                log.debug("gst_vconvert.set_state(Gst.State.NULL)")
                self.gst_vconvert.set_state(Gst.State.NULL)
                # self.gst_vconvert.disconnect(self.gst_vconvert_connect_id)
                self.gst_vconvert = None
                log.debug("gst_queue1.set_state(Gst.State.NULL)")
                self.gst_queue0.set_state(Gst.State.NULL)
                # self.gst_queue.disconnect()
                self.gst_queue0 = None
                log.debug("gst_video_source.set_state(Gst.State.NULL)")
                self.gst_video_source.set_state(Gst.State.NULL)
                # self.gst_video_source.disconnect(self._gst_video_source_connect_id)
                self.gst_video_source = None
                log.debug("gst_pipeline.set_state(Gst.State.NULL)")
                self.gst_pipeline.set_state(Gst.State.NULL)
                self.gst_pipeline = None
                log.debug("while GLib.MainContext.default().iteration(False)")
                while GLib.MainContext.default().iteration(False):
                    pass
            else:
                log.debug("self.gst_pipeline: None")
            if self.mainloop:
                log.debug("gst mainloop.quit()")
                self.mainloop.quit()
                self.mainloop = None
            else:
                log.debug("mainloop: None")
        except Exception as e:
            log.warning('Error while cleaning up gstreamer resources: %s',
                        str(e))
            formatted_lines = traceback.format_exc().splitlines()
            log.warning('Exception stack trace: %s', formatted_lines)
        log.debug("GST clean up exiting.")

    def service_shutdown(self, signum, frame):
        log.info('Caught system shutdown signal %d', signum)
        raise ServiceExit

    def _stop_handler(self):
        self._stop_handler.wait()
        self._gst_cleanup()

    def _register_stop_handler(self):
        stop_watch_thread = threading.Thread(
            name='GST stop watch thread',
            daemon=True,
            target=self._stop_handler)
        stop_watch_thread.start()

    def run(self):
        """ Run the gstreamer pipeline service """
        log.info("Starting %s", self.__class__.__name__)
        # Register the signal handlers
        signal.signal(signal.SIGTERM, self.service_shutdown)
        signal.signal(signal.SIGINT, self.service_shutdown)
        self._register_stop_handler()
        try:
            self._gst_loop()
        except ServiceExit as e:
            log.info('GST Service exit requested. Exiting...')
        except Exception as e:
            log.warning('GST loop exited with error: %s. ',
                        str(e))
            formatted_lines = traceback.format_exc().splitlines()
            log.warning('Exception stack trace: %s', formatted_lines)
        finally:
            log.debug('Gst service cleaning up before exit...')
            self._gst_cleanup()
            self._out_queue.close()
            log.debug("Gst service cleaned up and ready to exit.")
        log.info("Stopped %s", self.__class__.__name__)


def start_gst_service(source_conf=None, out_queue=None, stop_signal=None):
    svc = GstService(source_conf=source_conf,
                     out_queue=out_queue,
                     stop_signal=stop_signal)
    svc.run()
