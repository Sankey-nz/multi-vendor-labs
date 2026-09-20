# Addressing Table — Lab 01 CCNA Megalab

> **Last verified:** 2026-09-21 — fully reconciled against live harvested running configs.
> All addresses sourced directly from device configs in `configs/`. Deviations from original design are noted inline.

---

## VLAN Definitions

| VLAN ID | Name | Subnet | HSRP VIP | Role |
|---------|------|--------|----------|------|
| 10 | MGMT-A | 10.1.0.0/24 | 10.1.0.1 | Office A Management / PC |
| 20 | STAFF-A | 10.2.0.0/24 | 10.2.0.1 | Office A Staff / Voice |
| 30 | STAFF-B | 10.5.0.0/24 | 10.5.0.1 | Office B Staff / Servers |
| 40 | MGMT-B | 10.3.0.0/24 | 10.3.0.1 | Office B Management / PC |
| 40 (WLC) | Wi-Fi | 10.6.0.0/24 | 10.6.0.1 | Wireless clients (VLAN 40 on DSW-A) |
| 99 | NATIVE/MGMT | 10.0.0.0/28 (A), 10.0.0.16/28 (B) | 10.0.0.1 / 10.0.0.17 | Network Management |
| 1000 | NATIVE-TRUNK | — | — | Native VLAN on all trunks (unused) |
| 999 | UNUSED | — | — | Blackhole — unused ports |

> **Note:** VLAN numbering deviates from original design. Live configs use:
> - VLAN 10 = PC/Management (Office A), VLAN 20 = Voice/Staff (Office A)
> - VLAN 30 = Staff/Servers (Office B), VLAN 40 = PC/Management (Office B)
> - VLAN 40 on DSW-A side = Wi-Fi (10.6.0.0/24) — different VLAN meaning per office

---

## Edge Router — R1

| Interface | IPv4 Address | Description | Source |
|-----------|--------------|-------------|--------|
| Gi0/1 | 10.0.0.33/30 | Link to CSW1 e0/2 | R1.txt |
| Gi0/0 | 10.0.0.37/30 | Link to CSW2 e0/2 | R1.txt |
| Gi0/2 | 203.0.113.6/30 | WAN ISP-A (static) | R1.txt |
| Gi0/3 | DHCP (192.168.146.x) | WAN ISP-B / default route egress | R1.txt |
| Loopback0 | 10.0.0.76/32 | OSPF Router ID | R1.txt |

**Default route:** `ip route 0.0.0.0 0.0.0.0 GigabitEthernet0/3 dhcp` — via ISP-B (Gi0/3).
**PAT:** NAT overload via Gi0/3 for all internal subnets (ACL 2).
**DHCP server:** R1 hosts all DHCP pools (A-Mgmt, A-PC, A-Phone, B-Mgmt, B-PC, B-Phone, Wi-Fi).
**IPv6:** `ipv6 unicast-routing` enabled. EUI-64 on Gi0/0 and Gi0/1. Static routes `::/0` primary + floating.

---

## Core Layer — CSW1

| Interface | IPv4 Address | Description | Source |
|-----------|--------------|-------------|--------|
| Loopback0 | 10.0.0.77/32 | OSPF Router ID | CSW1.txt |
| e0/2 | 10.0.0.34/30 | Uplink to R1 Gi0/1 | CSW1.txt |
| Port-channel1 | 10.0.0.41/30 | L3 EtherChannel to CSW2 (mode on) | CSW1.txt |
| e0/3 | 10.0.0.45/30 | Routed downlink to DSW-A1 | CSW1.txt |
| e1/0 | 10.0.0.49/30 | Routed downlink to DSW-A2 | CSW1.txt |
| e1/1 | 10.0.0.53/30 | Routed downlink to DSW-B1 | CSW1.txt |
| e1/2 | 10.0.0.57/30 | Routed downlink to DSW-B2 | CSW1.txt |

> **No SVIs, no HSRP on CSW1.** Pure L3 routed core. All HSRP/SVI config lives on DSW layer.

---

## Core Layer — CSW2

