
# Quick Start

Ambianic's main goal is to provide helpful suggestions in the context of home
and business automation. The main unit of work is the Ambianic pipeline.
The following diagram illustrates an example pipeline that takes as input a video stream
 URI source such as a surveillance camera and
outputs object detections to a local directory.

<div class="diagram">
st=>start: Video Source
op_obj=>operation: Object Detection AI
op_sav1=>parallel: Storage Element
io1=>inputoutput: save object detections to file
op_face=>operation: Face Detection AI
op_sav2=>parallel: Storage Element
io2=>inputoutput: save face detections to file
e=>end: Output to other pipelines

st->op_obj
op_obj(bottom)->op_sav1
op_sav1(path1, bottom)->op_face
op_sav1(path2, right)->io1
op_face(bottom)->op_sav2
op_sav2(path1, bottom)->e
op_sav2(path2, right)->io2
</div>

<script>
$(".diagram").flowchart();
</script>

<br/>

## Configuration

Here is the corresponding configuration section in `config.yaml` for the pipeline above:

```yaml
pipelines:
  # sequence of piped operations for use in daytime front door watch
  daytime_front_door_watch:
    - source: *src_front_door_cam
    - detect_objects: # run ai inference on the input data
        <<: *tfm_image_detection
        confidence_threshold: 0.8
    - save_detections: # save samples from the inference results
        output_directory: *object_detect_dir
        positive_interval: 2 # how often (in seconds) to save samples with ANY results above the confidence threshold
        idle_interval: 6000 # how often (in seconds) to save samples with NO results above the confidence threshold
    - detect_faces: # run ai inference on the samples from the previous element output
        <<: *tfm_face_detection
        confidence_threshold: 0.8
    - save_detections: # save samples from the inference results
        output_directory: *face_detect_dir
        positive_interval: 2
        idle_interval: 600

```

In the configuration excerpt above, there are a few references to variables
defined elsewhere in the YAML file. `*src_front_door_cam` is the only
reference that you have to understand and configure in order
to get Ambianic working with your own camera (or other source of video feed).

Here is the definition of this variable reference that you will find in config.yaml:

```yaml
sources:
  front_door_camera: &src_front_door_cam
    uri: *secret_uri_front_door_camera
    type: video
```

The key parameter here is `uri`. We recommended that you store the value
in `secrets.yaml` which needs to be located in the same directory as
`config.yaml`.

A valid entry in `secretes.yaml` for a camera URI, would look like this:
```yaml
secret_uri_front_door_camera: &secret_uri_front_door_camera 'rtsp://user:pass@192.168.86.111:554/Streaming/Channels/101'
# add more secret entries as regular yaml mappings
```

Assuming you are familiar with yaml syntax, the rest of the configuration
settings can be left with their default values.

Once you specify the URI of your camera, you can navigate to the Ambianic
working directory and start the server with:
```sh
./ambianic-start.sh
```

You can find object and face detections stored in the `./data`
directory by default.
