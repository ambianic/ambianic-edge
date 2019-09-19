#!/bin/sh

# exit on error , verbose mode
set -ex

docker run -it --rm \
  --name ambianic-dev \
  --mount type=bind,source="$(pwd)",target=/workspace \
  --publish 1234:1234 \
  --publish 8778:8778 \
  --entrypoint 'bash' \
  ambianic/ambianic:dev /workspace/docs/build-docs.sh
