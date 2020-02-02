#!/bin/bash

# verbose shell mode and fail fast
set -ex

python3 -m peerjs.ext.http-proxy   &
python3 -m ambianic
