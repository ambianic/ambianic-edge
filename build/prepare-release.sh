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
docker tag "ambianic/ambianic-edge:latest" "ambianic/ambianic-edge:$MAJOR"
docker push "ambianic/ambianic-edge:$MAJOR"
docker tag "ambianic/ambianic-edge:latest" "ambianic/ambianic-edge:$MAJOR.$MINOR"
docker push "ambianic/ambianic-edge:$MAJOR.$MINOR"
docker tag "ambianic/ambianic-edge:latest" "ambianic/ambianic-edge:$RELEASE_VERSION"
docker push "ambianic/ambianic-edge:$RELEASE_VERSION"
