#!/bin/bash
VERSION=$1
a=( ${VERSION//./ } )
MAJOR=$a[0]
MINOR=$a[1]
PATCH=$a[2]
$ docker tag ambianic/ambianic:latest ambianic/ambianic:$MAJOR
$ docker push ambianic/ambianic:$MAJOR
$ docker tag ambianic/ambianic:latest ambianic/ambianic:"$MAJOR.$MINOR"
$ docker push ambianic/ambianic:"$MAJOR.$MINOR"
$ docker tag ambianic/ambianic:latest ambianic/ambianic $VERSION
$ docker push ambianic/ambianic:$VERSION
