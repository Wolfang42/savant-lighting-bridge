# Savant Lighting Bridge

Brings the lighting of a **Savant Pro** system (the kind with a Mac mini host) into Home
Assistant: every switch, dimmer and fan load becomes an ordinary Home Assistant entity.

## Before you start

- The **Mosquitto broker** add-on (or another MQTT broker set up in Home Assistant's MQTT
  integration). This add-on asks Home Assistant for the MQTT login itself.
- Your Savant host's **IP address**. If your system has the "Savant Smart Lighting" web page
  (`http://<host>/#/tab/devices`), this add-on will work: it talks to the host the same way.

## Configuration

| Option | |
|---|---|
| `savant_host` | The Savant host's IP address or name, e.g. `192.168.1.50` |

Start the add-on and look at its **Log**: it says how many loads it found. The entities
appear under the MQTT integration, one device per load, in the Savant room.

## Good to know

- **Alexa / Google**: if Home Assistant is set to expose new entities to them, it will
  expose all of these at once. Consider turning that off before the first start.
- On/off loads become **switches**, dimmable loads **lights** (brightness 0-100%), fan
  speed controls **fans** (speed as a percentage). Scenes aren't brought over (yet).
- Turning a light on without a brightness returns it to its last level.
