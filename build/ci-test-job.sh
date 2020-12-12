#!/bin/bash

# set bash debug parameters
set -exu

echo "Building for CPU architecture: ${ARCH}"

# Prepare docker engine enviroment
# sudo apt-get update -y
# sudo apt-get install --only-upgrade docker-ce -y
# docker is already installed on the github action base image
# sudo curl -fsSL get.docker.com | CHANNEL=stable sh
echo '{"experimental":true}' | sudo tee /etc/docker/daemon.json
export DOCKER_CLI_EXPERIMENTAL=enabled
sudo service docker restart
docker --version

# Raspberry PI section
# prepare qemu
DEV_TAG=dev-${TAG_SUFFIX}
PROD_TAG=latest-${TAG_SUFFIX}
docker run --rm --privileged docker/binfmt:66f9012c56a8316f9244ffd7622d7c21c1f6f28d
cat /proc/sys/fs/binfmt_misc/qemu-aarch64
cd ${GITHUB_WORKSPACE}/build
docker build -f Dev.Dockerfile --platform ${ARCH} -t "ambianic/ambianic-edge:${DEV_TAG}" .
docker tag ambianic/ambianic-edge:${DEV_TAG} "ambianic/ambianic-edge:dev"
docker images
cd ${GITHUB_WORKSPACE}/build
./ambianic-test.sh
