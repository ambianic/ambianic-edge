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

    class Shape:
        width = height = None
        pass

    def __init__(self, inf_callback = None):
        # Gstreamer pipeline for a given input source (could be image, audio or video)
        self.pipeline = None
        self.video_source = None
        # shape of the input stream image or video
        self.source_shape = self.Shape()
        # appsink handlies GStreamer callbacks for TF inference
        self.appsink = None
        # shape of the image passed to Tensorflow for inference
        # default values that are close to most TF image model input tensors
        self.appsink_shape = self.Shape()
        self.appsink_shape.width = 320
        self.appsink_shape.height = 320
        # overlay is where we draw labels and bounding boxes for users to see inference results
        self.overlay = None
        # inference callback
        self.inference_callback = inf_callback

    def on_autoplug_continue(self, src_bin, src_pad, src_caps):
        #print('on_autoplug_continue called for uridecodebin')
        #print('src_bin: {}'.format(str(src_bin)))
        #print('src_pad: {}'.format(str(src_pad)))
        #print('src_caps: {}'.format(str(src_caps)))
        struct = src_caps.get_structure(0)
        #print("src caps struct: {}".format(struct))
        self.source_shape.width = struct["width"]
        self.source_shape.height = struct["height"]
        if self.source_shape.width:
            print("Input source width: {}, height: {}".format(self.source_shape.width, self.source_shape.height))
        return True

    def on_bus_message(self, bus, message, loop):
        t = message.type
        if t == Gst.MessageType.EOS:
            print('End of stream. Exiting gstreamer loop for this video stream.')
            loop.quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            sys.stderr.write('Warning: %s: %s\n' % (err, debug))
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            sys.stderr.write('Error: %s: %s\n' % (err, debug))
            loop.quit()
        return True

    def on_new_sample(self, sink):
        # print('New image sample received.')
        sample = sink.emit('pull-sample')
        buf = sample.get_buffer()
        caps = sample.get_caps()
        struct = caps.get_structure(0)
        # print("appsink caps struct: {}".format(struct))
        app_width = struct["width"]
        app_height = struct["height"]
        # print("appsink(inference image) width: {}, height: {}".format(app_width, app_height))
        result, mapinfo = buf.map(Gst.MapFlags.READ)
        if result:
            img = Image.frombytes('RGB', (app_width, app_height), mapinfo.data, 'raw')
            svg_canvas = svgwrite.Drawing('', size=(self.source_shape.width, self.source_shape.height))
            # run TF model and draw results on SVG canvas
            self.inference_callback(img, svg_canvas)
            self.overlay.set_property('data', svg_canvas.tostring())
        buf.unmap(mapinfo)
        return Gst.FlowReturn.OK

    def run_pipeline(self):
        """ Start the gstreamer pipeline """

        # Note to self: The pipeline args below work but slow. Work fine with AI inference, but peg the CPU at 200%
        #   turns out certain gstreamer video conversion operations are challenging to move to GPU and are taxing on CPU.
        #   TODO: figure out RPI4 hardware acceleration for h264 to RGB conversion, overlay and scaling.
        #    Default gst ops: videoconvert, videoscale and overlay are slow and use CPU.
        PIPELINE = ' uridecodebin name=source latency=0 '
        PIPELINE += """ ! tee name=t
            t. ! {leaky_q} ! videoconvert ! videoscale ! {sink_caps} ! {sink_element}
            t. ! {leaky_q} ! videoconvert
               ! rsvgoverlay name=overlay fit-to-frame=true ! videoconvert
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

        sink_caps = SINK_CAPS.format(width=self.appsink_shape.width, height=self.appsink_shape.height)
        pipeline_args = PIPELINE.format(leaky_q=LEAKY_Q,
                                   sink_caps=sink_caps,
                                   sink_element=SINK_ELEMENT)
        log.info('Gstreamer pipeline: %s', pipeline_args)
        self.pipeline = Gst.parse_launch(pipeline_args)
        self.video_source = self.pipeline.get_by_name('source')
        self.video_source.props.uri = "rtsp://admin:121174l2ll74@192.168.86.131:554/ISAPI/Streaming/channels/101/picture"
        self.video_source.connect('autoplug-continue', self.on_autoplug_continue)
        self.overlay = self.pipeline.get_by_name('overlay')
        print("overlay sink: {}".format(str(self.overlay)))
        self.appsink = self.pipeline.get_by_name('appsink')
        print("appsink: {}".format(str(self.appsink)))
        print("appsink will emit signals: {}".format(self.appsink.props.emit_signals))
        print("Connecting AI model and detection overlay to video stream")
        self.appsink.connect('new-sample', self.on_new_sample)
        self.inference_callback = self.inference_callback
        loop = GObject.MainLoop()

        # set Gst debug log level
    #    Gst.debug_set_active(True)
    #    Gst.debug_set_default_threshold(3)

        # Set up a pipeline bus watch to catch errors.
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_bus_message, loop)

        # Run pipeline.
        self.pipeline.set_state(Gst.State.PLAYING)
        try:
            print("Entering main gstreamer loop")
            loop.run()
            print("Exited gstreamer loop")
        except Exception as e:
            sys.stderr("GST loop exited with error: {} ".format(str(e)))
            pass

        # Clean up.
        print("Cleaning up GST resources")
        self.pipeline.set_state(Gst.State.NULL)
        while GLib.MainContext.default().iteration(False):
            pass
        print("Done.")

    def stop_pipeline(self):
        """ Gracefully stop the gstream pipeline """
        loop = GLib.MainLoop.quit()
        print('Exiting...')
        Gst.debug_bin_to_dot_file(self.pipeline, Gst.DebugGraphDetails.ALL, 'stream')
        self.pipeline.set_state(Gst.State.NULL)
        loop.quit()