| Interface | IPv4 Address | Description | Source |
|-----------|--------------|-------------|--------|
| Loopback0 | 10.0.0.78/32 | OSPF Router ID | CSW2.txt |
| e0/2 | 10.0.0.38/30 | Uplink to R1 Gi0/0 | CSW2.txt |
| Port-channel1 | 10.0.0.42/30 | L3 EtherChannel to CSW1 (mode on) | CSW2.txt |
| e0/3 | 10.0.0.61/30 | Routed downlink to DSW-A1 | CSW2.txt |
| e1/0 | 10.0.0.65/30 | Routed downlink to DSW-A2 | CSW2.txt |
| e1/1 | 10.0.0.69/30 | Routed downlink to DSW-B1 | CSW2.txt |
| e1/2 | 10.0.0.73/30 | Routed downlink to DSW-B2 | CSW2.txt |

> **No SVIs, no HSRP on CSW2.** Pure L3 routed core.

---

## Distribution Layer — Office A (DSW-A1)

| Interface | IPv4 Address | HSRP Group | VIP | Priority | Source |
|-----------|--------------|------------|-----|----------|--------|
| Loopback0 | 10.0.0.79/32 | — | — | — | DSW-A1.txt |
| e1/1 | 10.0.0.46/30 | — | — | — | DSW-A1.txt |
| e1/2 | 10.0.0.62/30 | — | — | — | DSW-A1.txt |
| Vlan10 | 10.1.0.2/24 | 2 | 10.1.0.1 | 105 (active) | DSW-A1.txt |
| Vlan20 | 10.2.0.2/24 | 3 | 10.2.0.1 | default | DSW-A1.txt |
| Vlan40 | 10.6.0.2/24 | 4 | 10.6.0.1 | default | DSW-A1.txt |
| Vlan99 | 10.0.0.2/28 | 1 | 10.0.0.1 | 105 (active) | DSW-A1.txt |

**STP:** Root for VLAN 10, 99 (priority 0). Secondary for VLAN 20, 40 (priority 4096).
**EtherChannel:** Po1 with DSW-A2, PAgP desirable (e0/0 + e0/1).
**ACL:** `OfficeA_to_OfficeB` applied inbound on Vlan10.

---

## Distribution Layer — Office A (DSW-A2)

| Interface | IPv4 Address | HSRP Group | VIP | Priority | Source |
|-----------|--------------|------------|-----|----------|--------|
| Loopback0 | 10.0.0.80/32 | — | — | — | DSW-A2.txt |
| e1/1 | 10.0.0.50/30 | — | — | — | DSW-A2.txt |
| e1/2 | 10.0.0.66/30 | — | — | — | DSW-A2.txt |
| Vlan10 | 10.1.0.3/24 | 2 | 10.1.0.1 | default | DSW-A2.txt ⚠️ |
| Vlan20 | 10.2.0.3/24 | 3 | 10.2.0.1 | 105 (active) | DSW-A2.txt |
| Vlan40 | 10.6.0.3/24 | 4 | 10.6.0.1 | 105 (active) | DSW-A2.txt |
| Vlan99 | 10.0.0.3/28 | 1 | 10.0.0.1 | default | DSW-A2.txt |

**STP:** Root for VLAN 20, 40 (priority 0). Secondary for VLAN 10, 99 (priority 4096).
**EtherChannel:** Po1 with DSW-A1, PAgP desirable (e0/0 + e0/1).
**ACL:** `OfficeA_to_OfficeB` applied inbound on Vlan10.

> ⚠️ **Live deviation:** Vlan10, Vlan20, and Vlan40 SVIs are administratively **shutdown** on DSW-A2. Only Vlan99 is active. DSW-A1 carries all active SVI traffic for Office A.

---

## Distribution Layer — Office B (DSW-B1)

| Interface | IPv4 Address | HSRP Group | VIP | Priority | Source |
|-----------|--------------|------------|-----|----------|--------|
| Loopback0 | 10.0.0.81/32 | — | — | — | DSW-B1.txt |
| e1/1 | 10.0.0.54/30 | — | — | — | DSW-B1.txt |
| e1/2 | 10.0.0.70/30 | — | — | — | DSW-B1.txt |
| Vlan10 | 10.3.0.2/24 | 2 | 10.3.0.1 | 105 (active) | DSW-B1.txt |
| Vlan20 | 10.4.0.2/24 | 3 | 10.4.0.1 | default | DSW-B1.txt |
| Vlan30 | 10.5.0.2/24 | 4 | 10.5.0.1 | default | DSW-B1.txt |
| Vlan99 | 10.0.0.18/28 | 1 | 10.0.0.17 | 105 (active) | DSW-B1.txt |

**STP:** Root for VLAN 10, 99 (priority 0). Secondary for VLAN 20, 30 (priority 4096).
**EtherChannel:** Po1 with DSW-B2, LACP active (e0/0 + e0/1).

