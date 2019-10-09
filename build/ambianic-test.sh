#!/bin/sh

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

docker run -it --rm \
  --name ambianic-dev \
  --mount type=bind,source="$MY_DIR/../",target=/workspace \
  --publish 1234:1234 \
  --publish 8778:8778 \
  --entrypoint 'bash' \
  -e CODECOV_TOKEN \
  ambianic/ambianic:$TAG /workspace/tests/run-tests.sh
