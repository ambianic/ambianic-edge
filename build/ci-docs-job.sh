#!/bin/bash
# Run testsuite within a CI workflow

# set bash debug parameters
set -exu

# build docs

TAG="dev"

MY_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
MY_DIR=$(dirname "${MY_PATH}")

# run tests
docker run --rm \
  --name ambianic-dev \
  --mount type=bind,source="$MY_DIR/../",target=/workspace \
  --net=host \
  --entrypoint 'bash' \
  -e CODECOV_TOKEN \
  ambianic/ambianic-edge:$TAG /workspace/docs/build-docs.sh -u
