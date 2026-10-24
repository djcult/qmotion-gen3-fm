# Changelog

## v0.1.1 — 2026-10-24

- Home Assistant cover now exposes last-commanded position as **assumed** rather than always unknown.
- At startup, initial position comes from the gateway's stored FM group position, if valid.
- HA position updates only after TCP send succeeds; it is not motor feedback and physical remote use can make it stale.
- Added regression tests for the opposite QSync and Home Assistant percentage conventions.

## v0.1.0 — 2026-10-24

First hardware-tested release of an independent QMotion Gen 3 FM implementation.

### Working on physical hardware

- Communicate directly with a QSYNC433FM gateway over TCP port 9760.
- Discover and parse FM groups and their channel/page addresses.
- Create and delete gateway FM groups using the standalone CLI.
- Initiate Special Learn, select a blind by physical tug and complete pairing.
- Open and close a paired blind while preserving the original handheld remote.
- Install a HACS custom integration and control the blind from a Home Assistant cover entity.

### Distribution

- Standard-library Python protocol library and `qmotion-admin` CLI.
- Standalone gateway administration, separate from HA cover control.
- Dry-run by default for create, delete, pair and gateway erase, with `--send` for explicit transmission.
- HACS integration bundles a synchronized copy of this project's own protocol library; no dependency on the third-party/forked QSync libraries.
- Offline packet tests and GitHub Actions checks.

### Known limitations

- One-way RF; no actual blind position or remote-control state feedback.
- No verified Stop function; intermediate percentage control not yet physically validated.
- Gateway erase packet reconstructed from original app but not tested through Python.
- Newly added/deleted groups require HA integration reload or restart.
- Verified only on QMotion Gen 3 FM with QSYNC433FM; other generations/gateways untested.

### Development reference

Protocol reconstructed from the original QSyncAMFM 1.1.3 Android/.NET app and validated through a real gateway and blind. The app is not required at runtime.
