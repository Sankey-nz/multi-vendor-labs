---
title: "P02 — VLANs & Layer-2 EtherChannel"
created: 2025-01-01
updated: 2025-01-01
tags:
  - ccna
  - netbridge
  - networking
  - vlans
  - etherchannel
  - pagp
  - lacp
  - vtp
  - trunking
  - dtp
part: 2
topic: VLANs & Layer-2 EtherChannel
status: reviewed
lab: CCNA Mega Lab
source: CCNA_Mega_Lab_Step_By_Step_Guide.md
---

# P02 — VLANs & Layer-2 EtherChannel

> [!info] Part Summary
> **Topic:** Bond redundant switch links and propagate VLANs cleanly across the access/distribution layers
> **NetBridge Scenario:** The client's offices each have dual distribution switches for redundancy. Part 2 bonds those redundant links into EtherChannels, configures VTP to auto-sync VLANs, and assigns every port to the right VLAN — so hosts in Office A can't see hosts in Office B (unless routing allows it).
> **Key Concepts:** EtherChannel (PAgP vs LACP), trunking, DTP, native VLAN security, VTP, VLAN assignment, PortFast/BPDU Guard on access ports
> **Devices involved:** DSW-A1, DSW-A2, DSW-B1, DSW-B2, ASW-A1, ASW-A2, ASW-A3, ASW-B1, ASW-B2

---

## 🗺️ Big Picture

> [!tip] Mental Model
> Think of Part 2 as building the roads before adding traffic lights (STP) or directions (routing). EtherChannels are the highway lanes; VLANs are the separate lanes within them; VTP is the road-sign syncing system.

```
Office A:                          Office B:
DSW-A1 ══ PAgP ══ DSW-A2          DSW-B1 ══ LACP ══ DSW-B2
   ↕ trunk             ↕ trunk        ↕ trunk            ↕ trunk
ASW-A1  ASW-A2  ASW-A3             ASW-B1  ASW-B2

VLANs Office A: 10 (Mgmt), 20 (Staff), 40 (Servers/Other), 99 (Mgmt)
VLANs Office B: 10 (Mgmt), 20 (Staff), 30 (Staff/Other), 99 (Mgmt)
```

> [!cross-ref] Cross-Reference
> → **[[P03-IP-Addressing-L3-EtherChannel-HSRP]]:** SVIs for each VLAN are configured in Part 3
> → **[[P04-Rapid-Spanning-Tree]]:** STP root alignment with HSRP active router done in Part 4

---

## 📚 Sections

### Section 1 — EtherChannel: PAgP (Office A) and LACP (Office B)

> [!note] Key Concept
> **EtherChannel** (**Link Aggregation**) bundles multiple physical links into one logical link, giving higher bandwidth and redundancy. Two negotiation protocols exist — **PAgP** (Cisco-proprietary) and **LACP** (IEEE 802.3ad open standard).

**PAgP modes:**

| Mode | Behaviour |
|---|---|
| `desirable` | Actively sends PAgP frames — will form a channel |
| `auto` | Passively waits — only forms if other side is `desirable` |

> **Both sides `desirable`** = channel forms ✅

**LACP modes:**

| Mode | Behaviour |
|---|---|
| `active` | Actively sends LACP frames — will form a channel |
| `passive` | Passively waits — only forms if other side is `active` |

> **Both sides `active`** = channel forms ✅ — **One side `passive`** = also works

```
! === Office A: DSW-A1 and DSW-A2 (PAgP — Cisco proprietary) ===

! On DSW-A1
interface range GigabitEthernet1/0/1 - 2
 channel-group 1 mode desirable
 exit

! On DSW-A2 (same config — both desirable)
interface range GigabitEthernet1/0/1 - 2
 channel-group 1 mode desirable
 exit


! === Office B: DSW-B1 and DSW-B2 (LACP — open standard) ===

! On DSW-B1
interface range GigabitEthernet1/0/1 - 2
 channel-group 1 mode active
 exit

! On DSW-B2 (same config — both active)
interface range GigabitEthernet1/0/1 - 2
 channel-group 1 mode active
 exit
```

> [!warning] Exam Flags 🎯
> - PAgP: **desirable-desirable** or **desirable-auto** forms a channel; **auto-auto** does NOT
> - LACP: **active-active** or **active-passive** forms a channel; **passive-passive** does NOT
> - `on` mode: forces EtherChannel with no negotiation — both sides must use `on`; never mix `on` with PAgP/LACP modes

---

### Section 2 — Trunk Configuration on All Inter-Switch Links

> [!note] Key Concept
> Trunks carry **multiple VLANs** on a single physical link using 802.1Q tagging. Every link between access and distribution switches (including the new EtherChannels) must be trunked.

**Key trunk settings:**

