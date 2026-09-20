# Lab 01 — Compact LLM Handoff

> **Last updated:** 2026-09-21  
> **Prepared by:** Kiro  
> **Purpose:** Fast context for the next LLM working in this directory.

## Source of Truth

For current behavior, trust live `show` output and the harvested Cisco configurations under `configs/` over the older design documentation. FW1/FortiGate has been removed from the Lab 01 design. R1 is the live edge router.

## Access Path

- PNetLab server: `192.168.146.129`
- Kali VM SSH forwarding: server TCP `30067` -> Kali TCP `22`
- Kali account access is available through the authorized local workflow.
- Cisco SSH user and credentials are stored in the existing Kali workflow; do not duplicate secrets in reports.
- Cisco compatibility options:

```bash
-oKexAlgorithms=diffie-hellman-group14-sha1
-oHostKeyAlgorithms=ssh-rsa
-oPubkeyAcceptedAlgorithms=ssh-rsa
-oCiphers=aes128-ctr
-oMACs=hmac-sha1
```

## Kali VLAN Interfaces

Kali now has two separate interfaces:

| Interface | VLAN | Address | Purpose |
|---|---:|---|---|
| `eth0` | 99 | `10.0.0.14/28` | Switch management |
| `eth2` | 10 | `10.1.0.13/24` | User/access VLAN |

Use VLAN 99 to reach switch management addresses. Do not rely on the old single-interface/stale-address arrangement.

## Live Device Inventory

| Device | Management/loopback address | Live status |
|---|---|---|
| R1 | `10.0.0.76` | SSH and read-only collection successful |
| CSW1 | `10.0.0.77` | SSH and read-only collection successful |
| CSW2 | `10.0.0.78` | SSH and read-only collection successful |
| DSW-A1 | `10.0.0.79` | SSH and read-only collection successful |
| DSW-A2 | `10.0.0.80` | SSH and read-only collection successful |
| DSW-B1 | `10.0.0.81` | SSH and read-only collection successful |
| DSW-B2 | `10.0.0.82` | SSH and read-only collection successful |
| ASW-A1 | `10.0.0.4` | Direct SSH now successful from Kali VLAN 99 |
| ASW-A2 | `10.0.0.5` | SSH and read-only collection successful |
| ASW-A3 | `10.0.0.6` | SSH and read-only collection successful |
| WIN-SV1 | `10.5.0.4` | SMB/RDP reachable; no SSH (OpenSSH not installed); access via impacket-smbexec |
| ASW-B1 | `10.0.0.20` | SSH via DSW-B1 jump — collection successful |
| ASW-B2 | `10.0.0.21` | SSH via DSW-B1 jump — collection successful |
| ASW-B3 | `10.0.0.22` | SSH via DSW-B1 jump — collection successful |

## Verified Topology

```text
Upstream/WAN
    |
R1
  Gi0/1 10.0.0.33 ---- CSW1 Et0/2 10.0.0.34
  Gi0/0 10.0.0.37 ---- CSW2 Et0/2 10.0.0.38
  Gi0/2 203.0.113.6
  Gi0/3 192.168.146.209 (DHCP/upstream)

CSW1 Po1 10.0.0.41 ===== CSW2 Po1 10.0.0.42

CSW1/CSW2 routed OSPF uplinks:
  10.0.0.44/30, .48/30, .52/30, .56/30
  10.0.0.60/30, .64/30, .68/30, .72/30

Office A:
  DSW-A1 10.0.0.2, routed links .46/.62, SVIs 10.1.0.2/10.2.0.2/10.6.0.2
  DSW-A2 10.0.0.3, routed links .50/.66, SVIs 10.1.0.3/10.2.0.3/10.6.0.3
  DSW-A1/A2 Po1: Layer-2 PAgP

Office B:
  DSW-B1 10.0.0.18, routed links .54/.70, SVIs 10.3.0.2/10.4.0.2/10.5.0.2
  DSW-B2 10.0.0.19, routed links .58/.74, SVIs 10.3.0.3/10.4.0.3/10.5.0.3
  DSW-B1/B2 Po1: Layer-2 LACP
```

## Important Live Findings

