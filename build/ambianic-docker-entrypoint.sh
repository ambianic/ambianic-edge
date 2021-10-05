#!/bin/bash

# verbose shell mode and fail fast
set -ex

# Re-Install ARM/Raspberry Pi ca-certifcates
# Which otherwise cause SSL Certificate Verification problems.
if $(arch | grep -q arm)
then
  sudo dpkg --configure -a
  ## update local package info db
  # sudo apt-get update
  echo "Re-Installing ca-certifcates on Raspberry Pi / ARM CPU due to unresolved cert validation errors."
  sudo apt-get remove -y ca-certificates
  sudo apt-get install -y ca-certificates
fi

# start peerjs HTTP proxy
python3 -m peerjs.ext.http_proxy   &
# start OpenAPI (fastapi/uvicorn) server
python3 -m uvicorn ambianic.webapp.fastapi_app:app --port 8778 &
# start ambianic-edge core
python3 -m ambianic --config "config.yaml"
