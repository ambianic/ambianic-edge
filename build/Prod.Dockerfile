# Production version of Ambianic docker image
FROM ambianic/ambianic-edge:dev
LABEL maintainer="Ivelin Ivanov <ivelin@ambianic.ai>"

VOLUME /workspace

WORKDIR /opt/ambianic-edge
RUN pwd && ls -al
# assuming the context of docker build is ambianid-edge/src
COPY ["./src", "README.md", "./src/"]
COPY ["./ai_models", "./ai_models/"]

# install the ambianic python package on this docker image
RUN ls -al ./src/* && pip3 install -e src

# copy entrypoint script to docker image
COPY ["./build/ambianic-docker-entrypoint.sh", "./"]

# copy config defaults to docker image
COPY ["./config.defaults.yaml", "./"]


WORKDIR /workspace

# expose http port
# EXPOSE 8778

# ENTRYPOINT ["python3"]
# CMD [ "-m", "ambianic" ]
ENTRYPOINT ["bash"]
CMD ["/opt/ambianic-edge/ambianic-docker-entrypoint.sh"]
