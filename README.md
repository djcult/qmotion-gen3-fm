# QMotion Gen 3 FM

Independent Python implementation of the **QMotion Gen 3 FM** protocol using the **QSYNC433FM** TCP/IP gateway. No dependency on third-party QSync libraries or the original Android app at runtime.

## Status

**Early development (v0.1.0 foundation).** Tested on a real gateway at TCP port 9760:

- Gateway group synchronisation (`16 00`)
- Special Learn preparation and physical-tug pairing
- Pairing completion
- Open and close via position commands (`0` fully open, `100` fully closed)
- Existing handheld remote remains functional

Group creation, deletion, factory erase, intermediate positions, stop, motor feedback and Home Assistant integration **are not yet verified or implemented**. They are planned work, not advertised as supported features.

## Installation and CLI

Python 3.10+:

```bash
git clone https://github.com/djcult/qmotion-gen3-fm.git
cd qmotion-gen3-fm
python3 -m pip install -e .
qmotion-admin --host 192.168.1.206 groups
```

Use your gateway's IP address in place of the example.

```bash
qmotion-admin --host 192.168.1.206 position homeassistant 100
qmotion-admin --host 192.168.1.206 position homeassistant 0
qmotion-admin --host 192.168.1.206 pair homeassistant
```

Commands that transmit RF require interactive confirmation. **Pair only when physically present** to observe motor movement and jogs. Pairing is stateful; a wrong completion command could alter the motor's controller assignments. Never erase or reset a motor to troubleshoot basic control.

## Architecture

- `src/qmotion_gen3_fm/protocol.py`: frame and packet encoding
- `src/qmotion_gen3_fm/gateway.py`: TCP transport, group parsing and operations
- `src/qmotion_gen3_fm/cli.py`: standalone administration CLI
- `tests/`: offline protocol tests
- Future: `custom_components/qmotion_gen3_fm/` read/control-only Home Assistant integration, using the same library

The gateway is authoritative for group configuration. Records are distinguished using both channel and page address; duplicate channel values should be investigated, not silently deduplicated.

## Protocol notes

| Operation | Bytes |
|---|---|
| Sync | `16 00` |
| Set position | `38 02 <channel> <0..100>` |
| Special Learn prepare | `38 02 <channel> FA` |
| Complete pairing | `34 03 <page_hi> <page_lo> <channel>` |

The pairing bytes and 0/100 movement commands were verified in October 2026 against the QSYNC433FM. Protocol reference: decompilation of **QSyncAMFM 1.1.3**. This project is an independent implementation, not a fork.

## Tests

```bash
python3 -m unittest discover -s tests
```

## Safety

No gateway erase or group deletion is currently exposed in the CLI. Such operations will be added only after careful protocol validation and with explicit confirmation.