---

## Distribution Layer — Office B (DSW-B2)

| Interface | IPv4 Address | HSRP Group | VIP | Priority | Source |
|-----------|--------------|------------|-----|----------|--------|
| Loopback0 | 10.0.0.82/32 | — | — | — | DSW-B2.txt |
| e1/1 | 10.0.0.58/30 | — | — | — | DSW-B2.txt |
| e1/2 | 10.0.0.74/30 | — | — | — | DSW-B2.txt |
| Vlan10 | 10.3.0.3/24 | 2 | 10.3.0.1 | default | DSW-B2.txt |
| Vlan20 | 10.4.0.3/24 | 3 | 10.4.0.1 | 105 (active) | DSW-B2.txt |
| Vlan30 | 10.5.0.3/24 | 4 | 10.5.0.1 | 105 (active) | DSW-B2.txt |
| Vlan99 | 10.0.0.19/28 | 1 | 10.0.0.17 | default | DSW-B2.txt |

**STP:** Root for VLAN 20, 30 (priority 0). Secondary for VLAN 10, 99 (priority 4096).
**EtherChannel:** Po1 with DSW-B1, LACP active (e0/0 + e0/1).

---

## Access Layer — Management SVIs

| Device | Vlan99 IP | Mask | Default GW | Config hostname | Source |
|--------|-----------|------|------------|-----------------|--------|
| ASW-A1 | 10.0.0.4 | /24 | 10.0.0.1 | ASW-A1 | ASW-A1.txt |
| ASW-A2 | 10.0.0.5 | /24 | 10.0.0.1 | ASW-A2 | ASW-A2.txt |
| ASW-A3 | 10.0.0.6 | /24 | 10.0.0.1 | ASW-A3 | ASW-A3.txt |
| ASW-B1 | 10.0.0.20 | /28 | 10.0.0.17 | ASW-B1 | ASW-B1.txt |
| ASW-B2 | 10.0.0.21 | /28 | 10.0.0.17 | AWS-B2 ⚠️ | ASW-B2.txt |
| ASW-B3 | 10.0.0.22 | /28 | 10.0.0.17 | ASW-B3 | ASW-B3.txt |
| WLC1 | 10.0.0.7 | /28 | 10.0.0.1 | vWLC | LLM handoff |

> ⚠️ **ASW-B2 hostname typo:** Device is configured with `hostname AWS-B2` (A and S swapped). Functionally fine but inconsistent. Fix with `hostname ASW-B2` if needed.
>
> ⚠️ **ASW-A side mask:** ASW-A1/A2/A3 use `/24` for Vlan99 (10.0.0.x/255.255.255.0) instead of `/28`. This is wider than the Office B ASW switches which correctly use `/28`. Not a connectivity issue but is inconsistent with the /28 subnet design.

---

## Windows Server — WIN-SV1

| Item | Value | Source |
|------|-------|--------|
| IP Address | 10.5.0.4 | Live (ping + DNS) |
| VLAN | 30 (STAFF-B / Servers) | ASW-B3 Et0/2 config |
| Hostname (DNS) | srv.sankeylab.com | Reverse DNS lookup |
| OS | Windows Server 2008 R2 (v6.1) | rpcclient srvinfo |
| Domain | SANKEYLAB / sankeylab.com | rpcclient lsaquery |
| Roles | PDC, DNS Server, Time Server, Domain Controller | rpcclient srvinfo |
| SMB | Port 445 open | Live port scan |
| RDP | Port 3389 open | Live port scan |
| WinRM | Not enabled (5985/5986 closed) | Live port scan |
| AD Users | Administrator, Guest, krbtgt, Sankey | rpcclient enumdomusers |

**DNS behaviour:** Responds to all `*.SankeyLab` queries — acts as authoritative DNS for the domain.
All devices use `10.5.0.4` as name-server and `SankeyLab` as domain-name (confirmed in all device configs).

> **SSH note:** OpenSSH not installed on WIN-SV1. HTTPS download blocked by PNetLab MTU limitation.
> Access via `impacket-smbexec` from Kali works: `impacket-smbexec SANKEYLAB/Sankey:Test123@10.5.0.4`
> RDP also available on port 3389.

---

## Management Host — Kali Linux

| Interface | VLAN | IP Address | Purpose |
|-----------|------|------------|---------|
| eth0 | 99 | 10.0.0.14/24 | Switch management (VLAN 99) |
| eth2 | 10 | 10.1.0.13/24 | User/access VLAN — source IP for device SSH |

