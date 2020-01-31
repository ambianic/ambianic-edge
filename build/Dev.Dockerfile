# Development version of Ambianic docker image
FROM debian:buster-slim
LABEL maintainer="Ivelin Ivanov <ivelin@ambianic.ai>"

VOLUME /workspace

WORKDIR /opt/ambianic-edge

# Copy dependencies install list and script
# COPY install_requirements.sh install_requirements.sh
COPY ["install_requirements.sh", "requirements.txt", "install-edgetpu.sh", \
  "raspberrypi.pip.conf", "./"]
RUN /bin/bash ./install_requirements.sh

# expose http port
# EXPOSE 8778

# CMD bash
ENTRYPOINT ["bash"]
# CMD [ "ambianic_start_daemon.sh" ]
