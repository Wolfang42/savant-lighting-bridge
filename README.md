# Savant Lighting Bridge for Home Assistant

Control the lighting of a **Savant Pro** system from Home Assistant: switches, dimmers and
fans, two-way and live. Savant has no Home Assistant integration and older systems no
longer get updates, but the lighting controller already speaks a simple local protocol (its
own lighting web page uses it). This bridge speaks it too, and publishes every load to Home
Assistant through MQTT discovery.

- **Two-way**: switch and dim from Home Assistant; changes from wall keypads and the Savant
  app show up immediately.
- **Local**: no cloud, no Savant account, nothing installed on the Savant host.
- **Named and placed**: entities are named after the Savant load and put in its Savant room.
- Commands are **confirmed** by reading the level back from the host.

> Unofficial. Not affiliated with or endorsed by Savant Systems. Built and tested on one
> Savant Pro system (Mac mini host, 2017 installation, lighting controller type "NUC").
> Other versions may differ; issues and reports welcome.

## Install (Home Assistant OS / Supervised)

1. You need an MQTT broker in Home Assistant (the **Mosquitto broker** add-on is easiest).
2. **Settings → Add-ons → Add-on Store → ⋮ → Repositories**, add
   `https://github.com/Wolfang42/savant-lighting-bridge`.
3. Install **Savant Lighting Bridge**, set `savant_host` to your Savant host's IP address,
   and start it. The log says how many loads it found.

**Tip:** if Home Assistant exposes new entities to Alexa or Google automatically, turn that
off first, or every Savant load will be announced to them at once.

### Without Home Assistant OS

`savant_bridge/savant.py` runs anywhere with Python 3.11+:

```sh
pip install "websockets>=13" "aiomqtt>=2.3,<3"
SAVANT_HOST=192.0.2.10 MQTT_HOST=homeassistant.local MQTT_USER=... MQTT_PASSWORD=... \
    python3 savant_bridge/savant.py
```

## How it works

The Savant host serves a lighting web app on port 80 that talks to the lighting controller
over a WebSocket on port **8480**. The protocol, as read from that app:

| | |
|---|---|
| Connect | `ws://<host>:8480/` with subprotocol **`savant_protocol`** (without it the host silently ignores you) |
| Hello | `{"messages":[{"protocolVersion":"0.1","device":{...}}],"URI":"session/devicePresent"}` → `session/deviceRecognized` |
| Devices | `{"messages":[{}],"URI":"lighting/config/device/get"}` → `lighting/config/device/list` (name, room, type, hex `address`, `load` list with names) |
| Read levels | `{"messages":[{}],"URI":"state/module/<address>/get"}` → state `module.<ADDR>` = `"L1,L2,…,L8"` (0-100) |
| Live changes | `{"messages":[{"state":"module"}],"URI":"state/register"}` → `state/update` messages |
| Set a level | `{"messages":[{"state":"load.<id>","value":"75%"}],"URI":"state/set"}`, with `id = hex(int(address,16) << 6 \| (load - 1))` |

Device types seen: `WID` (dimmer), `WIS` (switch), `WIF` (fan speed control), `WIK`
(keypad with rotary dial). A load whose `min` and `max` are both 100 is on/off only.

Two quirks: the host never answers WebSocket pings (so they're off; the bridge notices a
dead connection through its regular re-reads instead), and its JSON sometimes contains raw
line breaks inside strings.

## MQTT topics

- Discovery: `homeassistant/<switch|light|fan>/savant_<uid>_<load>/config` (retained)
- State: `savant/<uid>_<load>/state` (`ON`/`OFF`), level: `savant/<uid>_<load>/level` (0-100)
- Commands: `savant/<uid>_<load>/set`, `savant/<uid>_<load>/level/set`
- Availability: `savant/bridge/status` (`online`/`offline`)

## Development

```sh
pip install pytest pytest-asyncio websockets aiomqtt
pytest
```

## Not yet

Savant scenes, keypad button presses as Home Assistant events, and shades/other non-lighting
devices.

## License

MIT. See [LICENSE](LICENSE).
