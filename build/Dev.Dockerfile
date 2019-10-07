# Development version of Ambianic docker image
ARG BASE_IMAGE
RUN echo BASE_IMAGE=$BASE_IMAGE
FROM ${BASE_IMAGE}

LABEL maintainer="Ivelin Ivanov <ivelin@ambianic.ai>"

VOLUME /workspace

WORKDIR /opt/ambianic

# Copy dependencies install list and script
# COPY install_requirements.sh install_requirements.sh
COPY ["install_requirements.sh", "requirements.txt", "install-edgetpu.sh", "./"]
RUN ./install_requirements.sh

# CMD bash

# [backend setup]
# Install Python dependencies
# COPY requirements.txt requirements.txt
# RUN pip3 install --no-cache-dir -r requirements.txt

# [production]

# Copy source for prod docker image
# COPY . .

# [frontend setup]
# RUN cd ambianic/webapp/client && \
#  npm install --save vue \
#  npm install --save-dev parcel-bundler \
#  npm install --save axios

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

# [development]

# dev only front end server
EXPOSE 1234

# CMD bash
ENTRYPOINT ["bash"]
# CMD [ "ambianic_start_daemon.sh" ]
