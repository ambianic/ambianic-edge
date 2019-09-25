# install native package that Ambianic needs to run

echo "Installing Ambianic dependencies"

# exit bash script on error
set -e

# verbose mode
set -x


# detect effective CPU architecture
if $(arch | grep -q 86)
then
  architecture="x86"
elif $(arch | grep -q arm)
then
  architecture="arm"
fi
echo $(arch)
echo "Effective CPU architecture: $architecture"

# quietly update apt-get, install sudo and python3 which is not available by default on slim buster
apt-get update -y && apt-get install -y sudo && apt-get install -y python3 && apt-get install -y python3-pip

# Install gstreamer
sudo apt-get update && sudo apt-get install -y gstreamer1.0-plugins-bad gstreamer1.0-plugins-good python3-gst-1.0 python3-gi

# [backend]

# make sure python sees the packages installed via apt-get
# export PYTHONPATH=$PYTHONPATH:/usr/lib/python3/dist-packages
# echo "export PYTHONPATH=$PYTHONPATH:/usr/lib/python3/dist-packages" >> $HOME/.bashrc

# Install Raspberry Pi video drivers
if grep -s -q "Raspberry Pi" /sys/firmware/devicetree/base/model; then
  echo "Installing Raspberry Pi specific dependencies"
  sudo apt-get install python3-rpi.gpio
  # Add v4l2 video module to kernel
  if ! grep -q "bcm2835-v4l2" /etc/modules; then
    echo bcm2835-v4l2 | sudo tee -a /etc/modules
  fi
  sudo modprobe bcm2835-v4l2
fi

# install python dependencies
sudo pip3 install -U pip
sudo pip3 install -r requirements.txt

  # install gcc as some of the python native dependencies
  # like pycairo don't ship as PIP packages and require build from source.
  # apt-get install gcc

# [AI]
# Install Tensorflow Lite and EdgeTPU libraries
# TODO: Add multi-architecture build instructions: [ARM, x86] x [32,64]
if [ $architecture == "x86" ]
then
  echo "Installing tflite for X86"
  sudo pip3 install https://dl.google.com/coral/python/tflite_runtime-1.14.0-cp37-cp37m-linux_x86_64.whl
elif [ $architecture == "arm" ]
then
  sudo pip3 install https://dl.google.com/coral/python/tflite_runtime-1.14.0-cp37-cp37m-linux_armv7l.whl
fi

wget https://dl.google.com/coral/edgetpu_api/edgetpu_api_latest.tar.gz -O edgetpu_api.tar.gz --trust-server-names

tar xzf edgetpu_api.tar.gz

sudo edgetpu_api/install.sh

# install ai models
# mkdir -p ai_models
# wget https://dl.google.com/coral/canned_models/all_models.tar.gz
# tar -C ai_models -xvzf all_models.tar.gz
# rm -f all_models.tar.gz

# [frontend]

# install latest npm
sudo apt-get install -y npm
# cd ambianic/webapp/client
# sudo npm install -g npm@latest
# sudo npm install -g @vue/cli
# npm run build
# cd ../../../


# install local npm dependencies from package.json
# runtime dir is where the executable code resides
# workspace is where local customer configuration files and user data goes
# cd $runtimedir
# cd ambianic/webapp/client
# npm install

# [Cleanup]
sudo apt-get -y autoremove

# remove apt-get cache
sudo  rm -rf /var/lib/apt/lists/*

# This is run automatically on Debian and Ubuntu, but just in case
sudo apt-get clean
