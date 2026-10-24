# QMotion Gen 3 FM

Independent Python implementation of the **QMotion Gen 3 FM** protocol using the **QSYNC433FM** TCP/IP gateway. No dependency on third-party QSync libraries or the original Android app at runtime.

## Status

**v0.1.0 — first hardware-tested Home Assistant release.** Tested on a QSYNC433FM gateway on 24 October 2026:

- Gateway group synchronisation (`16 00`)
- Special Learn preparation and physical-tug pairing
- Pairing completion
- Open and close via position commands (`0` fully open, `100` fully closed)
- Existing handheld remote remains functional after adding the gateway
- Standalone CLI group creation and deletion using a disposable FM group
- HACS installation and Home Assistant cover control (confirmed working with a real blind)

**Still unverified or unsupported:** gateway erase from Python, intermediate-position accuracy, Stop, actual motor-position feedback, and dynamic group discovery without reloading the integration.

## Installation and CLI

Python 3.10+:

```bash
git clone https://github.com/djcult/qmotion-gen3-fm.git
cd qmotion-gen3-fm
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
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
- `custom_components/qmotion_gen3_fm/`: HACS-compatible cover integration using a bundled copy of the same library

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

Delete and erase are available only with `--send` and explicit confirmation.


## Experimental administration (dry-run by default)

The original QSyncAMFM 1.1.3 implementation defines group create/update
(`37 3D 01` plus a 60-byte FM record), delete (`32 02 <reversed page>`),
and gateway erase (`02 00`). Create and delete have been tested with a disposable group; gateway erase has not been live-tested from Python. All three operations default to printing the proposed packet without sending it.

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

The wizard is a **dry-run by default**. Add `--send` to enable real pairing. In live mode it asks you to raise the blind fully, confirms before transmitting Special Learn, pauses while you tug the blind and observe the motor jog, then requires a separate `PAIR` confirmation before sending the completion packet. It never automatically erases groups, resets the motor or modifies
any other group. To abandon, enter anything other than the requested
confirmation. If the learning window expires, restart the sequence.

Pairing is a physical process and must be performed while observing the
blind. Successful TCP transmission does not establish successful RF
delivery; verify normal controls and the existing handheld remote afterwards.

To rehearse the complete interactive pairing workflow **without transmitting
any commands**, use:

```bash
qmotion-admin --host 192.168.1.206 pair homeassistant
```

This reads the group's channel and page address, previews both packet bytes,
and runs all confirmation prompts. Every RF operation is simulated; the
gateway receives only the read-only group sync request.

To perform **live pairing**, explicitly add `--send`:

```bash
qmotion-admin --host 192.168.1.206 pair homeassistant --send
```

Default pairing dry-run performs group discovery and simulates all steps without sending RF commands. No physical tug is needed for rehearsal.

## Home Assistant integration (v0.1.0)

The `custom_components/qmotion_gen3_fm/` folder is structured for HACS.
It bundles a byte-identical copy of this project's own gateway and protocol
implementation under `vendor/`; there are **no runtime dependencies on a
third-party QSync library or an unpublished PyPI package**.

**Install (manual):**

1. Copy `custom_components/qmotion_gen3_fm/` from this repository into
   your HA configuration's `custom_components/` directory.
2. Restart Home Assistant.
3. Open Settings → Devices & services → Add integration → **QMotion Gen 3 FM**.
4. Enter your gateway IP (example: `192.168.1.206`).
5. The integration reads existing gateway groups and exposes one cover per
   group. The group setup/pairing CLI remains separate.

**Install using HACS:** Add
`https://github.com/djcult/qmotion-gen3-fm` as a custom
**Integration** repository in HACS, download it, restart Home Assistant,
and add it under Devices & services. This repository has not yet been
submitted to a curated catalog.

**Features:** Open, Close, and Set Position (0% closed, 100% open in HA).
The integration reverses percentages to QSync's wire convention (0% open,
100% closed). The two end positions were verified with real hardware in
the CLI; intermediate positions are not yet physically verified.
**Stop is intentionally not exposed**, as its command is unverified.

**Important:** FM control is one-way. The gateway does not report actual
motor position or changes from the handheld remote. The integration does
not fabricate a current position: its cover state may show unknown/assumed.
TCP transmission does not mean that the motor received the RF command.
Group additions/deletions are discovered on HA integration reload/restart,
not continuously. Do not pair or erase from inside HA; use `qmotion-admin`.

**Developer:** Keep the bundled library in sync whenever the Python
library changes:

```bash
python scripts/sync_vendor.py
python scripts/sync_vendor.py --check
python -m unittest discover -s tests -v
```

The integration's installation and basic blind control have been **confirmed working in Home Assistant on real hardware**. This is an early release: intermediate percentages, Stop, state reporting, multi-group setups and long-term reliability still need broader testing.

## Compatibility and limitations

- **Verified hardware:** QMotion Gen 3 FM blind using the QSYNC433FM gateway (TCP port 9760). Other QMotion generations, AM gateways, and models are untested.
- **Verified HA functions:** HACS installation and basic control from a Home Assistant cover entity (24 October 2026).
- **FM status:** The system provides one-way RF control. The handheld remote can move the blind without HA knowing; no actual position is reported.
- **Group administration:** Use the standalone CLI, not Home Assistant. Group changes require reloading the integration.
- **Gateway erase:** Implemented with a guarded `--send` option but intentionally not exercised from Python against the working gateway.
- **Experimental:** Preset/percentage positions between the two end limits and the stop command still require validation.

See [CHANGELOG.md](CHANGELOG.md) for release details.
