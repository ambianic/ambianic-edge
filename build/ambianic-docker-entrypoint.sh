#!/bin/bash

# verbose shell mode and fail fast
set -ex

# Re-Install ARM/Raspberry Pi ca-certifcates
# Which otherwise cause SSL Certificate Verification problems.
if $(arch | grep -q arm)
then
  echo "Re-Installing ca-certifcates on Raspberry Pi / ARM CPU"
  sudo apt-get remove -y ca-certificates
  sudo apt-get update
  sudo apt-get install -y ca-certificates
fi

python3 -m peerjs.ext.http-proxy   &
python3 -m ambianic
