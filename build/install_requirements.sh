#!/bin/bash

# install native package that Ambianic needs to run

echo "Installing Ambianic dependencies"

# exit bash script on error
set -e

# verbose mode
set -x


# detect effective CPU architecture
if $(arch | grep -q 86)
then
  export architecture="x86"
elif $(arch | grep -q arm)
then
  export architecture="arm"
fi
echo arch=$(arch)
echo "Effective CPU architecture: $architecture"

# update apt-get and install sudo
apt-get update -y && apt-get install -y sudo

# check if python3 is installed
if python3 --version
then
  echo "python3 is already installed."
else
  # install python3 and pip3 which are not available by default on slim buster
  echo "python3 is not available from the parent image. Installing python3 now."
  sudo apt-get install -y python3 && apt-get install -y python3-pip
fi

# Install gstreamer
sudo apt-get update
sudo apt-get install -y libgstreamer1.0-0 gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav gstreamer1.0-doc \
  gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 \
  gstreamer1.0-pulseaudio \
  python3-gst-1.0 python3-gi
# install numpy native lib
sudo apt-get install -y python3-numpy
sudo apt-get install -y libjpeg-dev zlib1g-dev
# [backend]

# update ca certificates to prevent remote ssl download requests from erroring
sudo apt install ca-certificates
sudo update-ca-certificates -f -v

# make sure python sees the packages installed via apt-get
# export PYTHONPATH=$PYTHONPATH:/usr/lib/python3/dist-packages
# echo "export PYTHONPATH=$PYTHONPATH:/usr/lib/python3/dist-packages" >> $HOME/.bashrc

# Install Raspberry Pi video drivers
if $(arch | grep -q arm)
# there is no RPI firmware in docker images, so we will install on ARM flag
#if grep -s -q "Raspberry Pi" /sys/firmware/devicetree/base/model; then
then
  # avoid install during CI builds
  echo "Installing Raspberry Pi / ARM CPU specific dependencies"
  sudo READTHEDOCS=True pip3 install --upgrade RPi.GPIO picamera

  # sudo apt-get install -y modprobe
  # Add v4l2 video module to kernel
  #  if ! grep -q "bcm2835-v4l2" /etc/modules; then
  #    echo bcm2835-v4l2 | sudo tee -a /etc/modules
  #  fi
  #  sudo modprobe bcm2835-v4l2

  # Enable python wheels for rpi
  sudo cp raspberrypi.pip.conf /etc/pip.conf

  # install rust as it is required to build python packages that are not available as binary pip packages
  # for example orjson
  sudo curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -ksSf | sh

  
fi

# install python dependencies
python3 -m pip install --upgrade pip
python3 -m pip --version
python3 -m pip install -r requirements.txt

  # install gcc as some of the python native dependencies
  # like pycairo don't ship as PIP packages and require build from source.
  # apt-get install gcc

# [AI]
# Install Tensorflow Lite and EdgeTPU libraries for the underlying architecture
# ref: https://www.tensorflow.org/lite/guide/python
if $(arch | grep -q 86)
then
  echo "Installing tflite for x86 CPU"
  pip3 install --index-url https://google-coral.github.io/py-repo/ tflite_runtime
elif $(arch | grep -q arm)
then
  echo "Installing tflite for ARM CPU including Raspberry Pi"
  echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
  sudo apt-get update
  sudo apt-get install python3-tflite-runtime
fi

python3 -m pip show tflite-runtime

# install wget
apt-get install -y curl

# wget https://dl.google.com/coral/edgetpu_api/edgetpu_api_latest.tar.gz -O edgetpu_api.tar.gz --trust-server-names
curl -k -L -o /tmp/edgetpu_api.tar.gz https://dl.google.com/coral/edgetpu_api/edgetpu_api_latest.tar.gz

tar xzf /tmp/edgetpu_api.tar.gz -C /tmp --no-same-owner

echo "Effective CPU architecture: $architecture"
export architecture
pwd
ls -al
# ls -al build/
cp install-edgetpu.sh /tmp/edgetpu_api/install.sh
/tmp/edgetpu_api/install.sh


# [PeerJS Python]
# Install native dependencies for aiortc
apt-get install -y libavdevice-dev libavfilter-dev libopus-dev libvpx-dev pkg-config
apt-get install -y libsrtp2-dev
# Install peerjs python
python3 -m pip install peerjs

# [devtools]
# Install tools essential for debugging docker image related problems
apt-get install -y procps

# install ai models
# mkdir -p ai_models
# wget https://dl.google.com/coral/canned_models/all_models.tar.gz
# tar -C ai_models -xvzf all_models.tar.gz
# rm -f all_models.tar.gz

# [Cleanup]
sudo apt-get -y autoremove

# remove apt-get cache
sudo  rm -rf /var/lib/apt/lists/*

# This is run automatically on Debian and Ubuntu, but just in case
sudo apt-get clean
