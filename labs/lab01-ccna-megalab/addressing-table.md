# Addressing Table — Lab 01 CCNA Megalab

> **Last reviewed:** 2026-10-05. Network-device addresses are taken from the harvested configs where available; WLC, server, and Kali details use the source noted in their sections. Known deviations are labeled rather than presented as intended design.

---

## VLAN Definitions

VLAN numbers are locally significant. The same VLAN ID can have a different subnet and purpose in Office A and Office B because the sites are separate Layer 2 domains connected by routed links.

| Site | VLAN | Subnet and mask | HSRP gateway | Purpose |
|------|-----:|-----------------|--------------|---------|
| Office A | 10 | `10.1.0.0/24` (`255.255.255.0`) | `10.1.0.1` | PCs / management clients |
| Office A | 20 | `10.2.0.0/24` (`255.255.255.0`) | `10.2.0.1` | Staff / voice |
| Office A | 40 | `10.6.0.0/24` (`255.255.255.0`) | `10.6.0.1` | Wireless clients |
| Office B | 10 | `10.3.0.0/24` (`255.255.255.0`) | `10.3.0.1` | PCs / management clients |
| Office B | 20 | `10.4.0.0/24` (`255.255.255.0`) | `10.4.0.1` | Staff |
| Office B | 30 | `10.5.0.0/24` (`255.255.255.0`) | `10.5.0.1` | Servers / staff |
| Office A | 99 | `10.0.0.0/28` (`255.255.255.240`) | `10.0.0.1` | Network management, including WLC `10.0.0.7` |
| Office B | 99 | `10.0.0.16/28` (`255.255.255.240`) | `10.0.0.17` | Network management |
| Both sites | 1000 | — | — | Unused native VLAN on trunks |
| Both sites | 999 | — | — | Unused/blackhole ports |

### How the masks divide the address space

The prefix length tells how many leading bits identify the network. The remaining bits identify addresses inside that subnet. These are the mask sizes used in this lab:

| Prefix | Dotted-decimal mask | Addresses per subnet | Usable host addresses | Example use |
|--------|---------------------|----------------------|-----------------------|-------------|
| `/24` | `255.255.255.0` | 256 | 254 | User, staff, server, and wireless VLANs |
| `/28` | `255.255.255.240` | 16 | 14 | Each site's management VLAN |
| `/30` | `255.255.255.252` | 4 | 2 | Routed point-to-point links |
| `/32` | `255.255.255.255` | 1 address | 1 interface address | Router and switch loopbacks |

For example, the Office A management subnet is `10.0.0.0/28`:

```text
Mask bits:       11111111.11111111.11111111.11110000
Dotted mask:     255.255.255.240
Block size:      16 addresses (the final octet advances by 16)
Network address: 10.0.0.0
Usable range:    10.0.0.1–10.0.0.14
Broadcast:       10.0.0.15
HSRP gateway:    10.0.0.1
WLC management:  10.0.0.7
```

The next `/28` block is `10.0.0.16/28`: usable `10.0.0.17–10.0.0.30`, broadcast `10.0.0.31`, and Office B HSRP gateway `10.0.0.17`.

For a routed link, `10.0.0.44/30` has network address `.44`, usable endpoint addresses `.45` and `.46`, and broadcast `.47`. The `/30` mask (`255.255.255.252`) advances in blocks of four addresses, leaving two usable endpoint addresses per link.

The routed-link blocks are `10.0.0.32/30`, `.36/30`, `.40/30`, `.44/30`, `.48/30`, `.52/30`, `.56/30`, `.60/30`, `.64/30`, `.68/30`, and `.72/30`. Device loopbacks use `10.0.0.76/32` through `10.0.0.82/32`.

---

## Edge Router — R1

| Interface | IPv4 Address | IPv6 Address | Description | Source |
|-----------|--------------|--------------|-------------|--------|
| Gi0/1 | 10.0.0.33/30 | EUI-64: `2001:DB8:A1::/64` | Link to CSW1 e0/2 | R1.txt |
| Gi0/0 | 10.0.0.37/30 | EUI-64: `2001:DB8:A2::/64` | Link to CSW2 e0/2 | R1.txt |
| Gi0/2 | 203.0.113.6/30 | `2001:DB8:B::2/64` | WAN ISP-A (static) | R1.txt |
| Gi0/3 | DHCP (192.168.146.x) | `2001:DB8:A::2/64` | WAN ISP-B / default route egress | R1.txt |
| Loopback0 | 10.0.0.76/32 | — | OSPF Router ID | R1.txt |

**Default route:** `ip route 0.0.0.0 0.0.0.0 GigabitEthernet0/3 dhcp` — via ISP-B (Gi0/3).
**PAT:** NAT overload via Gi0/3 for all internal subnets (ACL 2).
**DHCP server:** R1 hosts all DHCP pools (A-Mgmt, A-PC, A-Phone, B-Mgmt, B-PC, B-Phone, Wi-Fi).
**IPv6:** `ipv6 unicast-routing` enabled. EUI-64 on Gi0/0 and Gi0/1. Static routes `::/0` primary + floating.

---

## Core Layer — CSW1

