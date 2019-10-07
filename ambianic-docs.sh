#!/bin/sh

# exit on error , verbose mode
set -ex

# detect effective CPU architecture
if $(arch | grep -q 86)
then
  TAG="dev-x86"
elif $(arch | grep -q arm)
then
  TAG="dev-arm"
fi


docker run -it --rm \
  --name ambianic-dev \
  --mount type=bind,source="$(pwd)",target=/workspace \
  --publish 1234:1234 \
  --publish 8778:8778 \
  --entrypoint 'bash' \
  ambianic/ambianic::$TAG /workspace/docs/build-docs.sh
