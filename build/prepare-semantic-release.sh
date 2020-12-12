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

# update version info in the ambianic python package setup.cfg
cp README.md src/
cd src
python3 setup.py setopt --command metadata --option version --set-value $RELEASE_VERSION


# update docker to allow multi-arch manifest support
sudo apt-get update -y
sudo apt-get install --only-upgrade docker-ce -y
echo '{"experimental":true}' | sudo tee /etc/docker/daemon.json
export DOCKER_CLI_EXPERIMENTAL=enabled
sudo service docker restart
docker --version

docker pull "ambianic/ambianic-edge:latest"

# create versioned image tags
# docker tag "ambianic/ambianic-edge:latest" "ambianic/ambianic-edge:$MAJOR"
# docker push "ambianic/ambianic-edge:$MAJOR"
# docker tag "ambianic/ambianic-edge:latest" "ambianic/ambianic-edge:$MAJOR.$MINOR"
# docker push "ambianic/ambianic-edge:$MAJOR.$MINOR"
# docker tag "ambianic/ambianic-edge:latest" "ambianic/ambianic-edge:$RELEASE_VERSION"
# docker push "ambianic/ambianic-edge:$RELEASE_VERSION"

# create multi-architecture manifests for each version
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
