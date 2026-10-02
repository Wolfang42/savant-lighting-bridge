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

About 10 minutes. You don't need to touch the Savant system or install anything on it.

**What you need**
- Home Assistant **OS** or **Supervised** (the kind with an **Add-ons** page, called **Apps** in
  newer versions). Running Home Assistant in Docker? See [Without Home Assistant OS](#without-home-assistant-os).
- A **Savant Pro** system (the kind with a Mac mini or similar host) on the same network.

### Step 1: Check that your Savant system will work (1 minute)

1. Find your **Savant host's IP address**. Any of these works:
   - your router's list of connected devices (look for a Mac mini, or a name with "Savant" or "RPM");
   - if you know the host's name, try `http://<name>.local` in a browser.
2. In a web browser on the same network, open `http://<savant-host-ip>/#/tab/devices`
   (for example `http://192.168.1.50/#/tab/devices`).
3. **You should see "Savant Smart Lighting"** with a list of your lighting devices.
   - ✅ You do: this bridge will work. Write the IP address down and carry on.
   - ❌ The page doesn't load: check the IP address. If it's right and there's still no lighting
     page, your system doesn't have the lighting web app this bridge relies on, and it won't work.

### Step 2: Make sure Home Assistant has an MQTT broker

The bridge hands your Savant devices to Home Assistant through MQTT.

1. Go to **Settings → Add-ons** (or **Apps**) and look for **Mosquitto broker**.
   - Already there and running? Go to Step 3.
2. If not: **Add-on Store** (button at the bottom right) → search **Mosquitto broker** →
   **Install** → **Start**.
3. Go to **Settings → Devices & services**. Home Assistant shows **MQTT** as *Discovered*: click
   **Add** / **Configure**, then **Submit**. MQTT is now listed under your integrations.

### Step 3 (recommended): Stop Home Assistant announcing new devices to Alexa or Google

The bridge can add 50+ devices at once. If Home Assistant automatically shares new devices with
Alexa or Google Assistant, they will all be announced there in one go.

- Go to **Settings → Voice assistants → Expose** tab and open the settings for **Amazon Alexa**
  and **Google Assistant** (the **⚙** / **⋮** at the top). Turn off **"Expose new entities"**.
- No Alexa or Google connected to Home Assistant? Skip this step.

You can still share individual Savant devices with them later, one by one.

### Step 4: Add this repository to Home Assistant

Click this button (it opens the right page in *your* Home Assistant):

[![Add repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FWolfang42%2Fsavant-lighting-bridge)

Or by hand:
1. **Settings → Add-ons** (or **Apps**) **→ Add-on Store**.
2. Click **⋮** (top right) **→ Repositories**.
3. Paste `https://github.com/Wolfang42/savant-lighting-bridge`, click **Add**, then **Close**.

### Step 5: Install the add-on

1. Still in the **Add-on Store**, scroll down to the section **Savant Lighting Bridge**
   (refresh the page if it doesn't show yet).
2. Click **Savant Lighting Bridge → Install**. It takes a minute or two.

### Step 6: Tell it where your Savant host is

1. Open the **Configuration** tab of the add-on.
2. In **savant_host**, type the IP address from Step 1 (for example `192.168.1.50`).
3. Click **Save**.

### Step 7: Start it and check the log

1. Back on the **Info** tab, switch on **Start on boot** and **Watchdog**, then click **Start**.
2. Open the **Log** tab. After a few seconds you should see a line like:

   ```
   [savant] 77 loads from 79 devices are in Home Assistant
   ```

   That's it: your Savant lights are in Home Assistant. If you see something else, look at
   [Troubleshooting](#troubleshooting).

### Step 8: Find your devices and try one

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

## Troubleshooting

| You see | What to do |
|---|---|
| *No Savant host set…* | Step 6: enter the IP address in **savant_host**, Save, Start. |
| *No MQTT broker found…* | Step 2: install and start **Mosquitto broker**, then start the bridge again. |
| *TimeoutError … trying again* or *ConnectionRefusedError … trying again* | The bridge can't reach the Savant host. Check the IP (Step 1). If the host's IP changes now and then, give it a fixed address in your router. |
| *0 loads from 0 devices* | The host answered but listed no lighting devices. Check the lighting page from Step 1 shows your devices. |
| Devices show **Unavailable** | The add-on isn't running: start it (Info tab) and check its log. |
| A device changes in Savant but not in Home Assistant | Wait up to 2 minutes (every level is re-read regularly). If it never updates, restart the add-on and check the log. |
| Too many devices announced to Alexa/Google | See Step 3, then remove them there with "Alexa, discover devices" or in the Alexa/Google app. |

Still stuck? Open an issue with the add-on's log (remove anything private first).

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
SAVANT_HOST=192.168.1.50 MQTT_HOST=<your broker> MQTT_USER=<user> MQTT_PASSWORD=<password> \
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