| Interface | IPv4 Address | IPv6 Address | Description | Source |
|-----------|--------------|--------------|-------------|--------|
| Loopback0 | 10.0.0.77/32 | — | OSPF Router ID | CSW1.txt |
| e0/2 | 10.0.0.34/30 | EUI-64: `2001:DB8:A1::/64` | Uplink to R1 Gi0/1 | CSW1.txt |
| Port-channel1 | 10.0.0.41/30 | Link-local only (`ipv6 enable`) | L3 EtherChannel to CSW2 (mode on) | CSW1.txt |
| e0/3 | 10.0.0.45/30 | — | Routed downlink to DSW-A1 | CSW1.txt |
| e1/0 | 10.0.0.49/30 | — | Routed downlink to DSW-A2 | CSW1.txt |
| e1/1 | 10.0.0.53/30 | — | Routed downlink to DSW-B1 | CSW1.txt |
| e1/2 | 10.0.0.57/30 | — | Routed downlink to DSW-B2 | CSW1.txt |

> **No SVIs, no HSRP on CSW1.** Pure L3 routed core. All HSRP/SVI config lives on DSW layer.

---

## Core Layer — CSW2

| Interface | IPv4 Address | IPv6 Address | Description | Source |
|-----------|--------------|--------------|-------------|--------|
| Loopback0 | 10.0.0.78/32 | — | OSPF Router ID | CSW2.txt |
| e0/2 | 10.0.0.38/30 | EUI-64: `2001:DB8:A2::/64` | Uplink to R1 Gi0/0 | CSW2.txt |
| Port-channel1 | 10.0.0.42/30 | Link-local only (`ipv6 enable`) | L3 EtherChannel to CSW1 (mode on) | CSW2.txt |
| e0/3 | 10.0.0.61/30 | — | Routed downlink to DSW-A1 | CSW2.txt |
| e1/0 | 10.0.0.65/30 | — | Routed downlink to DSW-A2 | CSW2.txt |
| e1/1 | 10.0.0.69/30 | — | Routed downlink to DSW-B1 | CSW2.txt |
| e1/2 | 10.0.0.73/30 | — | Routed downlink to DSW-B2 | CSW2.txt |

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
| Vlan10 | 10.1.0.3/24 | 2 | 10.1.0.1 | default | DSW-A2.txt |
| Vlan20 | 10.2.0.3/24 | 3 | 10.2.0.1 | 105 (active) | DSW-A2.txt |
| Vlan40 | 10.6.0.3/24 | 4 | 10.6.0.1 | 105 (active) | DSW-A2.txt |
| Vlan99 | 10.0.0.3/28 | 1 | 10.0.0.1 | default | DSW-A2.txt |

**STP:** Root for VLAN 20, 40 (priority 0). Secondary for VLAN 10, 99 (priority 4096).
**EtherChannel:** Po1 with DSW-A1, PAgP desirable (e0/0 + e0/1).
**ACL:** `OfficeA_to_OfficeB` applied inbound on Vlan10.

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
| ASW-A2 | 10.0.0.5 | /28 | 10.0.0.1 | ASW-A2 | ASW-A2.txt |
| ASW-A3 | 10.0.0.6 | /28 | 10.0.0.1 | ASW-A3 | ASW-A3.txt |
| ASW-B1 | 10.0.0.20 | /28 | 10.0.0.17 | ASW-B1 | ASW-B1.txt |
| ASW-B2 | 10.0.0.21 | /28 | 10.0.0.17 | AWS-B2 | ASW-B2.txt |
| ASW-B3 | 10.0.0.22 | /28 | 10.0.0.17 | ASW-B3 | ASW-B3.txt |
| WLC1 | 10.0.0.7 | /28 | 10.0.0.1 | vWLC | LLM handoff |

## IPv6 Addressing — Configured Interfaces

These entries reflect the device configurations in `configs/`. EUI-64 entries identify the configured `/64` prefix and method; the exact interface identifier is generated from each interface's MAC address. A dash in the IPv6 columns above means no IPv6 address is configured on that interface.

| Device | Interface | IPv6 address or prefix | Method / notes | Source |
|--------|-----------|------------------------|----------------|--------|
| R1 | Gi0/0 → CSW2 e0/2 | `2001:DB8:A2::/64` | EUI-64 | R1.txt |
| CSW2 | e0/2 → R1 Gi0/0 | `2001:DB8:A2::/64` | EUI-64 | CSW2.txt |
| R1 | Gi0/1 → CSW1 e0/2 | `2001:DB8:A1::/64` | EUI-64 | R1.txt |
| CSW1 | e0/2 → R1 Gi0/1 | `2001:DB8:A1::/64` | EUI-64 | CSW1.txt |
| R1 | Gi0/2 (ISP-A) | `2001:DB8:B::2/64` | Manually configured | R1.txt |
| R1 | Gi0/3 (ISP-B) | `2001:DB8:A::2/64` | Manually configured | R1.txt |
| CSW1 | Port-channel1 → CSW2 | Link-local only | `ipv6 enable`; no global address configured | CSW1.txt |
| CSW2 | Port-channel1 → CSW1 | Link-local only | `ipv6 enable`; no global address configured | CSW2.txt |

No IPv6 addresses are configured on the distribution/access switches, their SVIs, or the device loopbacks in the available config files.

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
| eth0 | 99 | 10.0.0.14/28 | Switch and WLC management (VLAN 99) |
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
