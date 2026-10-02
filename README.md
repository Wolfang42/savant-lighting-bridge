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

## Install, step by step

About 10 minutes. You don't need to touch the Savant system, install anything on it, or know
its IP address: the bridge finds it on your network.

**What you need**
- Home Assistant **OS** or **Supervised** (the kind with an **Add-ons** page, called **Apps** in
  newer versions). Running Home Assistant in Docker? See [Without Home Assistant OS](#without-home-assistant-os).
- A **Savant Pro** system (the kind with a Mac mini or similar host) on the same network as
  Home Assistant.

### Step 1: Make sure Home Assistant has an MQTT broker

The bridge hands your Savant devices to Home Assistant through MQTT.

1. Go to **Settings → Add-ons** (or **Apps**) and look for **Mosquitto broker**.
   - Already there and running? Go to Step 2.
2. If not: **Add-on Store** (button at the bottom right) → search **Mosquitto broker** →
   **Install** → **Start**.
3. Go to **Settings → Devices & services**. Home Assistant shows **MQTT** as *Discovered*: click
   **Add** / **Configure**, then **Submit**. MQTT is now listed under your integrations.

### Step 2: Add this repository to Home Assistant

Click this button (it opens the right page in *your* Home Assistant):

[![Add repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FWolfang42%2Fsavant-lighting-bridge)

Or by hand:
1. **Settings → Add-ons** (or **Apps**) **→ Add-on Store**.
2. Click **⋮** (top right) **→ Repositories**.
3. Paste `https://github.com/Wolfang42/savant-lighting-bridge`, click **Add**, then **Close**.

### Step 3: Install the add-on

1. Still in the **Add-on Store**, scroll down to the section **Savant Lighting Bridge**
   (refresh the page if it doesn't show yet).
2. Click **Savant Lighting Bridge → Install**. It takes a minute or two.

### Step 4: Start it and check the log

1. On the add-on's **Info** tab, switch on **Start on boot** and **Watchdog**, then click **Start**.
2. Open the **Log** tab. Within about 10 seconds you should see:

   ```
   [savant] looking for the Savant host on 192.168.1.0/24 ...
   [savant] found the Savant host at 192.168.1.50
   [savant] 77 loads from 79 devices are in Home Assistant
   ```

   (your addresses and numbers will differ). That's it: your Savant lights are in Home
   Assistant. If it says it found no Savant host, see [If it can't find your Savant host](#if-it-cant-find-your-savant-host).

### Step 5: Find your devices and try one

- **Settings → Devices & services → MQTT → devices**: each Savant load is a device, named after
  the load ("Kitchen Can Lights") and placed in its Savant room.
- Switch one on and off from Home Assistant, and flip a wall keypad: Home Assistant should follow
  within a second or two.

What you get:

| Savant | In Home Assistant |
|---|---|
| On/off load | **Switch** |
| Dimmer load | **Light** with brightness (0-100%) |
| Fan speed control | **Fan** with speed as a percentage |

### If it can't find your Savant host

The bridge looks on Home Assistant's own network. If the Savant host is on a different network
(another VLAN or subnet), tell the bridge where it is:

1. Find the Savant host's IP address, for example in your **router's list of connected devices**
   (look for a Mac mini, or a name with "Savant" or "RPM").
2. Optional check: in a web browser, `http://<that-address>/#/tab/devices` should show the
   **"Savant Smart Lighting"** page with your lighting devices.
3. In the add-on's **Configuration** tab, enter the address in **savant_host** (just the address,
   for example `192.168.20.15`, no `http://`), click **Save**, and restart the add-on.

## Troubleshooting

| You see in the log | What to do |
|---|---|
| *no Savant host found on the local network* | See [If it can't find your Savant host](#if-it-cant-find-your-savant-host). If it still can't, your system may not have the lighting service this bridge uses (port 8480). |
| *No MQTT broker found…* | Step 1: install and start **Mosquitto broker**, then start the bridge again. |
| *TimeoutError … trying again* or *ConnectionRefusedError … trying again* | The bridge can't reach the Savant host. If you entered an address, check it. If the host's address changes now and then, give it a fixed address in your router (or leave **savant_host** empty so the bridge finds it). |
| *0 loads from 0 devices* | The host answered but listed no lighting devices. |
| Devices show **Unavailable** | The add-on isn't running: start it (Info tab) and check its log. |
| A device changes in Savant but not in Home Assistant | Wait up to 2 minutes (every level is re-read regularly). If it never updates, restart the add-on and check the log. |

Still stuck? [Report a problem](https://github.com/Wolfang42/savant-lighting-bridge/issues/new/choose)
(the form asks for the add-on's log; remove anything private first), or ask in
[Discussions](https://github.com/Wolfang42/savant-lighting-bridge/discussions).

## Updating

When a new version is out, Home Assistant shows an **Update** button on the add-on. Your
devices, names and automations stay as they are.

## Uninstalling

1. **Stop** the add-on, then **Uninstall** it.
2. **Settings → Devices & services → MQTT → devices**: delete the Savant devices (open each and
   choose **Delete**), or leave them; they stay *Unavailable*.
3. Optionally remove the repository (Add-on Store → **⋮ → Repositories**).

Nothing on the Savant system is changed by installing or removing the bridge.

### Without Home Assistant OS

For Home Assistant in Docker (Container) or Core: run the bridge yourself next to your MQTT
broker. `savant_bridge/savant.py` needs Python 3.11+:

```sh
pip install "websockets>=13" "aiomqtt>=2.3,<3"
SAVANT_HOST=<optional, found if left out> MQTT_HOST=<your broker> MQTT_USER=<user> MQTT_PASSWORD=<password> \
    python3 savant_bridge/savant.py
```

Home Assistant's MQTT integration must be set up with the same broker (with discovery on, the
default). Keep it running as a service (systemd, Docker, ...), so it restarts after a reboot.

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
