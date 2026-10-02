ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base:latest
FROM $BUILD_FROM

RUN apk add --no-cache python3 py3-pip \
    && pip3 install --no-cache-dir --break-system-packages "websockets>=13,<16" "aiomqtt>=2.3,<3"

COPY savant.py run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
