#!/bin/bash
# exit bash script on error
set -e

# verbose mode
set -x

# Build Ambianic's development mode docker image
TAG="ambianic/ambianic:dev"

docker build --file Dev.Dockerfile --tag $TAG ./
docker run --rm --entrypoint echo "$TAG" "Hello $hello"
# docker push $TAG

# Build Ambianic's production mode docker image
TAG="ambianic/ambianic:latest"

docker build --file Prod.Dockerfile --tag $TAG ./
docker run --rm --entrypoint echo "$TAG" "Hello $hello"
# docker push $TAG
