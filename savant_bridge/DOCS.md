# Savant Lighting Bridge

Brings the lighting of a **Savant Pro** system (the kind with a Mac mini host) into Home
Assistant: every switch, dimmer and fan load becomes an ordinary Home Assistant entity.

## Before you start

- The **Mosquitto broker** add-on (or another MQTT broker set up in Home Assistant's MQTT
  integration). This add-on asks Home Assistant for the MQTT login itself.
- Nothing else: the add-on finds your Savant host on the network by itself.

## Configuration

| Option | |
|---|---|
| `savant_host` | Optional. Leave it empty and the bridge finds your Savant host on the network. Only needed if the host is on another network: its IP address, e.g. `192.168.20.15` (no `http://`). |

Start the add-on and look at its **Log**: it says how many loads it found. The entities
appear under the MQTT integration, one device per load, in the Savant room.

## Good to know

- On/off loads become **switches**, dimmable loads **lights** (brightness 0-100%), fan
  speed controls **fans** (speed as a percentage). Scenes aren't brought over (yet).
- Turning a light on without a brightness returns it to its last level.

## Step-by-step guide and troubleshooting

The full install guide (with a compatibility check and the meaning of every log message) is
in the README: https://github.com/Wolfang42/savant-lighting-bridge#install-step-by-step
