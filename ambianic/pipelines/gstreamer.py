# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from functools import partial
import svgwrite
import gi
import logging
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
from gi.repository import GLib, GObject, Gst, GstBase
from PIL import Image

GObject.threads_init()
Gst.init(None)

log = logging.getLogger(__name__)

class InputStreamProcessor:
    """
        Handles a wide range of media input sources and calls back for TF inference.
        This class is not thread safe. Should not be called from multiple threads simultaneously.

        :argument inf_callback the callback function that applies TF inference (e.g. object detection)
            to a streamed image

    """

    class ImageShape:
        width = height = None
        pass

    class PipelineSource:
        def __init__(self, source_conf=None):
            assert source_conf, "pipeline source configuration required."
            assert source_conf['uri'], "pipeline source definition missing uri element"
            self.uri = source_conf['uri']  # rtsp://..., rtmp://..., http://..., file:///...
            self.type = source_conf.get('type', 'auto')  # video, image, audio, auto
        pass

    def __init__(self, inf_callback=None, source_conf=None):
        # pipeline source info
        self.source = self.PipelineSource(source_conf=source_conf)
        # Reference to Gstreamer main loop structure
        self.mainloop = None
        # Gstreamer pipelines for a given input source (could be image, audio or video)
        self.gst_pipeline = None
        self.gst_video_source = None
        # shape of the input stream image or video
        self.source_shape = self.ImageShape()
        # gst_appsink handlies GStreamer callbacks for TF inference
        self.gst_appsink = None
        # shape of the image passed to Tensorflow for inference
        # default values that are close to most TF image model input tensors
        # gst_overlay is where we draw labels and bounding boxes for users to see inference results
        self.gst_overlay = None
        # inference callback
        self.inference_callback = inf_callback

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
            log.info("Input source width: %d, height: %d", self.source_shape.width, self.source_shape.height)
        return True

    def on_bus_message(self, bus, message, loop):
        t = message.type
        if t == Gst.MessageType.EOS:
            log.info('End of stream. Exiting gstreamer loop for this video stream.')
            loop.quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            log.warning('Warning: %s: %s', err, debug)
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            log.warning('Error: %s: %s', err, debug)
            loop.quit()
        return True

    def on_new_sample(self, sink):
        # print('New image sample received.')
        if not (self.source_shape.width or self.source_shape.height):
            # source stream shape still unknown
            log.warning('New image sample received but source shape still unknown?!')
            return Gst.FlowReturn.OK
        sample = sink.emit('pull-sample')
        buf = sample.get_buffer()
        caps = sample.get_caps()
        struct = caps.get_structure(0)
        # print("gst_appsink caps struct: {}".format(struct))
        app_width = struct["width"]
        app_height = struct["height"]
        # print("gst_appsink(inference image) width: {}, height: {}".format(app_width, app_height))
        result, mapinfo = buf.map(Gst.MapFlags.READ)
        if result:
            img = Image.frombytes('RGB', (app_width, app_height), mapinfo.data, 'raw')
            svg_canvas = svgwrite.Drawing('', size=(self.source_shape.width, self.source_shape.height))
            # run TF model and draw results on SVG canvas
            self.inference_callback(img, svg_canvas)
            self.gst_overlay.set_property('data', svg_canvas.tostring())
        buf.unmap(mapinfo)
        return Gst.FlowReturn.OK

    def run_pipeline(self):
        """ Start the gstreamer pipelines """

        log.info("Starting %s", self.__class__.__name__)

        # Note to self: The pipelines args below work but slow. Work fine with AI inference, but peg the CPU at 200%
        #   turns out certain gstreamer video conversion operations are challenging to move to GPU and are taxing on CPU.
        #   TODO: figure out RPI4 hardware acceleration for h264 to RGB conversion, gst_overlay and scaling.
        #    Default gst ops: videoconvert, videoscale and gst_overlay are slow and use CPU.
        PIPELINE = ' uridecodebin name=source latency=0 '
        PIPELINE += """ ! tee name=t
            t. ! {leaky_q} ! videoconvert ! videoscale ! {sink_caps} ! {sink_element}
            t. ! {leaky_q} ! videoconvert
               ! rsvgoverlay name=gst_overlay fit-to-frame=true ! videoconvert
            """
        # save video stream to files with 1 minute duration
        PIPELINE += " ! omxh264enc ! h264parse ! splitmuxsink muxer=matroskamux location=\"tmp/test1-%02d.mkv\" max-size-time=60000000000"

        LEAKY_Q = 'queue max-size-buffers=1 leaky=downstream'
        # Ask gstreamer to format the images in a way that are close to the TF model tensor
        # Note: Having gstreamer resize doesn't appear to make a big performance difference.
        # Need to look closer at hardware acceleration options where available.
        # ,width={width},pixel-aspect-ratio=1/1'
        SINK_CAPS = 'video/x-raw,format=RGB'
        SINK_ELEMENT = 'appsink name=appsink sync=false emit-signals=true max-buffers=1 drop=true'

        pipeline_args = PIPELINE.format(leaky_q=LEAKY_Q,
                                   sink_caps=SINK_CAPS,
                                   sink_element=SINK_ELEMENT)
        log.info('Gstreamer pipelines: %s', pipeline_args)
        self.gst_pipeline = Gst.parse_launch(pipeline_args)
        self.gst_video_source = self.gst_pipeline.get_by_name('source')
        self.gst_video_source.props.uri = self.source.uri
        self.gst_video_source.connect('autoplug-continue', self.on_autoplug_continue)
        self.gst_overlay = self.gst_pipeline.get_by_name('overlay')
        log.info("overlay sink: %s",str(self.gst_overlay))
        self.gst_appsink = self.gst_pipeline.get_by_name('appsink')
        log.info("appsink: %s", str(self.gst_appsink))
        log.info("appsink will emit signals: %s", self.gst_appsink.props.emit_signals)
        log.info("Connecting AI model and detection overlay to video stream")
        # register to receive new image sample events from gst
        self.gst_appsink.connect('new-sample', self.on_new_sample)
        self.mainloop = GObject.MainLoop()

        if log.getEffectiveLevel() <= logging.DEBUG:
            # set Gst debug log level
            Gst.debug_set_active(True)
            Gst.debug_set_default_threshold(3)

        # Set up a pipelines bus watch to catch errors.
        bus = self.gst_pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_bus_message, self.mainloop)

        # Run pipelines.
        self.gst_pipeline.set_state(Gst.State.PLAYING)
        try:
            log.info("Entering main gstreamer loop")
            self.mainloop.run()
            log.info("Exited gstreamer loop")
        except Exception as e:
            sys.stderr("GST loop exited with error: {} ".format(str(e)))
            pass

        # Clean up.
        log.info("Cleaning up GST resources")
        self.gst_pipeline.set_state(Gst.State.NULL)
        while GLib.MainContext.default().iteration(False):
            pass
        log.info("Stopped %s", self.__class__.__name__)

    def stop_pipeline(self):
        """ Gracefully stop the gstream pipelines """
        log.info("Stopping... %s", self.__class__.__name__)
        Gst.debug_bin_to_dot_file(self.gst_pipeline, Gst.DebugGraphDetails.ALL, 'stream')
        self.gst_pipeline.set_state(Gst.State.NULL)
        self.mainloop.quit()
