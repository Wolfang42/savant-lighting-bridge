#!/usr/bin/with-contenv bashio
# MQTT login comes from Home Assistant's Mosquitto add-on (services: mqtt:need), no password to keep.
export SAVANT_HOST="$(bashio::config 'savant_host')"
if [ -z "${SAVANT_HOST}" ]; then
    bashio::exit.nok "No Savant host set. Open this add-on's Configuration tab, enter your Savant host's IP address in savant_host, save, and start again."
fi
if ! bashio::services.available mqtt; then
    bashio::exit.nok "No MQTT broker found. Install and start the Mosquitto broker add-on first (see the install guide)."
fi
export MQTT_HOST="$(bashio::services mqtt 'host')"
export MQTT_PORT="$(bashio::services mqtt 'port')"
export MQTT_USER="$(bashio::services mqtt 'username')"
export MQTT_PASSWORD="$(bashio::services mqtt 'password')"
export PYTHONUNBUFFERED=1
bashio::log.info "Savant host ${SAVANT_HOST}, MQTT broker ${MQTT_HOST}:${MQTT_PORT}"
exec python3 /savant.py
