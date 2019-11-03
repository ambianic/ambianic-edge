#!/bin/bash
set -ex

MY_PATH=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
MY_DIR=$(dirname "${MY_PATH}")

# test if coral usb stick is available
USB_DIR=/dev/bus/usb

if [ -d "$USB_DIR" ]; then
  USB_ARG="--device $USB_DIR"
else
  USB_ARG=""
fi

# check if there is an image update
docker pull ambianic/ambianic:dev
# run dev image
docker run -it --rm \
  --name ambianic-dev \
  --mount type=bind,source="$MY_DIR",target=/workspace \
  --publish 1234:1234 \
  --publish 8778:8778 \
  $USB_ARG \
  ambianic/ambianic:dev 
