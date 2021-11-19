#!/bin/bash

# verbose shell mode and fail fast
set -ex

# Re-Install ARM/Raspberry Pi ca-certifcates
# Which otherwise cause SSL Certificate Verification problems.
if $(arch | grep -q arm)
then
  sudo dpkg --configure -a
  ## update local package info db
  echo "Re-Installing ca-certifcates on Raspberry Pi / ARM CPU due to unresolved cert validation errors."
  sudo apt-get remove -y ca-certificates
  # update references to new package version info
  sudo apt-get update
  # allow use of previous stable linux image in case a new version became the default
  sudo apt update --allow-releaseinfo-change
  # reinstall ca-certificates to pick up any updates
  sudo apt-get install -y ca-certificates
fi

# start peerjs HTTP proxy
python3 -m peerjs.ext.http_proxy   &
# start OpenAPI (fastapi/uvicorn) server
python3 -m uvicorn ambianic.webapp.fastapi_app:app --port 8778 &
# set list of config files
AMBIANIC_CONFIG_FILES=/opt/ambianic-edge/config.defaults.yaml, config.yaml, config.local.yaml
AMBIANIC_SAVE_CONFIG_TO=config.local.yaml
# start ambianic-edge core
python3 -m ambianic
