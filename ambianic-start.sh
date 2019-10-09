#!/bin/sh
# docker run -it ambianic/ambianic:v0.1.1
# docker run -it ambianic/ambianic bash
# python3 ambianic.py
# --rm : remove docker container on exit

MY_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
MY_DIR=$(dirname "${MY_PATH}")

# test if coral usb stick is available
USB_DIR=/dev/bus/usb

if [ -d "$DIRECTORY" ]; then
  USB_ARG="--device $USB_DIR"
else
  USB_ARG=""
fi

docker run -it --rm \
  --name ambianic-dev \
  --mount type=bind,source="$MY_DIR",target=/workspace \
  --publish 1234:1234 \
  --publish 8778:8778 \
  $USB_ARG \
  ambianic/ambianic:dev /workspace/src/run-dev.sh
