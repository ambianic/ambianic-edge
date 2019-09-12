# install native package that Ambianic needs to run

echo "Installing Ambianic dependencies"

# Install gstreamer
sudo apt-get update && sudo apt-get install -y gstreamer1.0-plugins-bad gstreamer1.0-plugins-good python3-gst-1.0 python3-gi

# [backend]

# make sure python sees the packages installed via apt-get
# export PYTHONPATH=$PYTHONPATH:/usr/lib/python3/dist-packages
echo "export PYTHONPATH=$PYTHONPATH:/usr/lib/python3/dist-packages" >> $HOME/.bashrc

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
pip3 install -U pip
pip3 install -r requirements.txt

  # install gcc as some of the python native dependencies
  # like pycairo don't ship as PIP packages and require build from source.
  # apt-get install gcc

# install ai models
mkdir -p ai_models
wget https://dl.google.com/coral/canned_models/all_models.tar.gz
tar -C ai_models -xvzf all_models.tar.gz
rm -f all_models.tar.gz

# [frontend]

# install latest npm
cd ambianic/webapp/client
sudo apt-get install -y npm
# sudo npm install -g npm@latest
# sudo npm install node
sudo npm install -g @vue/cli
sudo npm install -g parcel-bundler
cd ../../../

# install local npm dependencies from package.json
# runtime dir is where the executable code resides
# workspace is where local customer configuration files and user data goes
# cd $runtimedir
# cd ambianic/webapp/client
# npm install
