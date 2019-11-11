# Production version of Ambianic docker image
FROM ambianic/ambianic-edge:dev
LABEL maintainer="Ivelin Ivanov <ivelin@ambianic.ai>"

VOLUME /workspace

WORKDIR /opt/ambianic-edge
RUN pwd && ls -al
# assuming the context of docker build is ambianid-edge/src
COPY [".", "./src/"]
COPY ["README.md", "./"]
RUN ls -al ./src/* && pip3 install -e src

WORKDIR /workspace

# expose http port
EXPOSE 8778

# CMD bash
ENTRYPOINT ["bash"]
CMD [ "python3", "-m", "ambianic" ]
