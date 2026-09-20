# Harvest Scripts

These scripts SSH into lab devices and collect running configurations,
saving them as plain-text files under `configs/`.

## Scripts

### `final_harvest_v5.py`
The primary harvest script. Connects to all lab devices via Netmiko (SSH)
and writes each device's running-config to `configs/<hostname>.txt`.
Use this for routine config snapshots.

### `harvest_aswb_v2.py`
Targeted harvest for the ASW-B access-layer switches (ASW-B1/B2/B3).
Uses a shell-channel workaround to reliably capture output from switches
that drop the channel after `terminal length 0`. Run after any ASW-B
change to update their config files.

## Usage

```bash
# From the lab root
python labs/lab01-ccna-megalab/scripts/harvest/final_harvest_v5.py
python labs/lab01-ccna-megalab/scripts/harvest/harvest_aswb_v2.py
```

## Requirements
- `netmiko` — install with `pip install netmiko`
- Lab devices reachable on the management network (see `addressing-table.md`)
