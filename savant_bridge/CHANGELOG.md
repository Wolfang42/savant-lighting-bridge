# Changelog

## 1.1.0

- Finds the Savant host on the network by itself: `savant_host` is now optional.

## 1.0.1

- Clear messages in the log when no Savant host is set or no MQTT broker is found.
- Step-by-step install guide and troubleshooting in the README.

## 1.0.0

- First release: every wired load on a Savant Pro lighting system appears in Home
  Assistant through MQTT discovery (switches, dimmable lights, fans), named after the
  load and placed in its Savant room. Changes from keypads and the Savant app show up
  immediately; every level is also re-read every two minutes.
