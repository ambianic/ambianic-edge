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
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
from gi.repository import GLib, GObject, Gst, GstBase
from PIL import Image

GObject.threads_init()
Gst.init(None)

def on_bus_message(bus, message, loop):
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

def on_new_sample(sink, overlay, appsink_size, user_function):
    print('New image sample received.')
    sample = sink.emit('pull-sample')
    buf = sample.get_buffer()
    caps = sample.get_caps()
    struct = caps.get_structure(0)
    # print("caps struct: {}".format(struct))
    video_source_width = struct["width"]
    video_source_height = struct["height"]
    print("Input video source width: {}, height: {}".format(video_source_width, video_source_height))
    result, mapinfo = buf.map(Gst.MapFlags.READ)
    if result:
      img = Image.frombytes('RGB', (appsink_size[0], appsink_size[1]), mapinfo.data, 'raw')
      svg_canvas = svgwrite.Drawing('', size=(appsink_size[0], appsink_size[1]))
      user_function(img, svg_canvas)
      overlay.set_property('data', svg_canvas.tostring())
    buf.unmap(mapinfo)
    return Gst.FlowReturn.OK

def run_pipeline(user_function,
                 appsink_size=(320, 180)):

# WORKS GREAT with streaming. No AI inference. Even smaller file sizes. 3.4MB per 1MB video. CPU at 10%! Uses GPU!
#    PIPELINE = ' uridecodebin name=source latency=0 ! queue ! videoconvert ! omxh264enc ! h264parse '
#    PIPELINE += " ! splitmuxsink muxer=matroskamux location=\"tmp/test1-%02d.mkv\" max-size-time=60000000000"

# WORKS SLOW. Works fine with AI inference, but pegs the CPU at 200%
#   turns out certain gstreamer video conversion operations are challenging to move to GPU and are taxing on CPU.
#   TODO: figure out RPI hardware acceleration for h264 to RGB conversion, overlay and scaling.
#    Default gst ops: videoconvert, videoscale and overlay are slow, using CPU.
    PIPELINE = ' uridecodebin name=source latency=0 '
    PIPELINE += """ ! tee name=t
        t. ! {leaky_q} ! videoconvert ! videoscale ! {sink_caps} ! {sink_element}
        t. ! {leaky_q} ! videoconvert
           ! rsvgoverlay name=overlay fit-to-frame=true ! videoconvert
        """
    # save video stream to files with 10 minutes duration
    PIPELINE += " ! omxh264enc ! h264parse ! splitmuxsink muxer=matroskamux location=\"tmp/test1-%02d.mkv\" max-size-time=600000000000"

# Experimental version: doesn't work yet
#    PIPELINE = ' uridecodebin name=source latency=100 ' + \
#        ' source. ! application/x-rtp, media=(string)audio ! decodebin ! audioconvert ! fakesink silent=false ' +\
#        ' source. ! application/x-rtp, media=(string)video ! decodebin !   ' +\
#        ' ! rtph264depay ! h264parse ! v4l2h264dec capture-io-mode=4 ! v4l2convert output-io-mode=5 capture-io-mode=4 ! video/x-raw, format=RGB' + \
#        ' ! {leaky_q} ! {sink_caps} ! {sink_element}'

#    PIPELINE += """
#        source. ! decodebin ! {leaky_q} ! videoconvert ! videoscale ! {sink_caps} ! {sink_element}
#        source. ! decodebin ! {leaky_q} ! videoconvert
#        """

#    PIPELINE += " ! vp8enc ! webmmux ! queue leaky=2 ! tcpserversink host=hass.lan port=8778 recover-policy=keyframe sync-method=latest-keyframe"

#PIPELINE += " ! omxh264enc ! h264parse ! tee name=t_out " \
#            "t_out. ! {leaky_q} ! splitmuxsink muxer=matroskamux location=\"tmp/test1-%02d.mkv\" max-size-time=60000000000 " \
#            "t_out. ! {leaky_q} ! decodebin ! vp8enc ! webmmux ! queue leaky=2 ! tcpserversink host=hass.lan port=8778 recover-policy=keyframe sync-method=latest-keyframe"

