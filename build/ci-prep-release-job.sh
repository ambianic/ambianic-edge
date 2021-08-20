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

# echo "Clean up any leftover docker build artifacts
# docker builder prune --all
echo "Clean up any previous docker artifacts"
yes | docker system prune --all


# Raspberry PI section
# prepare qemu
DEV_TAG=dev-${TAG_SUFFIX}
PROD_TAG=latest-${TAG_SUFFIX}
docker run --rm --privileged docker/binfmt:66f9012c56a8316f9244ffd7622d7c21c1f6f28d
cat /proc/sys/fs/binfmt_misc/qemu-aarch64

echo "Publishing docker binaries and multi-arch manifests"
echo "ARCH=$ARCH"
echo "DEV_TAG=$DEV_TAG"
echo "PROD_TAG=$PROD_TAG"
pwd
ls -al

echo "Building dev image"
cd ${GITHUB_WORKSPACE}/build
docker build -f Dev.Dockerfile --no-cache --platform ${ARCH} -t "ambianic/ambianic-edge:${DEV_TAG}" .
docker tag ambianic/ambianic-edge:${DEV_TAG} "ambianic/ambianic-edge:dev"
docker images
cd ${GITHUB_WORKSPACE}/build

# dockerhub login is now done safer via github action
# docker login -u="$DOCKER_USER" -p="$DOCKER_PASS"
docker push "ambianic/ambianic-edge:${DEV_TAG}"
docker manifest create "ambianic/ambianic-edge:dev" "ambianic/ambianic-edge:dev-amd64" "ambianic/ambianic-edge:dev-arm32v7"
docker manifest annotate "ambianic/ambianic-edge:dev" "ambianic/ambianic-edge:dev-arm32v7" --os=linux --arch=arm --variant=v7
docker manifest annotate "ambianic/ambianic-edge:dev" "ambianic/ambianic-edge:dev-amd64" --os=linux --arch=amd64
docker manifest push "ambianic/ambianic-edge:dev"

cd ${GITHUB_WORKSPACE}
pwd
ls -al

echo "Building production image"
docker build -f ./build/Prod.Dockerfile --no-cache --platform ${ARCH} -t "ambianic/ambianic-edge:${PROD_TAG}" .
docker tag "ambianic/ambianic-edge:${PROD_TAG}" "ambianic/ambianic-edge:latest"
docker push "ambianic/ambianic-edge:${PROD_TAG}"
docker manifest create "ambianic/ambianic-edge:latest" "ambianic/ambianic-edge:latest-amd64" "ambianic/ambianic-edge:latest-arm32v7"
docker manifest annotate "ambianic/ambianic-edge:latest" "ambianic/ambianic-edge:latest-arm32v7" --os=linux --arch=arm --variant=v7
docker manifest annotate "ambianic/ambianic-edge:latest" "ambianic/ambianic-edge:latest-amd64" --os=linux --arch=amd64
docker manifest push "ambianic/ambianic-edge:latest"

echo $PWD
cd ${GITHUB_WORKSPACE}
ls -al
