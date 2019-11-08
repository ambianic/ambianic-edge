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
docker push ambianic/ambianic:${DEV_TAG}
docker manifest create ambianic/ambianic:dev ambianic/ambianic:dev-amd64 ambianic/ambianic:dev-arm32v7
docker manifest annotate ambianic/ambianic:dev ambianic/ambianic:dev-arm32v7 --os=linux --arch=arm --variant=v7
docker manifest annotate ambianic/ambianic:dev ambianic/ambianic:dev-amd64 --os=linux --arch=amd64
docker manifest push ambianic/ambianic:dev

# push prod image
cd ${TRAVIS_BUILD_DIR}
docker build -f ./build/Prod.Dockerfile --platform ${ARCH} -t ambianic/ambianic:${PROD_TAG} .
docker tag ambianic/ambianic:${PROD_TAG} ambianic/ambianic:latest
docker manifest create ambianic/ambianic:latest ambianic/ambianic:latest-amd64 ambianic/ambianic:latest-arm32v7
docker manifest annotate ambianic/ambianic:latest ambianic/ambianic:latest-arm32v7 --os=linux --arch=arm --variant=v7
docker manifest annotate ambianic/ambianic:latest ambianic/ambianic:latest-amd64 --os=linux --arch=amd64
docker manifest push ambianic/ambianic:latest
RELEASE_VERSION=$1
a=( ${RELEASE_VERSION//./ } )
MAJOR=${a[0]}
MINOR=${a[1]}
PATCH=${a[2]}
echo "RELEASE_VERSION=$RELEASE_VERSION"
echo "MAJOR=$MAJOR"
echo "MINOR=$MAJOR.$MINOR"
echo "PATCH=$PATCH"
docker tag ambianic/ambianic:latest ambianic/ambianic:$MAJOR
docker push ambianic/ambianic:$MAJOR
docker tag ambianic/ambianic:latest ambianic/ambianic:"$MAJOR.$MINOR"
docker push ambianic/ambianic:"$MAJOR.$MINOR"
docker tag ambianic/ambianic:latest ambianic/ambianic $RELEASE_VERSION
docker push ambianic/ambianic:$RELEASE_VERSION