- R1 has default route via `192.168.146.2` on `Gi0/3`, not via FW1.
- R1, CSW1, and CSW2 have full OSPF adjacency.
- CSW1/CSW2 are routed Layer-3 core switches; they do not carry the documented HSRP SVIs.
- Distribution switches carry the VLAN SVIs and HSRP.
- DSW-A2 VLAN 10, 20, and 40 SVIs are administratively down.
- DSW-A1 and DSW-A2 use PAgP; DSW-B1 and DSW-B2 use LACP; CSW1/CSW2 use a routed static EtherChannel.
- RSTP/PVST and VLAN/trunk behavior should be treated as live-config evidence, not the older README design.
- ASW-A1 `Ethernet0/3` is access VLAN 10 with voice VLAN 99; `Vlan99` is `10.0.0.4`.
- ASW-A1 LLDP:
  - `Et0/0` -> DSW-A1 `10.0.0.46`
  - `Et0/1` -> DSW-A2 `10.0.0.50`

## SSH/VTY ACL Lesson

ASW-A1 and likely ASW-A2 use:

```text
line vty 0 4
 access-class 1 in
 login local
 transport input ssh

access-list 1 permit 10.1.0.0 0.0.0.255
```

This permits SSH only from VLAN 10 sources. VLAN 99 management sources such as `10.0.0.14` or DSW-A1 `10.0.0.2` are denied by the implicit deny. Ping can succeed while SSH is refused.

For the intended management design, add the management subnet while preserving VLAN 10 access:

```text
conf t
access-list 1 permit 10.0.0.0 0.0.0.15
end
```

Verify before saving:

```text
show access-lists 1
show running-config | section line vty
```

Clear counters and test one connection if learning ACL behavior:

```text
clear access-list counters 1
show access-lists 1
```

Do not use broad `debug ip packet` for long periods. Stop it with `undebug all`.

## Current Blockers

1. The older `README.md` and `addressing-table.md` still contain some planned-design drift beyond the FW1 removal. Treat them as documentation requiring further synchronization.
2. Do not make configuration changes unless explicitly requested. Previous work was read-only except for temporary Kali interface/address tests.

**ASW-B access note:** ASW-B1/B2/B3 require a jump via DSW-B1 (`10.3.0.2`) from Kali `eth2` (`10.1.0.14`). Direct SSH from VLAN 99 (`10.0.0.x`) is blocked by the VTY ACL, which permits only `10.1.0.0/24`.

## Live Configuration Harvest — 2026-09-09 23:15:32 NZST

The `configs/` directory now contains a fresh read-only Netmiko harvest from R1, CSW1/2, DSW-A1/A2, DSW-B1/B2, and ASW-A1/A2/A3. ASW-B1/B2/B3 and the WLC at the previously assumed addresses could not be reached over SSH. Treat the harvested files and `configs/live-configs-20260909/HARVEST_STATUS.txt` as the current evidence; the older README/addressing table remain design references only. Signed: Copilot.

## Final vWLC State — 2026-09-14

The vWLC management path is working. The confirmed virtual-cable mapping is:

```text
vWLC g0/0/0 -> ASW-A1 Ethernet0/2  (service/out-of-band port)
vWLC g0/0/1 -> ASW-A1 Ethernet1/1  (data/management port)
```

The WLC management interface is statically configured as:

```text
IP address: 10.0.0.7/28
VLAN:       99
Gateway:    10.0.0.1
```

Normal access uses the data-port trunk:

```text
Kali eth0 untagged access VLAN 99
  -> ASW-A1 Ethernet1/1 trunk
  -> vWLC g0/0/1
  -> WLC management 10.0.0.7
```

The original outage was caused by connecting the VLAN 99 trunk to the service-port NIC (`g0/0/0`) instead of the data-port NIC (`g0/0/1`). The service-port could remain up while the management/data port was down. ASW-A1 `Ethernet1/1` also required the correct trunk configuration and interface trust for Dynamic ARP Inspection/DHCP snooping because the WLC uses a static address.

**Current WLC status:** management access confirmed through VLAN 99 data-port.  
**Prepared by:** Copilot

