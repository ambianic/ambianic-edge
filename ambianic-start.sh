#!/bin/sh
# docker run -it ambianic/ambianic:v0.1.1
# docker run -it ambianic/ambianic bash
# python3 ambianic.py
# --rm : remove docker container on exit
docker run -it --rm \
  --name ambianic-dev \
  --mount type=bind,source="$(pwd)",target=/workspace \
  --publish 1234:1234 \
  ambianic/ambianic
