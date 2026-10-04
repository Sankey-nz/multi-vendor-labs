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

## PNetLab Topology Visual Update — 2026-10-04

Updated the live lab file `/opt/unetlab/labs/multivendorlabs.unl` to make the two office zones easier to distinguish:

- Office A panel: pale blue (`#E3F2FD`); title pill: blue (`#1565C0`).
- Office B panel: pale green (`#E8F5E9`); title pill: green (`#2E7D32`).
- Office title text increased from 24px to 26px.
- Office A title box height increased to 38px to fit the larger text.

Only the four corresponding text-object style payloads were changed. Node positions, interface/link definitions, device configurations, and runtime state were not modified. The original lab file was backed up on the PNetLab host at:

```text
/opt/unetlab/labs/multivendorlabs.unl.backup-20261004-2225
```

The backup SHA-256 matches the pre-edit lab file. Refresh the PNetLab topology page to see the updated colors and title sizing. Signed: Copilot.

### Network Layer Labels — 2026-10-04

Added visual labels to the live topology canvas:

- `CORE LAYER` above the CSW1/CSW2 core.
- `DISTRIBUTION LAYER` above each office's DSW pair.
- `ACCESS LAYER` beside each office's access-switch group.

The labels use consistent role colors (blue for core, teal for distribution, slate for access) with white text. The live lab was backed up before editing at `/opt/unetlab/labs/multivendorlabs.unl.backup-20261004-2231`. The XML parsed successfully after the update; node, network, interface/link data and all pre-existing annotations are unchanged. Refresh the PNetLab page to view. Signed: Copilot.

### Topology Legend and EtherChannel Labels — 2026-10-04

Added a compact legend in the open upper-right canvas area:

- Blue = core; teal = distribution; slate = access/WAN labels.
- Red oval = physical member links in an EtherChannel bundle.
- Office A uses PAgP (Cisco), `desirable/desirable`; Office B uses LACP (IEEE 802.3ad), `active/active`.
- Both DSW pairs bundle `e0/0 + e0/1` into `Port-channel1`.

The existing PAgP and LACP pills now show the negotiation modes and member ports. Live device configs are in `configs/DSW-A1.txt`, `DSW-A2.txt`, `DSW-B1.txt`, and `DSW-B2.txt`; the topology guide is `../obsidian-notes/P02-VLANs-and-L2-EtherChannel.md`.

Before editing the live `.unl`, created `/opt/unetlab/labs/multivendorlabs.unl.backup-20261004-2238` and verified its SHA-256 matched the exact pre-edit file. The XML parses after the edit; all node, network, and link definitions and unrelated annotations are unchanged. Refresh PNetLab to see the legend and protocol callouts. Signed: Copilot.

### EtherChannel Callout and Routed-Subnet Label Cleanup — 2026-10-04

Following review that the PAgP/LACP callouts obscured links, both were reduced to compact two-line pills above their respective distribution pairs:

```text
PAgP desirable/desirable | Po1: e0/0 + e0/1
LACP active/active (IEEE) | Po1: e0/0 + e0/1
```

The eight core-to-distribution `/30` labels were normalized to 132 x 26 px, 15 px text, and staggered across two rows. Their text remains attached to the corresponding subnet labels; bounding-box checks confirm no label-to-label overlap. The three R1/core `/30` labels were left unchanged.

The live lab was backed up before editing at `/opt/unetlab/labs/multivendorlabs.unl.backup-20261004-2242`; the backup checksum matched the source. Post-edit XML parses successfully, and all nodes, network definitions, links, and unrelated annotations are unchanged. Refresh the canvas to view. Signed: Copilot.

### Removed Redundant Layer Pills — 2026-10-04

Removed the five repeated `CORE LAYER`, `DISTRIBUTION LAYER`, and `ACCESS LAYER` pills because the legend already explains the corresponding layer colors. Kept the legend, Office A/B headings, WAN EDGE label, PAgP/LACP callouts, and subnet labels.

Backup before removal: `/opt/unetlab/labs/multivendorlabs.unl.backup-20261004-2245` (SHA-256 verified against the pre-edit lab file). XML validation confirmed that exactly the five layer text objects were removed; all 20 nodes, 38 networks, and every other annotation remain unchanged. Refresh PNetLab to view. Signed: Copilot.

### Final Label Simplification — 2026-10-04

Removed the standalone `WAN EDGE` text pill. The WAN area remains visually identified by its blue background. Reduced the two EtherChannel annotations to name-only `PAgP` and `LACP` pills beside their red bundle markers; the legend retains the standards, modes, and color explanations. The legend line now identifies slate as the access-layer color only.

Backup: `/opt/unetlab/labs/multivendorlabs.unl.backup-20261004-2246` (pre-edit SHA-256 verified). XML validation confirms only the WAN pill and the three intended annotation payloads changed; all 20 nodes and 38 networks/links are preserved. Refresh PNetLab to see the final labels. Signed: Copilot.

### Clear CSW1/DSW-B1 e1/1 Port Labels — 2026-10-04

The `10.0.0.52/30` subnet label was covering the diagonal routed link between `CSW1 e1/1` and `DSW-B1 e1/1`. This was an annotation overlap, not a PNetLab rendering fault. Moved that label from `left=905, top=1095` to `left=810, top=1175`; the routed line is now approximately 87 px clear of the label's right edge at that height.

Backup before edit: `/opt/unetlab/labs/multivendorlabs.unl.backup-20261004-2249` (SHA-256 verified). Only the `10.0.0.52/30` text-object position changed; all nodes, interfaces, networks, links, and other annotations remain unchanged. Refresh the canvas to verify both e1/1 labels are visible. Signed: Copilot.

### Office VLAN Summaries on Topology — 2026-10-04

Extended the existing topology legend with compact, color-coded VLAN allocations for each site:

- **Office A:** VLAN 10 users (`10.1.0.0/24`), VLAN 20 staff/voice (`10.2.0.0/24`), VLAN 40 Wi-Fi clients (`10.6.0.0/24`), and VLAN 99 network management (`10.0.0.0/28`).
- **Office B:** VLAN 10 users (`10.3.0.0/24`), VLAN 20 staff (`10.4.0.0/24`), VLAN 30 servers/staff (`10.5.0.0/24`), and VLAN 99 network management (`10.0.0.16/28`).
- Both sites note VLAN 999 for parking and VLAN 1000 as the unused native VLAN.

The legend card was extended downward in the open upper-right canvas area to keep this site-specific detail together without covering office links or device labels. Backup before edit: `/opt/unetlab/labs/multivendorlabs.unl.backup-20261004-2255` (SHA-256: `9d5e4a4541026bd7a698a6208d35d85d7eeca287141b67ab7fc207dc4704c0cc`). The lab XML parses successfully; the 20 nodes and 38 networks/links are unchanged. No VLAN configuration was modified. Refresh PNetLab to view the summary. Signed: Copilot.

The updated live topology was captured as `topology/Screenshot 2026-10-04 23011400.png` and copied over the repository's `topology/topology.png` reference image. The supplied capture is 1693 x 1080 and includes the VLAN legend without the PNetLab footer controls. The prior `topology.png` was preserved outside the repository as `topology-before-vlan-summary-20261004.png` in the local temp directory. Signed: Copilot.
