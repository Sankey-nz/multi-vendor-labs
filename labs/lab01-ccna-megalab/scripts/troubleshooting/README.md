# Troubleshooting Scripts

Utility scripts used during lab bring-up to diagnose SSH/connectivity issues
between the Windows host and Cisco IOS/NX-OS devices.

## Scripts

### `test_connectivity_v2.py`
Comprehensive reachability test. Attempts a Netmiko SSH connection to every
device in the lab topology and reports success/failure with latency.
Use this first when a device appears unreachable.

### `test_ssh_legacy.py`
Attempts SSH using legacy key-exchange algorithms (`diffie-hellman-group1-sha1`,
`diffie-hellman-group14-sha1`). Useful when a Cisco IOS device refuses the
default modern algorithms negotiated by OpenSSH/Paramiko.

### `test_ssh_flags.py`
Tests SSH with various Paramiko transport flags (disabled algorithms, adjusted
banner timeout, manual auth). Helps narrow down which SSH handshake parameter
is causing a connection failure.

## Typical workflow

1. Run `test_connectivity_v2.py` to identify which devices are down.
2. For SSH negotiation failures, try `test_ssh_legacy.py`.
3. For persistent Paramiko errors, use `test_ssh_flags.py` to isolate the flag.

## Requirements
- `netmiko`, `paramiko` — install with `pip install netmiko paramiko`
