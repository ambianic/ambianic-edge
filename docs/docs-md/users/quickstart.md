
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
