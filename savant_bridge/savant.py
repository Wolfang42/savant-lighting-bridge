"""Savant lighting in Home Assistant, through MQTT (until the Savant system is retired).

A Savant Pro host (e.g. a Mac mini) has no Home Assistant support,
but its own lighting web page talks to it over a local WebSocket, and so does this:

    ws://<host>:8480/, subprotocol "savant_protocol" (without it the host ignores you)
    session/devicePresent             -> session/deviceRecognized   (no password)
    lighting/config/device/get        -> lighting/config/device/list (devices and their loads)
    state/module/<address>/get        -> "module.<ADDR>" = "L1,L2,...,L8"  (levels 0-100)
    state/register {"state":"module"} -> state/update pushes when anything changes
    state/set {"state":"load.<id>","value":"100%"}, id = hex(address << 6 | load - 1)

Each load (a light, outlet or fan on a Savant keypad) becomes a Home Assistant entity
through MQTT discovery: on/off switches as switches, dimmers as dimmable lights, fan
controls as fans. Wall keypads and the Savant app show up straight away (the host pushes
changes), and everything is re-read every few minutes in case a push was missed.

As a Home Assistant add-on, run.sh fills in the settings. To run it anywhere else:

    SAVANT_HOST=192.0.2.10 MQTT_HOST=homeassistant.local MQTT_USER=... MQTT_PASSWORD=... \
        python3 savant.py
"""

import asyncio
import json
import os
import re

PREFIX = "savant"            # MQTT topics: savant/<uid>_<load>/...
DISCOVERY = "homeassistant"  # Home Assistant's MQTT discovery prefix
AVAILABILITY = f"{PREFIX}/bridge/status"
RECHECK_SECONDS = 120        # re-read every level this often (a push missed, or the host gone)
APP = "Savant Smart Lighting (build.rev:7.0 Dev)"


def load_id(address: str, load: int) -> str:
    """The id the host uses for a load: address 01D, load 1 -> "740"."""
    return format((int(address, 16) << 6) | ((load - 1) & 0x0F), "x")


def parse(text: str) -> dict | None:
    """The host's JSON (it sometimes has raw line breaks inside strings)."""
    try:
        return json.loads(text)
    except ValueError:
        try:
            return json.loads(re.sub(r"\r?\n|\r", "", text))
        except ValueError:
            return None


def kind_of(device: dict, load: dict) -> str:
    """ "switch" (on/off only), "fan", or "light" (dimmable)."""
    if device.get("type") == "WIF":
        return "fan"
    if str(load.get("min")) == str(load.get("max")) == "100":
        return "switch"
    return "light"


def loads_of(devices: list[dict]) -> list[dict]:
    """Every wired load, with what Home Assistant needs to know about it."""
    found = []
    for device in devices:
        for load in device.get("load") or []:
            if str(load.get("loadNotWired")).lower() == "true":
                continue
            number = int(load["id"])
            name = (load.get("name") or "").strip()
            if not name or name.lower().startswith("unknown"):
                name = device.get("name", f"Savant {device['address']}")
            found.append({
                "key": f"{device['uid']}_{number}".lower(),
                "uid": device["uid"], "address": device["address"], "load": number,
                "id": load_id(device["address"], number), "name": name,
                "room": load.get("room") or device.get("room") or "",
                "kind": kind_of(device, load),
                "device": {"identifiers": [f"savant_{device['uid']}"], "name": device.get("name"),
                           "manufacturer": "Savant", "model": device.get("boardname") or device.get("type"),
                           "suggested_area": device.get("room") or None},
            })
    return found


def discovery(load: dict) -> tuple[str, dict]:
    """Home Assistant's discovery topic and config for one load."""
    base = f"{PREFIX}/{load['key']}"
    config = {
        "name": None,  # the entity is named after its device...
        "unique_id": f"savant_{load['key']}",
        "object_id": f"savant_{re.sub(r'[^a-z0-9]+', '_', load['name'].lower()).strip('_')}",
        "availability_topic": AVAILABILITY,
        "command_topic": f"{base}/set",
        "state_topic": f"{base}/state",
        "device": {**load["device"], "name": load["name"]},  # ...which is named after the load
    }
    if load["kind"] == "light":
        config.update({"brightness_command_topic": f"{base}/level/set", "brightness_state_topic": f"{base}/level",
                       "brightness_scale": 100, "on_command_type": "brightness"})
    elif load["kind"] == "fan":
        config.update({"percentage_command_topic": f"{base}/level/set", "percentage_state_topic": f"{base}/level",
                       "speed_range_min": 1, "speed_range_max": 100})
    return f"{DISCOVERY}/{load['kind']}/savant_{load['key']}/config", config


