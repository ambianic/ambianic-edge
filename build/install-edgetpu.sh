#!/bin/bash
#
# Based on original Google Coral install script.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

echo architecture=$architecture

set -ex

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
CLEAR="\033[0m"

CPU_ARCH=$(uname -m)
OS_VERSION=$(uname -v)

function info {
  echo -e "${GREEN}${1}${CLEAR}"
}

function warn {
  echo -e "${YELLOW}${1}${CLEAR}"
}

function error {
  echo -e "${RED}${1}${CLEAR}"
}


if [ $architecture == "x86" ]
then
  info "Recognized as Linux on x86_64."
  LIBEDGETPU_SUFFIX=x86_64
  HOST_GNU_TYPE=x86_64-linux-gnu
elif [ $architecture == "arm" ]
then
  info "Recognized as Raspberry Pi"
  LIBEDGETPU_SUFFIX=arm32
  HOST_GNU_TYPE=arm-linux-gnueabihf
fi

if [[ -z "${HOST_GNU_TYPE}" ]]; then
  error "Your platform is not supported."
  exit 1
fi

info "Using default operating frequency."
LIBEDGETPU_SRC="${SCRIPT_DIR}/libedgetpu/libedgetpu_${LIBEDGETPU_SUFFIX}_throttled.so"

LIBEDGETPU_DST="/usr/lib/${HOST_GNU_TYPE}/libedgetpu.so.1.0"

# Install dependent libraries.
info "Installing library dependencies..."
sudo apt-get install -y \
  libusb-1.0-0 \
  python3-pip \
  python3-pil \
  python3-numpy \
  libc++1 \
  libc++abi1 \
  libunwind8 \
  libgcc1
info "Done."

# Device rule file.
UDEV_RULE_PATH="/lib/udev/rules.d/99-edgetpu-accelerator.rules"
info "Installing device rule file [${UDEV_RULE_PATH}]..."

if [[ -f "${UDEV_RULE_PATH}" ]]; then
  warn "File already exists. Replacing it..."
  sudo rm -f "${UDEV_RULE_PATH}"
fi

# Runtime library.
info "Installing Edge TPU runtime library [${LIBEDGETPU_DST}]..."
if [[ -f "${LIBEDGETPU_DST}" ]]; then
  warn "File already exists. Replacing it..."
  sudo rm -f "${LIBEDGETPU_DST}"
fi

sudo cp -p "${LIBEDGETPU_SRC}" "${LIBEDGETPU_DST}"
sudo ldconfig
info "Done."

# Python API.
WHEEL=$(ls ${SCRIPT_DIR}/edgetpu-*-py3-none-any.whl 2>/dev/null)
if [[ $? == 0 ]]; then
  info "Installing Edge TPU Python API..."
  sudo python3 -m pip install --no-deps "${WHEEL}"
  info "Done."
fi
