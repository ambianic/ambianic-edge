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
if $(type python3 || (pyenv versions | grep 3))
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
  
fi

# install python dependencies
python3 -m pip install --upgrade pip
pip3 --version
pip3 install -r requirements.txt

  # install gcc as some of the python native dependencies
  # like pycairo don't ship as PIP packages and require build from source.
  # apt-get install gcc

# [AI]
# Install Tensorflow Lite and EdgeTPU libraries for the underlying architecture
if $(arch | grep -q 86)
then
  echo "Installing tflite for x86 CPU"
  sudo pip3 install https://github.com/google-coral/pycoral/releases/download/release-frogfish/tflite_runtime-2.5.0-cp38-cp38-linux_x86_64.whl
elif $(arch | grep -q arm)
then
  echo "Installing tflite for ARM CPU"
  sudo pip3 install https://dl.google.com/coral/python/tflite_runtime-1.14.0-cp37-cp37m-linux_armv7l.whl
fi

pip3 show tflite-runtime

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
pip3 install peerjs

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
