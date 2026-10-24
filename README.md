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


## Experimental administration (dry-run by default)

The original QSyncAMFM 1.1.3 implementation defines group create/update
(`37 3D 01` plus a 60-byte FM record), delete (`32 02 <reversed page>`),
and gateway erase (`02 00`). These are **not yet live-tested** from this
project. All three operations default to printing the proposed packet without
sending it.

```bash
qmotion-admin --host 192.168.1.206 create spare
qmotion-admin --host 192.168.1.206 delete spare
qmotion-admin --host 192.168.1.206 erase
```

Creating the **first** group on an empty gateway requires its independently
verified MAC address because no existing group record supplies it:

```bash
qmotion-admin --host 192.168.1.206 create spare --mac AA:BB:CC:DD:EE:FF
```

This is an illustrative MAC only; use your gateway's actual MAC.

When physically present and ready to test with a disposable group, add
`--send`. The CLI then requires a typed confirmation. Erase requires
typing `ERASE <gateway-ip>` and removes **all gateway group and scene data**;
it may leave RF assignments stored in the motors. Never use it casually.
Deletion removes a **gateway group record**, not necessarily the shade's
learned association; removing a blind from a group is a separate pairing
operation. Re-read `groups` after each test.

Do not test delete or erase on a working, sole group. Test creation of a
disposable group first and verify its returned page address through sync.

## Guided shade pairing

A working group must already exist on the gateway. Pairing takes its
**name** and reads the channel and page address directly from gateway sync:

```bash
qmotion-admin --host 192.168.1.206 pair homeassistant
```

The wizard asks you to raise the blind fully, confirms before transmitting
Special Learn, pauses while you tug the blind and observe the motor jog,
then requires a separate `PAIR` confirmation before sending the completion
packet. It never automatically erases groups, resets the motor or modifies
any other group. To abandon, enter anything other than the requested
confirmation. If the learning window expires, restart the sequence.

Pairing is a physical process and must be performed while observing the
blind. Successful TCP transmission does not establish successful RF
delivery; verify normal controls and the existing handheld remote afterwards.