# ! queue !rtph264depay ! h264parse ! v4l2h264dec capture-io-mode=4 ! v4l2convert output-io-mode=5 capture-io-mode=4 ! video/x-raw, format=RGB'
#         " ! h264parse ! omxh264dec ! videoconvert ! {sink_caps} ! {sink_element}"
#        "! queue ! v4l2h264dec capture-io-mode=4 ! v4l2convert output-io-mode=5 capture-io-mode=4 ! {sink_caps} ! {sink_element}"

#    PIPELINE += """ ! tee name=t
#        t. ! {leaky_q} ! rtph264depay ! h264parse ! v4l2h264dec capture-io-mode=4 ! v4l2convert output-io-mode=5 capture-io-mode=4 ! {sink_caps} ! {sink_element}
#        t. ! {leaky_q} ! videoconvert
#        """
#    PIPELINE += " ! queue ! videoconvert ! omxh264enc ! h264parse ! splitmuxsink muxer=matroskamux location=\"tmp/test1-%02d.mkv\" max-size-time=60000000000"

#         t. ! {leaky_q} ! videoconvert ! {sink_caps} ! {sink_element}
#         t. ! {leaky_q} ! rtph264depay ! h264parse ! v4l2h264dec capture-io-mode=4 ! v4l2video12convert output-io-mode=5 capture-io-mode=4 ! {sink_caps} ! {sink_element}

# OUTDATED:
#    PIPELINE += '{leaky_q} ! videoconvert ! videoscale ! {sink_caps} ! {sink_element}'
#    PIPELINE += " ! splitmuxsink muxer=matroskamux location=\"test1-%02d.mkv\" max-size-time=60000000000"

    LEAKY_Q = 'queue max-size-buffers=1 leaky=downstream'
#    SINK_CAPS = 'video/x-raw,format=RGB'
    SINK_CAPS = 'video/x-raw,format=RGB,width={width},pixel-aspect-ratio=1/1'
    SINK_ELEMENT = 'appsink name=appsink sync=false emit-signals=true max-buffers=1 drop=true'

    sink_caps = SINK_CAPS.format(width=appsink_size[0], height=appsink_size[1])
    pipeline = PIPELINE.format(leaky_q=LEAKY_Q,
                               sink_caps=sink_caps,
                               sink_element=SINK_ELEMENT)
    print('Gstreamer pipeline: ', pipeline)
    pipeline = Gst.parse_launch(pipeline)

    video_src = pipeline.get_by_name('source')
    video_src.props.uri = "rtsp://admin:121174l2ll74@192.168.86.131:554/ISAPI/Streaming/channels/101/picture"
    print("Video source URI: {}".format(video_src.props.uri))
    overlay = pipeline.get_by_name('overlay')
    print("overlay sink: {}".format(str(overlay)))
    appsink = pipeline.get_by_name('appsink')
    print("appsink: {}".format(str(appsink)))
    print("appsink will emit signals: {}".format(appsink.props.emit_signals))
    print("Connecting AI model and detection overlay to video stream")
    appsink.connect('new-sample', partial(on_new_sample,
        overlay=overlay, appsink_size=appsink_size, user_function=user_function))
    loop = GObject.MainLoop()

    # set Gst debug log level
#    Gst.debug_set_active(True)
#    Gst.debug_set_default_threshold(3)

    # Set up a pipeline bus watch to catch errors.
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect('message', on_bus_message, loop)

    # Run pipeline.
    pipeline.set_state(Gst.State.PLAYING)
    try:
        print("Entering main gstreamer loop")
        loop.run()
        print("Exited gstreamer loop")
    except Exception as e:
        sys.stderr("GST loop exited with error: {} ".format(str(e)))
        pass

    # Clean up.
    print("Cleaning up GST resources")
    pipeline.set_state(Gst.State.NULL)
    while GLib.MainContext.default().iteration(False):
        pass
    print("Done.")

