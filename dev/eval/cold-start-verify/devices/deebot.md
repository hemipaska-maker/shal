---
type: reference
owner: repo-agent
scope: repo/shal
reviewed: 2026-06-23
---

# Device card — Ecovacs Deebot N20 (the gate hero)

| field | value |
|---|---|
| make / model | Ecovacs · Deebot N20 (`ecovacs,deebot` family, JSON `payloadType:"j"`) |
| reached by | Ecovacs **cloud** (unofficial API via the `deebot-client` library) — personal-rig/demo path, never the implied shipped path |
| Python floor | **3.11+** — `deebot-client` uses `asyncio.TaskGroup` (#84). Build the venv with `PYTHON=py-3.12 bash setup.sh`. |
| creds (`.env`) | `ECOVACS_EMAIL`, `ECOVACS_PASSWORD`, `ECOVACS_COUNTRY`, `ECOVACS_CONTINENT`, `ECOVACS_DEVICE` |

## Acceptance (the success oracle)
- **liveness reads:** `get_battery`, `get_state` → live data (must raise on none).
- **actuation:** `start_cleaning` — **gated** (`side_effect="actuator"`).
- **expected:** after approve, `get_state` **becomes** `cleaning`.
- **deny_path:** after deny, the device **stays** docked/idle (did NOT move).
- **teardown:** `stop_cleaning` then `go_charge` (leave it safe).

## Known gotchas (found in run 1 — operator must handle, none are SHAL-core bugs)
- **Country must be UPPERCASE** for `deebot-client` (`NZ`, not `nz`) or login rejects with
  `errno 1202 "unknown org … ECOWW, country: nz"`. Normalize in the driver.
- **`pip install deebot-client` may try a Rust/maturin build** → use
  `pip install --only-binary=:all: deebot-client` (pure-Python wheel).
- **Windows:** `shal mcp` sets the selector event-loop policy (#87); a hand-rolled script
  needs `WindowsSelectorEventLoopPolicy` for aiomqtt.
- **The robot must be online** (powered, docked, on home Wi-Fi, shown online in the Ecovacs
  app) or every MQTT read times out (`delivered=no`) — a real wall, correctly raised.