async def is_savant(address: str, timeout: float = 3) -> bool:
    """Whether a Savant lighting host answers at this address (port 8480, savant_protocol)."""
    import websockets

    try:
        async with websockets.connect(f"ws://{address}:8480/", subprotocols=["savant_protocol"],
                                      origin=f"http://{address}", compression=None, open_timeout=timeout,
                                      ping_interval=None) as ws:
            await ws.send(json.dumps({"messages": [{"protocolVersion": "0.1", "device": {
                "name": "linux", "version": None, "app": APP, "ip": address, "model": "savant-bridge"}}],
                "URI": "session/devicePresent"}))
            while True:
                reply = parse(await asyncio.wait_for(ws.recv(), timeout))
                if reply and reply.get("URI") == "session/deviceRecognized":
                    return True
    except Exception:
        return False


def local_networks() -> list[str]:
    """This machine's local network(s) as "a.b.c" prefixes (/24), from SAVANT_NETWORKS or the
    address it uses to reach the outside."""
    import socket

    given = [n.strip() for n in os.environ.get("SAVANT_NETWORKS", "").split(",") if n.strip()]
    found = []
    for network in given:
        address = network.split("/")[0]
        if address.count(".") == 3:
            found.append(address.rsplit(".", 1)[0])
    if not found:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            try:
                probe.connect(("192.0.2.1", 9))  # no packet is sent; it just picks the local address
                found.append(probe.getsockname()[0].rsplit(".", 1)[0])
            except OSError:
                pass
    return list(dict.fromkeys(found))


async def find_savant_host() -> str | None:
    """Look for the Savant lighting host on the local network(s)."""
    for prefix in local_networks():
        print(f"[savant] looking for the Savant host on {prefix}.0/24 ...", flush=True)
        candidates = [f"{prefix}.{n}" for n in range(1, 255)]
        open_ports = await asyncio.gather(*(_port_open(a) for a in candidates))
        for address in [a for a, ok in zip(candidates, open_ports) if ok]:
            # the host stays busy for a moment after the scan's knock on its port
            for attempt in range(4):
                await asyncio.sleep(2)
                if await is_savant(address):
                    return address
    return None


async def _port_open(address: str) -> bool:
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(address, 8480), 1.5)
        writer.close()
        return True
    except Exception:
        return False


class SavantHost:
    """One WebSocket to the Savant host: requests wait for their reply; pushes go to on_levels."""

    def __init__(self, host: str, on_levels):
        self.host = host
        self.on_levels = on_levels  # (address, [levels]) for every module state seen
        self.ws = None
        self.waiting: dict[str, asyncio.Future] = {}

    async def connect(self) -> None:
        import websockets

        self.ws = await websockets.connect(f"ws://{self.host}:8480/", subprotocols=["savant_protocol"],
                                           origin=f"http://{self.host}", compression=None,
                                           open_timeout=10, max_size=2 ** 24,
                                           ping_interval=None)  # the host never answers pings
        self.reader = asyncio.create_task(self._read())
        await self.request({"messages": [{"protocolVersion": "0.1", "device": {
            "name": "linux", "version": None, "app": APP, "ip": self.host, "model": "savant-bridge"}}],
            "URI": "session/devicePresent"}, "session/deviceRecognized")
        await self.ws.send(json.dumps({"messages": [{"state": "module"}], "URI": "state/register"}))

    async def _read(self) -> None:
        async for text in self.ws:
            message = parse(text)
            if not message:
                continue
            uri = message.get("URI", "")
            for item in message.get("messages") or message.get("message") or []:
                state = str(item.get("state", "")) if isinstance(item, dict) else ""
                if state.startswith("module."):
                    self.on_levels(state.split(".", 1)[1], [int(v) if v.lstrip("-").isdigit() else -1
                                                            for v in str(item.get("value", "")).split(",")])
            future = self.waiting.pop(uri, None)
            if future and not future.done():
                future.set_result(message)
        for future in self.waiting.values():  # the host went away: nobody waits forever
            if not future.done():
                future.set_exception(ConnectionError("the Savant host closed the connection"))

    async def request(self, message: dict, reply_uri: str, timeout: float = 10) -> dict:
        future = asyncio.get_running_loop().create_future()
        self.waiting[reply_uri] = future
        await self.ws.send(json.dumps(message))
        return await asyncio.wait_for(future, timeout)

    async def devices(self) -> list[dict]:
        reply = await self.request({"messages": [{}], "URI": "lighting/config/device/get"},
                                   "lighting/config/device/list", 20)
        return reply.get("messages") or []

    async def read(self, address: str) -> None:
        """Ask for a device's levels (they arrive through on_levels)."""
        uri = f"state/module/{address}/get"
        await self.request({"messages": [{}], "URI": uri}, uri)

    async def set_level(self, load: dict, level: int) -> None:
        await self.ws.send(json.dumps({"messages": [{"state": f"load.{load['id']}", "value": f"{level}%"}],
                                       "URI": "state/set"}))

    async def close(self) -> None:
        if self.ws:
            await self.ws.close()