```
! Apply to ALL inter-switch links (physical and Port-Channel)
interface Port-channel1
 switchport mode trunk
 switchport nonegotiate
 switchport trunk native vlan 1000
 switchport trunk allowed vlan 10,20,40,99    ! Office A
 ! OR for Office B:
 ! switchport trunk allowed vlan 10,20,30,99
 exit
```

**`switchport nonegotiate` — kill DTP:**
- **DTP** (**Dynamic Trunking Protocol**) auto-negotiates trunk vs. access mode
- Even with `switchport mode trunk`, DTP frames are still sent
- `switchport nonegotiate` stops DTP frames entirely — best practice on all trunk ports

**`switchport trunk native vlan 1000` — VLAN hopping defence:**
- The **native VLAN** carries untagged frames on a trunk
- If two trunks share the same native VLAN, an attacker can inject frames that "hop" between VLANs
- Setting native VLAN to an **unused VLAN** (1000 here) eliminates this attack surface

> [!warning] Exam Flags 🎯
> - Native VLAN mismatch between two trunk ends → CDP warning; traffic issues — both ends must match
> - VLAN 1 is the default native VLAN — always change it
> - `allowed vlan` list only — unlisted VLANs are pruned from the trunk; don't forget to include Management VLAN 99

---

### Section 3 — VTP (VLAN Trunking Protocol)

> [!note] Key Concept
> **VTP** automatically synchronises the VLAN database across switches in the same VTP domain. One **server** creates/modifies VLANs; **clients** receive updates and cannot add VLANs locally.

```
! === VTP Server (one per office — e.g. DSW-A1 for Office A) ===
vtp mode server
vtp domain JeremysITLab
vtp version 2

! Create VLANs on the server only
vlan 10
 name PCs
 exit
vlan 20
 name Phones
 exit
vlan 40
 name Wi-Fi
 exit
vlan 99
 name Management
 exit
! Office B server also creates VLAN 30 (Servers) instead of VLAN 40 (Wi-Fi)


! === VTP Client (all other switches) ===
vtp mode client
vtp domain JeremysITLab
vtp version 2
! VLANs propagate automatically — do NOT create VLANs on clients
```

**VLAN reference table:**

| VLAN | Name | Office A | Office B |
|---|---|---|---|
| 10 | Management | ✅ (10.1.0.0/24) | ✅ (10.3.0.0/24) |
| 20 | Staff | ✅ (10.2.0.0/24) | ✅ (10.4.0.0/24) |
| 30 | Staff/Other | ❌ | ✅ (10.5.0.0/24) |
| 40 | Servers/Other | ✅ (10.6.0.0/24) | ❌ |
| 99 | Management | ✅ (10.0.0.x) | ✅ (10.0.0.x) |
| 1000 | Native (unused) | ✅ | ✅ |

> [!warning] VTP Gotcha 🎯
> A **VTPv2 client with a higher revision number** can overwrite the server's VLAN database when connected — if you bring an old switch in from another network. Always reset revision number to 0 when adding a switch to a new VTP domain (change to transparent mode and back to client/server).

---

### Section 4 — Access Port Configuration

> [!note] Key Concept
> **Access ports** carry only one VLAN and don't tag frames. End devices (PCs, phones, LWAPs) connect to access ports — they're unaware of VLAN tagging.

```
! Standard access port (PC or printer)
interface GigabitEthernet1/0/3
 switchport mode access
 switchport nonegotiate
 switchport access vlan 10
 exit

! Voice port (PC + IP phone on same port)
interface GigabitEthernet1/0/4
 switchport mode access
 switchport nonegotiate
 switchport access vlan 10
 switchport voice vlan 20
 exit

! LWAP / WLC uplink — TRUNK (not access) carrying Management + Wi-Fi VLANs
interface GigabitEthernet1/0/5
 switchport mode trunk
 switchport nonegotiate
 switchport trunk native vlan 99
 switchport trunk allowed vlan 40,99
 exit
```

---

### Section 5 — Disable Unused Ports

> [!note] Key Concept
> Any unused port is a potential security entry point — shut them all down as a baseline hygiene measure.

```
! Find unused ports first
show interfaces status
! Look for any port showing 'notconnect'

! Disable them
interface range GigabitEthernet1/0/10 - 24
 shutdown
 exit
```

---

## 🖥️ NetBridge Applied — Full Config Block

> [!example] DSW-A1 — Complete Part 2 Configuration

```
! === DSW-A1 — VLANs & EtherChannel ===

! Step 1: EtherChannel to DSW-A2 (PAgP)
interface range GigabitEthernet1/0/1 - 2
 channel-group 1 mode desirable
 exit

! Step 2: Configure the Port-Channel as trunk
interface Port-channel1
 switchport mode trunk
 switchport nonegotiate
 switchport trunk native vlan 1000
 switchport trunk allowed vlan 10,20,40,99
 exit

! Step 3: Trunk uplinks to access switches
interface range GigabitEthernet1/0/3 - 5
 switchport mode trunk
 switchport nonegotiate
 switchport trunk native vlan 1000
 switchport trunk allowed vlan 10,20,40,99
 exit

! Step 4: VTP server + create VLANs
vtp mode server
vtp domain JeremysITLab
vtp version 2

vlan 10
 name PCs
vlan 20
 name Phones
vlan 40
 name Wi-Fi
vlan 99
 name Management
vlan 1000
 name Native_Unused
 exit

! Step 5: Save
write memory
```

