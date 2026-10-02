#!/usr/bin/with-contenv bashio
# MQTT login comes from Home Assistant's Mosquitto add-on (services: mqtt:need), no password to keep.
export SAVANT_HOST="$(bashio::config 'savant_host')"
export MQTT_HOST="$(bashio::services mqtt 'host')"
export MQTT_PORT="$(bashio::services mqtt 'port')"
export MQTT_USER="$(bashio::services mqtt 'username')"
export MQTT_PASSWORD="$(bashio::services mqtt 'password')"
export PYTHONUNBUFFERED=1
bashio::log.info "Savant host ${SAVANT_HOST}, MQTT broker ${MQTT_HOST}:${MQTT_PORT}"
exec python3 /savant.py
