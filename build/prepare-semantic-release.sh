#!/bin/bash

# verbose mode
set -x

RELEASE_VERSION=$1
a=( ${RELEASE_VERSION//./ } )
MAJOR=${a[0]}
MINOR=${a[1]}
PATCH=${a[2]}
echo "RELEASE_VERSION=$RELEASE_VERSION"
echo "MAJOR=$MAJOR"
echo "MINOR=$MAJOR.$MINOR"
echo "PATCH=$PATCH"

# Which dir are we in?
pwd

# update version info in the ambianic python package setup.cfg
cp README.md src/
cd src
python3 setup.py setopt --command metadata --option version --set-value $RELEASE_VERSION
# verify if version is updated in setup.cfg
cat setup.cfg

# update docker to allow multi-arch manifest support
sudo apt-get update -y
sudo apt-get install --only-upgrade docker-ce -y
echo '{"experimental":true}' | sudo tee /etc/docker/daemon.json
export DOCKER_CLI_EXPERIMENTAL=enabled
sudo service docker restart
docker --version

###
# Build docker images for arm32 and amd64 architectures
###

echo "Preparing docker release for ARM32 architecture "
export ARCH="linux/arm/v7"
export TAG_SUFFIX="arm32v7"
pwd
echo GITHUB_WORKSPACE=${GITHUB_WORKSPACE}
echo "ARCH=${ARCH}"
echo "TAG_SUFFIX=${TAG_SUFFIX}"
${GITHUB_WORKSPACE}/build/ci-prep-release-job.sh

echo "Preparing docker release for AMD64 architecture"
export ARCH="linux/amd64"
export TAG_SUFFIX="amd64"
pwd
echo GITHUB_WORKSPACE=${GITHUB_WORKSPACE}
echo "ARCH=${ARCH}"
echo "TAG_SUFFIX=${TAG_SUFFIX}"
${GITHUB_WORKSPACE}/build/ci-prep-release-job.sh

####
# Docker image versioning section
####
docker pull "ambianic/ambianic-edge:latest"

echo "Creating multi-architecture manifests for each version"
docker manifest create "ambianic/ambianic-edge:$MAJOR" "ambianic/ambianic-edge:latest-amd64" "ambianic/ambianic-edge:latest-arm32v7"
docker manifest annotate "ambianic/ambianic-edge:$MAJOR" "ambianic/ambianic-edge:latest-arm32v7" --os=linux --arch=arm --variant=v7
docker manifest annotate "ambianic/ambianic-edge:$MAJOR" "ambianic/ambianic-edge:latest-amd64" --os=linux --arch=amd64
docker manifest push "ambianic/ambianic-edge:$MAJOR"

docker manifest create "ambianic/ambianic-edge:$MAJOR.$MINOR" "ambianic/ambianic-edge:latest-amd64" "ambianic/ambianic-edge:latest-arm32v7"
docker manifest annotate "ambianic/ambianic-edge:$MAJOR.$MINOR" "ambianic/ambianic-edge:latest-arm32v7" --os=linux --arch=arm --variant=v7
docker manifest annotate "ambianic/ambianic-edge:$MAJOR.$MINOR" "ambianic/ambianic-edge:latest-amd64" --os=linux --arch=amd64
docker manifest push "ambianic/ambianic-edge:$MAJOR.$MINOR"

docker manifest create "ambianic/ambianic-edge:$RELEASE_VERSION" "ambianic/ambianic-edge:latest-amd64" "ambianic/ambianic-edge:latest-arm32v7"
docker manifest annotate "ambianic/ambianic-edge:$RELEASE_VERSION" "ambianic/ambianic-edge:latest-arm32v7" --os=linux --arch=arm --variant=v7
docker manifest annotate "ambianic/ambianic-edge:$RELEASE_VERSION" "ambianic/ambianic-edge:latest-amd64" --os=linux --arch=amd64
docker manifest push "ambianic/ambianic-edge:$RELEASE_VERSION"
