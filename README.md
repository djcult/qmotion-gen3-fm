# QMotion Gen 3 FM

![QMotion QSYNC433FM gateway showing underside model label, Ethernet/power connections and antenna](docs/images/s-l1600.webp)

*QMotion QSYNC433FM gateway (underside view). Photograph from [eBay listing 880011062879](https://www.ebay.co.uk/itm/880011062879); reproduced for hardware identification.*

Independent, local Python support for **QMotion Gen 3 FM blinds** through a **QSYNC433FM** Ethernet gateway. Includes a standalone administration CLI and an **optional** Home Assistant integration. No dependency on the original Android app or third-party QSync libraries at runtime.

**Initial hardware-tested release:** Gateway group discovery, group creation/deletion, physical-tug pairing and open/close have been tested on real hardware. HACS installation and basic Home Assistant blind control have also been confirmed working.

## 1. Initial setup — administration CLI

Use the CLI to configure the gateway and pair your blinds **before** installing Home Assistant. You can use it on any computer that can reach the gateway over TCP port `9760`. Home Assistant is not required.

### Prerequisites: install the CLI

- QSYNC433FM gateway powered, connected to the same network, with a known IP address.
- Python 3.10 or later, Git and a working Python virtual environment.
- The original handheld remote, and physical access to the blind for pairing.

```bash
git clone https://github.com/djcult/qmotion-gen3-fm.git
cd qmotion-gen3-fm
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

In the examples below, replace `192.168.1.206` with **your gateway IP**, and `livingroom` with **your chosen group name**. The addresses and names are examples, not universal defaults.

### Step 1 — inspect or (optionally) reset the gateway

First list the existing groups:

```bash
qmotion-admin --host 192.168.1.206 groups
```

**You do not need to reset a new or correctly configured gateway.** If the gateway has old, orphaned or conflicting groups and you intentionally want to start from scratch, you can *preview* the erase operation:

```bash
qmotion-admin --host 192.168.1.206 erase
```

To actually erase all gateway groups and scenes:

```bash
qmotion-admin --host 192.168.1.206 erase --send
```

You must type `ERASE 192.168.1.206` when prompted. **Warning:** This is destructive to gateway configuration; learned motor associations may persist, and existing blinds may need re-pairing. The Python erase command is derived from the original app but **has not yet been hardware-tested**. Don't run it merely to check that the command works.

If you do erase, run `groups` again to confirm the gateway reports no groups.

### Step 2 — create a group

A group represents the gateway address that one or more blinds will learn. First preview creation:

```bash
qmotion-admin --host 192.168.1.206 create livingroom
```

Then create it:

```bash
qmotion-admin --host 192.168.1.206 create livingroom --send
qmotion-admin --host 192.168.1.206 groups
```

The CLI chooses an unused FM channel and the gateway allocates its page address. Creation is dry-run by default; `--send` also requires typed confirmation.

**Important for an empty gateway:** The CLI cannot currently obtain the gateway MAC from group records if no groups exist. Supply your independently verified **gateway MAC**, for example:

```bash
qmotion-admin --host 192.168.1.206 create livingroom --mac AA:BB:CC:DD:EE:FF --send
```

`AA:BB:CC:DD:EE:FF` is a placeholder — **do not use it as an actual address**. If you cannot verify the MAC, do not guess; the first-group setup is not yet fully automated.

### Step 3 — pair each blind to its group

The CLI looks up the channel and page address automatically using the group name. You don't need to type raw packets.

Rehearse the workflow safely (**dry-run by default**):

```bash
qmotion-admin --host 192.168.1.206 pair livingroom
```

For actual pairing, stand beside the blind and run:

```bash
qmotion-admin --host 192.168.1.206 pair livingroom --send
```

Follow the interactive prompts:

1. Raise the blind fully using its **existing handheld remote**; type `READY`.
2. Confirm `SEND` to transmit the **Special Learn** preparation command. The blind should lower toward its programming position.
3. Once movement stops, gently tug the blind's accessible hembar or operating cord. Watch for a brief **jog**; enter `JOG` only if you observed one.
4. Confirm `PAIR` to send the final pairing packet. The blind should jog again and return to its upper limit.
5. Check that the handheld remote **still works**.

If no jog occurs, **do not confirm the final pairing command**. Cancel and investigate; if the learning window times out, restart the pairing sequence. To associate multiple blinds with the same group, repeat the guided process for each blind. Do not reset the motor as a troubleshooting shortcut.

### Step 4 — test movement

When the blind has completed pairing, test ordinary movement:

```bash
# Fully close (QSync 100%)
qmotion-admin --host 192.168.1.206 position livingroom 100

# Fully open (QSync 0%)
qmotion-admin --host 192.168.1.206 position livingroom 0
```

The CLI requests confirmation before sending movement commands. Observe the blind; a successful TCP send does not guarantee RF delivery. Intermediate percentage positions are implemented but not yet physically validated.

**Optional group maintenance:**

```bash
# Preview deletion: no command transmitted
qmotion-admin --host 192.168.1.206 delete livingroom

# Actually delete the gateway group, after confirmation
qmotion-admin --host 192.168.1.206 delete livingroom --send
```

Deleting a gateway group does **not necessarily remove its identity from a blind's motor**. Create and delete were validated with a disposable group. Avoid deleting a group that controls a working blind.

## 2. Home Assistant installation — optional (HACS)

Once your gateway and blinds work through the admin CLI, you can add them to Home Assistant. This integration handles **everyday cover control only**; use `qmotion-admin` for creating, deleting and pairing groups.

### Install with HACS

1. Open **HACS** in Home Assistant and add `https://github.com/djcult/qmotion-gen3-fm` as a **custom repository**, category **Integration**.
2. Download **QMotion Gen 3 FM** from HACS.
3. Restart Home Assistant.
4. Open **Settings → Devices & services → Add integration**.
5. Search for **QMotion Gen 3 FM** and enter your gateway IP address.
6. Home Assistant reads the configured gateway groups and creates a **cover entity** for each one. Use the cover's Open and Close controls to test.

This repository is available as a HACS custom repository; it has not been submitted to the default curated catalog.

**Manual alternative:** Copy `custom_components/qmotion_gen3_fm/` into your Home Assistant configuration's `custom_components/` directory, restart Home Assistant, then follow steps 4–6 above.

### Home Assistant behaviour and limitations

- Supports **Open**, **Close**, and **Set Position**. Home Assistant uses **0% closed / 100% open**; the integration converts this to QSync's opposite wire convention.
- **Assumed last-commanded position:** On startup HA uses the position stored in the gateway's FM group record; after HA sends a movement command it shows that requested position (0% closed, 100% open). This is **not measured motor position**, and the cover retains `assumed_state=True`. The `position_source` attribute distinguishes `gateway_record` from `home_assistant_command`.
- **One-way RF:** The motor does not report actual position. The handheld remote talks directly to the motor and may leave the displayed position stale. A successful TCP command does not guarantee the blind moved; the displayed value is the requested position.
- **Stop is not supported** because the packet has not yet been validated. Intermediate positions also await hardware validation.
- If groups are added or removed with the CLI, **reload the Home Assistant integration** to discover the changes. Group discovery is not continuous.
- HACS installs a bundled copy of **this project's own** protocol implementation. No separate PyPI install or forked QSync dependency is needed.

Installation and basic Home Assistant blind control were successfully tested on a QSYNC433FM in October 2026. Other motor generations and gateway variants have not been verified.

## Compatibility and technical details

**Verified:** QMotion Gen 3 FM blinds, QSYNC433FM gateway, TCP port `9760`. **Not verified:** Gen 2 AM, other gateways, actual position feedback, Stop, intermediate position accuracy, and the Python gateway-erase command.

Protocol commands recovered from QSyncAMFM v1.1.3 and confirmed where noted:

| Function | TCP bytes | Status |
|---|---|---|
| List gateway groups | `16 00` | Verified |
| Move to position | `38 02 <channel> <0..100>` | Endpoints verified |
| Special Learn preparation | `38 02 <channel> FA` | Verified |
| Pairing completion | `34 03 <page_hi> <page_lo> <channel>` | Verified |
| Create/update group | `37 3D 01` + 60-byte record | Creation verified |
| Delete group | `32 02 <page_hi> <page_lo>` | Verified |
| Erase gateway | `02 00` | Not tested from Python |

**Architecture:** `src/qmotion_gen3_fm/` holds the shared standard-library Python protocol, transport and admin CLI; `custom_components/qmotion_gen3_fm/` provides the HACS integration with a synchronized bundled copy of the protocol implementation. The gateway is the source of truth for group configuration; channel and page address together identify a group.

For developers:

```bash
python -m unittest discover -s tests -v
python scripts/sync_vendor.py --check
```

See [CHANGELOG.md](CHANGELOG.md) for release history. The code is distributed under the [MIT licence](LICENSE).

### Position-tracking behaviour (development update)

The Home Assistant cover now displays an **assumed last-commanded position** rather than an unknown value:

- On integration setup/reload, it reads the position byte in the gateway's saved FM group record (byte offset 30 of the 60-byte record). An invalid value remains unknown.
- After a Home Assistant command completes at the TCP transport layer, it updates the displayed position to the requested value, converted to HA's position convention.
- Commands from the physical remote do **not** update Home Assistant. The gateway's saved position may also be stale after direct movement; reload is not guaranteed to recover actual physical position.
- The integration deliberately exposes no Stop function or actual-position feedback.

This change is committed after the initial v0.1.0 release documentation and requires a newer HACS checkout/reload. Actual on-device testing of position display remains outstanding.
