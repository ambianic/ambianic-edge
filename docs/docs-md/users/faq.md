
# Frequently Asked Questions


1. Does Ambianic use hardware accelerators for AI inference?
Yes. Ambianic currently supports the Google Coral EdgeTPU.
The server relies on the Tensorflow Lite Runtime to dynamically detect Coral.
If no EdgeTPU is available, AI inference falls back on the CPU. Check your logs
for messages indicating EdgeTPU availability.
2. Does Ambianic use hardware accelerators for video processing?
Yes. Ambianic relies on `gstreamer` to dynamically detect and use any available
GPU on the host platform for video and image processing.

3. Asked
4. Asked
5. Asked
6.
2.



TBD
