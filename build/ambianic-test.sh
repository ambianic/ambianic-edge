#!/bin/bash

set -ex

# detect effective CPU architecture
if $(arch | grep -q 86)
then
  TAG="dev"
elif $(arch | grep -q arm)
then
  TAG="dev"
fi

MY_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
MY_DIR=$(dirname "${MY_PATH}")

# run tests
docker run --rm \
  --name ambianic-dev \
  --mount type=bind,source="$MY_DIR/../",target=/workspace \
  --net=host \
  --entrypoint 'bash' \
  -e CODECOV_TOKEN \
  ambianic/ambianic-edge:$TAG /workspace/tests/run-tests.sh -u
