import asyncio

import savant

DEVICES = [
    {"name": "Kitchen Gang 1", "room": "Kitchen", "type": "WID", "boardname": "2 Button Keypad", "uid": "AABBCC0000010001",
     "address": "01D", "load": [{"id": "1", "name": "Kitchen Lights", "room": "Kitchen", "loadNotWired": "false",
                                 "min": "0", "max": "100"}]},
    {"name": "Closet Switch", "room": "Bedroom 2", "type": "WIS", "uid": "AABBCC0000020001",
     "address": "035", "load": [{"id": "1", "name": "Closet Light", "loadNotWired": "false", "min": "100", "max": "100"}]},
    {"name": "Bedroom Fan", "room": "Bedroom 2", "type": "WIF", "uid": "AABBCC0000030001",
     "address": "024", "load": [{"id": "1", "name": "Bedroom 2 Fan", "loadNotWired": "false", "min": "0", "max": "100"}]},
    {"name": "Patio Gang 1", "room": "Patio", "type": "WID", "uid": "AABBCC0000040001", "address": "004",
     "load": [{"id": "1", "name": "Unknown Outlet", "loadNotWired": "false", "min": "0", "max": "100"},
              {"id": "2", "name": "Spare", "loadNotWired": "true", "min": "0", "max": "100"}]},
]


def test_load_ids_match_the_savant_page():
    assert savant.load_id("01D", 1) == "740"   # Kitchen Gang 1, switched on and off for real
    assert savant.load_id("004", 2) == "101"


def test_loads_become_switches_lights_and_fans():
    loads = {l["name"]: l for l in savant.loads_of(DEVICES)}
    assert loads["Kitchen Lights"]["kind"] == "light"
    assert loads["Closet Light"]["kind"] == "switch"
    assert loads["Bedroom 2 Fan"]["kind"] == "fan"
    assert "Patio Gang 1" in loads           # an "Unknown" load is named after its keypad
    assert "Spare" not in loads              # not wired: left out


def test_discovery_configs():
    loads = {l["name"]: l for l in savant.loads_of(DEVICES)}
    topic, config = savant.discovery(loads["Kitchen Lights"])
    assert topic == "homeassistant/light/savant_aabbcc0000010001_1/config"
    assert config["brightness_scale"] == 100 and config["device"]["suggested_area"] == "Kitchen"
    topic, config = savant.discovery(loads["Closet Light"])
    assert topic.startswith("homeassistant/switch/") and "brightness_scale" not in config


class FakeMQTT:
    def __init__(self):
        self.sent = []

    async def publish(self, topic, payload, retain=False):
        self.sent.append((topic, payload))


class FakeHost:
    def __init__(self):
        self.set = []
        self.read_from = []

    async def set_level(self, load, level):
        self.set.append((load["id"], level))

    async def read(self, address):
        self.read_from.append(address)


async def test_commands_and_states(monkeypatch):
    async def no_wait(seconds):
        return None
    monkeypatch.setattr(asyncio, "sleep", no_wait)
    bridge = savant.Bridge({"savant": {"host": "savant"}})
    bridge.loads = {l["key"]: l for l in savant.loads_of(DEVICES)}
    bridge.by_address = {}
    for l in bridge.loads.values():
        bridge.by_address.setdefault(l["address"].upper(), []).append(l)
    bridge.mqtt, bridge.savant = FakeMQTT(), FakeHost()
    office = "aabbcc0000010001_1"

    await bridge.command(f"savant/{office}/level/set", "40")     # dim to 40%
    await bridge.command(f"savant/{office}/set", "OFF")
    await bridge.publish(bridge.loads[office], 40)
    await bridge.command(f"savant/{office}/set", "ON")           # back to the last level, not 100
    await bridge.command("savant/aabbcc0000020001_1/set", "ON")  # a switch: always 100
    assert bridge.savant.set == [("740", 40), ("740", 0), ("740", 40), ("d40", 100)]
    assert bridge.savant.read_from == ["01D", "01D", "01D", "035"]  # each confirmed by reading back
    assert (f"savant/{office}/state", "ON") in bridge.mqtt.sent and (f"savant/{office}/level", "40") in bridge.mqtt.sent