**Connected to:** ASW-A1 (visible in topology as "Linux" node)
**PNetLab access:** `ssh kali@192.168.146.129 -p 30067` (user: kali / pass: kali)
**SSH to devices:** Must bind to `10.1.0.14` (eth2) as source — legacy Kex/HostKey/Ciphers required for Cisco IOL.
**Jump path to Office B ASWs:** Kali (10.1.0.14) → DSW-B1 (10.3.0.2) → ASW-B1/B2/B3

> **Note:** ASW VTY ACLs permit `10.1.0.0/24` only — management from eth0 (10.0.0.14) is blocked by implicit deny on A-side ASWs. B-side ASWs (post Sep-20 harvest) permit both `10.1.0.0/24` and `10.0.0.0/24`.

---

## OSPF Summary

| Device | Router ID | Area | Interfaces Advertised |
|--------|-----------|------|-----------------------|
| R1 | 10.0.0.76 | 0 | Loopback0, Gi0/0, Gi0/1 |
| CSW1 | 10.0.0.77 | 0 | Lo0, e0/2, Po1, e0/3, e1/0, e1/1, e1/2 |
| CSW2 | 10.0.0.78 | 0 | Lo0, e0/2, Po1, e0/3, e1/0, e1/1, e1/2 |
| DSW-A1 | 10.0.0.79 | 0 | Lo0, e1/1, e1/2, Vlan10/20/40/99 |
| DSW-A2 | 10.0.0.80 | 0 | Lo0, e1/1, e1/2, Vlan10/20/40/99 |
| DSW-B1 | 10.0.0.81 | 0 | Lo0, e1/1, e1/2, Vlan10/20/30/99 |
| DSW-B2 | 10.0.0.82 | 0 | Lo0, e1/1, e1/2, Vlan10/20/30/99 |

---

## WLC — vWLC1

| Item | Value | Source |
|------|-------|--------|
| Management IP | 10.0.0.7/28 | LLM handoff / R1 DHCP option 43 |
| VLAN | 99 | LLM handoff |
| Gateway | 10.0.0.1 | LLM handoff |
| Data port | ASW-A1 Ethernet1/1 (trunk VLAN 40,99) | ASW-A1.txt |
| Service port | ASW-A1 Ethernet0/2 (trunk VLAN 40,99) | ASW-A1.txt |

> **Original design documented WLC at 192.168.30.20 on VLAN 60 connected to DSW-A1 — all three values are wrong.** Live config confirmed above.

---

## Key Point-to-Point Links Summary

| Link | Side A | Side B | Subnet |
|------|--------|--------|--------|
| R1 ↔ CSW1 | Gi0/1 10.0.0.33/30 | e0/2 10.0.0.34/30 | 10.0.0.32/30 |
| R1 ↔ CSW2 | Gi0/0 10.0.0.37/30 | e0/2 10.0.0.38/30 | 10.0.0.36/30 |
| CSW1 ↔ CSW2 | Po1 10.0.0.41/30 | Po1 10.0.0.42/30 | 10.0.0.40/30 |
| CSW1 ↔ DSW-A1 | e0/3 10.0.0.45/30 | e1/1 10.0.0.46/30 | 10.0.0.44/30 |
| CSW1 ↔ DSW-A2 | e1/0 10.0.0.49/30 | e1/1 10.0.0.50/30 | 10.0.0.48/30 |
| CSW1 ↔ DSW-B1 | e1/1 10.0.0.53/30 | e1/1 10.0.0.54/30 | 10.0.0.52/30 |
| CSW1 ↔ DSW-B2 | e1/2 10.0.0.57/30 | e1/1 10.0.0.58/30 | 10.0.0.56/30 |
| CSW2 ↔ DSW-A1 | e0/3 10.0.0.61/30 | e1/2 10.0.0.62/30 | 10.0.0.60/30 |
| CSW2 ↔ DSW-A2 | e1/0 10.0.0.65/30 | e1/2 10.0.0.66/30 | 10.0.0.64/30 |
| CSW2 ↔ DSW-B1 | e1/1 10.0.0.69/30 | e1/2 10.0.0.70/30 | 10.0.0.68/30 |
| CSW2 ↔ DSW-B2 | e1/2 10.0.0.73/30 | e1/2 10.0.0.74/30 | 10.0.0.72/30 |
