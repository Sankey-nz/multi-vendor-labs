# Troubleshooting Scripts

Utility scripts for read-only SSH reachability checks against the listed Lab 01
Cisco devices. Running them attempts network connections; this repository
review did not run them.

## Scripts

### `test_connectivity_v2.py`
Attempts a Netmiko SSH connection to each listed device using the configured
source address and reports success or failure. It does not measure latency.

### `test_ssh_legacy.py`
Attempts SSH with RSA SHA-2 public-key algorithms disabled. It does not
configure legacy key-exchange algorithms.

### `test_ssh_flags.py`
Also attempts SSH with RSA SHA-2 public-key algorithms disabled. It currently
uses the same algorithm restriction as `test_ssh_legacy.py`.

## Typical workflow

1. Set Cisco credentials with the environment variables documented in
   [`../harvest/README.md`](../harvest/README.md), or run interactively for
   hidden password prompts.
2. Run `test_connectivity_v2.py` to check SSH reachability for the listed
   device addresses.
3. Use either SSH test script for its RSA SHA-2 compatibility attempt.

## Requirements
- From the lab root, install with `python -m pip install -r scripts/requirements.txt`.
