#!/bin/sh

set -ex

docker run -it --rm \
  --name ambianic-dev \
  --mount type=bind,source="$(pwd)",target=/workspace \
  --publish 1234:1234 \
  --publish 8778:8778 \
  --entrypoint 'bash' \
  -e CODECOV_TOKEN \
  ambianic/ambianic:dev /workspace/tests/run-tests.sh
