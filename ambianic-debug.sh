#!/bin/bash
set -ex

MY_PATH=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
MY_DIR=$(dirname "${MY_PATH}")

# test if coral usb stick is available
USB_DIR=/dev/bus/usb

VIDEO_0=/dev/video0

if [ -d "$USB_DIR" ]; then
  USB_ARG="--device $USB_DIR"
else
  USB_ARG=""
fi

if [ -e "$VIDEO_0" ]; then
  VIDEO_ARG="--device $VIDEO_0"
else
  VIDEO_ARG=""
fi

# check if there is an image update
docker pull ambianic/ambianic-edge:dev
# run dev image
docker run -it --rm \
  --name ambianic-edge-dev \
  --mount type=bind,source="$MY_DIR",target=/workspace \
  --net=host \
  $VIDEO_ARG \
  $USB_ARG \
  ambianic/ambianic-edge:dev