class Bridge:
    def __init__(self, config: dict):
        cfg = config.get("savant", {})
        self.host = cfg.get("host") or None  # None: found on the network
        self.broker = cfg.get("mqtt_host") or "homeassistant.local"
        self.port = int(cfg.get("mqtt_port") or 1883)
        self.loads: dict[str, dict] = {}
        self.by_address: dict[str, list[dict]] = {}
        self.last: dict[str, int] = {}      # load key -> level last published
        self.on_level: dict[str, int] = {}  # load key -> level to go back to on "ON"
        self.mqtt = None
        self.savant = None

    def levels_seen(self, address: str, levels: list[int]) -> None:
        for load in self.by_address.get(address.upper(), []):
            if load["load"] - 1 < len(levels) and levels[load["load"] - 1] >= 0:
                asyncio.get_running_loop().create_task(self.publish(load, levels[load["load"] - 1]))

    async def publish(self, load: dict, level: int) -> None:
        if not self.mqtt or self.last.get(load["key"]) == level:
            return
        self.last[load["key"]] = level
        if level > 0:
            self.on_level[load["key"]] = level
        base = f"{PREFIX}/{load['key']}"
        await self.mqtt.publish(f"{base}/state", "ON" if level > 0 else "OFF", retain=True)
        if load["kind"] in ("light", "fan") and level > 0:
            await self.mqtt.publish(f"{base}/level", str(level), retain=True)

    async def command(self, topic: str, payload: str) -> None:
        parts = topic.split("/")  # savant/<key>/set or savant/<key>/level/set
        load = self.loads.get(parts[1]) if len(parts) >= 3 else None
        if not load:
            return
        if parts[2] == "level":
            level = max(0, min(100, int(float(payload))))
        else:
            level = self.on_level.get(load["key"], 100) if payload.upper() == "ON" else 0
            if load["kind"] == "switch" and level:
                level = 100
        print(f"[savant] {load['name']} ({load['room']}) -> {level}%", flush=True)
        await self.savant.set_level(load, level)
        await asyncio.sleep(0.7)
        await self.savant.read(load["address"])  # confirm what actually happened

    async def run(self) -> None:
        import aiomqtt

        delay = 5
        while True:
            try:
                await self._run_once(aiomqtt)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"[savant] {type(e).__name__}: {e}; trying again in {delay} s", flush=True)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 120)
            else:
                delay = 5

    async def _run_once(self, aiomqtt) -> None:
        if not self.host:
            self.host = await find_savant_host()
            if not self.host:
                raise ConnectionError("no Savant host found on the local network. If it's on another network, "
                                      "enter its IP address in savant_host")
            print(f"[savant] found the Savant host at {self.host}", flush=True)
        self.savant = SavantHost(self.host, self.levels_seen)
        await self.savant.connect()
        devices = await self.savant.devices()
        self.loads = {load["key"]: load for load in loads_of(devices)}
        self.by_address = {}
        for load in self.loads.values():
            self.by_address.setdefault(load["address"].upper(), []).append(load)
        self.last = {}
        will = aiomqtt.Will(AVAILABILITY, "offline", retain=True)
        async with aiomqtt.Client(self.broker, port=self.port, username=os.environ.get("MQTT_USER"),
                                  password=os.environ.get("MQTT_PASSWORD"), will=will,
                                  identifier="savant-bridge") as mqtt:
            self.mqtt = mqtt
            for load in self.loads.values():
                topic, config = discovery(load)
                await mqtt.publish(topic, json.dumps(config), retain=True)
            await mqtt.publish(AVAILABILITY, "online", retain=True)
            await mqtt.subscribe(f"{PREFIX}/+/set")
            await mqtt.subscribe(f"{PREFIX}/+/level/set")
            print(f"[savant] {len(self.loads)} loads from {len(devices)} devices are in Home Assistant", flush=True)

            async def listen():
                async for message in mqtt.messages:
                    try:
                        await self.command(str(message.topic), message.payload.decode())
                    except Exception as e:
                        print(f"[savant] couldn't do {message.topic} {message.payload!r}: {e}", flush=True)

            tasks = [asyncio.create_task(listen()), asyncio.create_task(self._recheck()), self.savant.reader]
            try:
                done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    task.result()  # whatever ended it, raised here
                raise ConnectionError("the Savant host closed the connection")
            finally:
                for task in tasks:
                    task.cancel()
                self.mqtt = None
                await self.savant.close()

    async def _recheck(self) -> None:
        while True:
            for address in list(self.by_address):
                await self.savant.read(address)
            await asyncio.sleep(RECHECK_SECONDS)


if __name__ == "__main__":  # as a Home Assistant add-on (addons/savant_bridge): settings from run.sh
    asyncio.run(Bridge({"savant": {"host": os.environ.get("SAVANT_HOST") or None,
                                   "mqtt_host": os.environ.get("MQTT_HOST"),
                                   "mqtt_port": os.environ.get("MQTT_PORT")}}).run())
