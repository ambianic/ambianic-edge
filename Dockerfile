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

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# expose http port
EXPOSE 8778

# CMD bash
CMD [ "python3", "ambianic.py", "--workspace", "/workspace" ]