> [!example] ASW-A1 — Complete Part 2 Configuration

```
! === ASW-A1 — Access Switch ===

! Step 1: VTP client
vtp mode client
vtp domain JeremysITLab
vtp version 2

! Step 2: Uplinks to DSW-A1 and DSW-A2 as trunks
interface range GigabitEthernet0/1 - 2
 switchport mode trunk
 switchport nonegotiate
 switchport trunk native vlan 1000
 switchport trunk allowed vlan 10,20,40,99
 exit

! Step 3: Access ports — PCs on VLAN 10 + phones on VLAN 20
interface range FastEthernet0/1 - 10
 switchport mode access
 switchport nonegotiate
 switchport access vlan 10
 switchport voice vlan 20
 exit

! Step 4: Disable unused ports
interface range FastEthernet0/11 - 24
 shutdown
 exit

! Step 5: Save
write memory
```

---

## ✅ Verification Commands

| Command | What to Look For |
|---|---|
| `show etherchannel summary` | Flags: `SU` on Po1 (Layer 2, in use); `P` on member ports |
| `show interfaces trunk` | Port-channel1 listed as trunk; allowed VLANs correct |
| `show vlan brief` | All VLANs (10, 20, 30/40, 99) present on client switches (propagated by VTP) |
| `show vtp status` | Correct domain, version, and mode (server/client) |
| `show interfaces status` | Unused ports showing `disabled`; access ports showing correct VLAN |
| `show spanning-tree vlan 10` | Port-channel shows as trunk |

---

## ⚠️ Common Pitfalls

> [!warning] Watch Out
> - **`desirable-auto` works; `auto-auto` doesn't** — one side must be active/desirable
> - **Forgetting `switchport nonegotiate`** — DTP still runs even in trunk mode without it; could be exploited
> - **Native VLAN mismatch** — both sides of a trunk must have the same native VLAN or CDP alerts and VLAN tagging breaks
> - **Creating VLANs on VTP clients** — client mode blocks local VLAN creation; create VLANs on the VTP server only
> - **Forgetting to include VLAN 99 in allowed list** — Management VLAN must be explicitly allowed or management traffic is pruned
> - **EtherChannel member ports not matching** — speed, duplex, VLAN config must match on all member interfaces or the channel won't form

---

## 📊 Concepts Summary

| Concept | What It Does | Exam Tip |
|---|---|---|
| EtherChannel | Bundles physical links into one logical link | `show etherchannel summary` — look for `SU` flag |
| PAgP | Cisco-proprietary EtherChannel negotiation | `desirable-desirable` or `desirable-auto` |
| LACP | IEEE 802.3ad EtherChannel negotiation | `active-active` or `active-passive` |
| 802.1Q Trunking | Tags frames with VLAN ID on inter-switch links | Native VLAN frames are NOT tagged |
| DTP | Auto-negotiates trunk vs. access | Disable with `switchport nonegotiate` |
| Native VLAN | Untagged VLAN on a trunk | Set to unused VLAN (e.g. 1000) to prevent hopping |
| VLAN hopping | Attack exploiting shared native VLAN | Fix: change native VLAN to unused VLAN |
| VTP server | Creates and propagates VLANs | Only one server per office needed |
| VTP client | Receives VLAN database, cannot create locally | All access switches are clients |
| VTP revision number | Higher revision wins — can overwrite VLAN DB | Reset by changing domain or mode before connecting |
| Access port | Single VLAN, untagged | End devices connect here |
| Voice VLAN | Separate VLAN for IP phones on same port | `switchport voice vlan 20` |

---

## 🛠️ Practice Tasks

1. **EtherChannel negotiation matrix:** Draw a 3×3 grid with `on/desirable/auto` (PAgP) on each axis. Fill in whether each combination forms a channel. Repeat for LACP with `on/active/passive`.

2. **VLAN hopping demo:** Configure two switches with matching native VLAN 1. Attempt to send an 802.1Q-tagged frame with VLAN 10 across the trunk — observe how it's treated. Then change native VLAN to 1000 and verify the attack no longer works.

3. **VTP revision reset:** Take a switch configured as VTP client in domain "OldDomain" with revision 50. Add it to your lab. What happens to your VLAN database? How do you prevent this? Reset the revision number and re-add safely.

4. **Allowed VLAN troubleshooting:** Remove VLAN 99 from the allowed list on one trunk. Try to ping the Management SVI from that VLAN. Observe the failure. Re-add VLAN 99 and verify connectivity restores.
