#!/bin/sh
# docker run -it ambianic/ambianic:v0.1.1
# docker run -it ambianic/ambianic bash
# python3 ambianic.py
# --rm : remove docker container on exit
docker run -it \
  --name ambianic-dev \
  --mount type=bind,source="$(pwd)",target=/workspace \
  ambianic/ambianic
