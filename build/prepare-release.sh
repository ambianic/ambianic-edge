#!/bin/bash

# verbose mode
set -x

echo "ARCH=$ARCH"
echo "DEV_TAG=$DEV_TAG"
echo "PROD_TAG=$PROD_TAG"
pwd
ls -al

# push dev image
docker login -u="$DOCKER_USER" -p="$DOCKER_PASS"
docker push ambianic/ambianic-edge:${DEV_TAG}
docker manifest create ambianic/ambianic-edge:dev ambianic/ambianic-edge:dev-amd64 ambianic/ambianic-edge:dev-arm32v7
docker manifest annotate ambianic/ambianic-edge:dev ambianic/ambianic-edge:dev-arm32v7 --os=linux --arch=arm --variant=v7
docker manifest annotate ambianic/ambianic-edge:dev ambianic/ambianic-edge:dev-amd64 --os=linux --arch=amd64
docker manifest push ambianic/ambianic-edge:dev

# push prod image
cd ${TRAVIS_BUILD_DIR}
pwd
ls -al

cp README.md ./src

docker build -f ./build/Prod.Dockerfile --platform ${ARCH} -t "ambianic/ambianic-edge:${PROD_TAG}" ./src
docker tag ambianic/ambianic-edge:${PROD_TAG} ambianic/ambianic-edge:latest
docker manifest create ambianic/ambianic-edge:latest ambianic/ambianic-edge:latest-amd64 ambianic/ambianic-edge:latest-arm32v7
docker manifest annotate ambianic/ambianic-edge:latest ambianic/ambianic-edge:latest-arm32v7 --os=linux --arch=arm --variant=v7
docker manifest annotate ambianic/ambianic-edge:latest ambianic/ambianic-edge:latest-amd64 --os=linux --arch=amd64
docker manifest push ambianic/ambianic-edge:latest
RELEASE_VERSION=$1
a=( ${RELEASE_VERSION//./ } )
MAJOR=${a[0]}
MINOR=${a[1]}
PATCH=${a[2]}
echo "RELEASE_VERSION=$RELEASE_VERSION"
echo "MAJOR=$MAJOR"
echo "MINOR=$MAJOR.$MINOR"
echo "PATCH=$PATCH"
docker tag ambianic/ambianic-edge:latest ambianic/ambianic-edge:$MAJOR
docker push ambianic/ambianic-edge:$MAJOR
docker tag ambianic/ambianic-edge:latest ambianic/ambianic-edge:"$MAJOR.$MINOR"
docker push ambianic/ambianic-edge:"$MAJOR.$MINOR"
docker tag ambianic/ambianic-edge:latest ambianic/ambianic-edge $RELEASE_VERSION
docker push ambianic/ambianic-edge:$RELEASE_VERSION
