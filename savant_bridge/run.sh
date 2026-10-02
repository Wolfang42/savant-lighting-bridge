#!/usr/bin/with-contenv bashio
# MQTT login comes from Home Assistant's Mosquitto add-on (services: mqtt:need), no password to keep.
export SAVANT_HOST=""
if bashio::config.has_value 'savant_host'; then
    export SAVANT_HOST="$(bashio::config 'savant_host')"
else
    # No address given: the bridge looks for the Savant host on Home Assistant's own network(s).
    export SAVANT_NETWORKS="$(bashio::network.ipv4_address | tr '\n' ',')"
    bashio::log.info "No savant_host set: looking for the Savant host on ${SAVANT_NETWORKS}"
fi
if ! bashio::services.available mqtt; then
    bashio::exit.nok "No MQTT broker found. Install and start the Mosquitto broker add-on first (see the install guide)."
fi
export MQTT_HOST="$(bashio::services mqtt 'host')"
export MQTT_PORT="$(bashio::services mqtt 'port')"
export MQTT_USER="$(bashio::services mqtt 'username')"
export MQTT_PASSWORD="$(bashio::services mqtt 'password')"
export PYTHONUNBUFFERED=1
bashio::log.info "Savant host ${SAVANT_HOST:-(to be found)}, MQTT broker ${MQTT_HOST}:${MQTT_PORT}"
exec python3 /savant.py
