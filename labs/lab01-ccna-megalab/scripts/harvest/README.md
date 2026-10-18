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
# From the repository root
python labs/lab01-ccna-megalab/scripts/harvest/final_harvest_v5.py
python labs/lab01-ccna-megalab/scripts/harvest/harvest_aswb_v2.py
```

## Requirements and credentials

Install the pinned dependencies from the lab directory:

```bash
python -m pip install -r scripts/requirements.txt
```

Set `CISCO_USERNAME`, `CISCO_PASSWORD`, and `CISCO_ENABLE_SECRET` in the
environment before running. If a value is unset, interactive runs prompt for
it (passwords are hidden); non-interactive runs fail with a clear error.
The ASW-B harvester also requires `KALI_HOST`, `KALI_PORT`, `KALI_USERNAME`,
and `KALI_PASSWORD`. `.env.example` lists the variable names and placeholders;
it is not loaded automatically.

Harvested output redacts local authentication directives and SNMP community
values before writing config snapshots. The snapshots are evidence of
configuration, not proof of end-to-end service behavior.

Netmiko `4.7.0` is documented as the version used for collection. The
Paramiko version used was not recorded, so it remains unpinned in
`scripts/requirements.txt` pending confirmation.