## Remaining Issue — HTTPS/TLS Only

The WLC path is resolved. The only remaining active issue is the independent HTTPS/TLS failure affecting Kali/Windows outbound connections.

Confirmed TLS facts:
```text
NAT/PAT:       healthy; translations active and zero misses
DNS:           tested with internal and public resolvers; not causal
TCP/443:       establishes
HTTP:          works
TLS:           stalls after ClientHello / early server response
Clock:         checked and not the cause
MSS 1360:      tested on R1; did not resolve the issue
```

Investigation History (2026-09-14):
- Attempted `ip tcp adjust-mss 1360` on WAN interfaces $\rightarrow$ Failed.
- Attempted `ip tcp adjust-mss 1200` + `ip mtu 1400` on WAN $\rightarrow$ Failed.
- Attempted Global `ip tcp adjust-mss 1200` on all interfaces $\rightarrow$ Failed.
- Attempted "Nuclear" fix: `ip mtu 1200` + `ip tcp adjust-mss 1200` on WAN $\rightarrow$ Failed.
- Observation: Handshake progressed to "Server Hello" after MSS clamping, but stalled on large Certificate packets.
- Diagnosis: Highly likely a PNetLab/Host-level MTU drop (PMTUD Black Hole) that persists despite router-level configuration.

## WIN-SV1 Access (Windows Server 2008 R2)

- **IP:** `10.5.0.4` (VLAN 30, Office B servers subnet)
- **Hostname:** `srv.sankeylab.com`
- **Domain:** `SANKEYLAB` — PDC, DNS, Time Server
- **Credentials:** `SANKEYLAB\Sankey` / `Test123`
- **SSH:** Not available — OpenSSH not installed; HTTPS blocked by PNetLab MTU issue prevents download
- **RDP:** Port 3389 open — connect via `xfreerdp` from Kali GUI or Windows RDP client
- **SMB:** Port 445 open — use impacket tools from Kali:

```bash
# Interactive shell
impacket-smbexec SANKEYLAB/Sankey:Test123@10.5.0.4

# Single command
impacket-wmiexec SANKEYLAB/Sankey:Test123@10.5.0.4 "whoami"

# Domain/user info
rpcclient -U SANKEYLAB/Sankey%Test123 10.5.0.4 -c srvinfo
```

- **DNS:** All devices point to `10.5.0.4` as name-server with domain `SankeyLab`
- **AD Users:** Administrator, Guest, krbtgt, Sankey

## Netmiko & Management Tooling
Netmiko is installed on the Kali VM. To access network devices, a jump-host approach is required via the Kali machine.

Access details:
- Kali SSH: `kali@192.168.146.129 -p 30067`
- Credentials: User `kali` / Password `kali`
- Device Credentials: User `cisco` / Password `CCNA` / Enable `class`
- **Critical R1 Access:** R1 is accessible at `10.0.0.76` ONLY when binding to the source IP `10.1.0.14` (eth2 on Kali).
- SSH Compatibility: Requires legacy Kex/HostKey/Ciphers (see "Access Path" section above).

Tools on Kali:
- `/home/kali/harvest_configs.sh`: Script for bulk config collection.
- Various Python/Netmiko scripts were used for auditing and fixing (stored locally in the repo under `audit_r1_nat.py`, etc., for reference).


## Config Harvest Status — 2026-09-21

All 13 devices now have configs collected in `labs/lab01-ccna-megalab/configs/`.

| Device group | Method | Notes |
|---|---|---|
| R1, CSW1/2, DSW-A1/A2, DSW-B1/B2, ASW-A1/A2/A3 | Direct SSH from Kali VLAN 99 (`10.0.0.14`) | Previously harvested 2026-09-09 |
| ASW-B1/B2/B3 | Shell hop: Kali (`10.1.0.14`) → DSW-B1 (`10.3.0.2`) → ASW-Bx | Harvested 2026-09-21 |

- Script used: `scripts/harvest/harvest_aswb_shell.py`
- Duplicate old-format files (no-hyphen naming) removed from `configs/`
- Obsidian notes P07/P08/P09 updated with live evidence (2026-09-21)

**Prepared by:** Kiro
