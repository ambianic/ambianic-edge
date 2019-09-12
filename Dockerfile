FROM python:3.7.4-slim-buster
LABEL maintainer="Ivelin Ivanov <ivelin@ambianic.ai>"

VOLUME /workspace

WORKDIR /opt/ambianic

# quietly update apt-get and install sudo which is not available by default on slim buster
RUN apt-get update -qq && apt-get install -qq sudo

# Copy native dependencies install script
COPY install_requirements.sh install_requirements.sh
RUN ./install_requirements.sh

# CMD bash

# [backend setup]
# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# [frontend setup]
# install npm packages
# cd ambianic/webapp/client
# npm install node
# npm install --save vue
# npm install --save-dev parcel-bundler
# ...
# build frontend bundles
# parcel ...
# cleanup
# remove npm, parcel and other build time tools

# expose http port
EXPOSE 8778

# CMD bash
ENTRYPOINT ["bash"]
# CMD [ "ambianic_start_daemon.sh" ]
