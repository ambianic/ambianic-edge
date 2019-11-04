# Production version of Ambianic docker image
FROM ambianic:dev
LABEL maintainer="Ivelin Ivanov <ivelin@ambianic.ai>"

VOLUME /workspace

WORKDIR /opt/ambianic
COPY src/ /src/
RUN ls -la /src/* && pip3 install -e src

WORKDIR /workspace

# expose http port
EXPOSE 8778

# CMD bash
ENTRYPOINT ["bash"]
CMD [ "python3", "-m", "ambianic" ]
