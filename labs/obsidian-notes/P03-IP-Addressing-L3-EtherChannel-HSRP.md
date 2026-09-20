---
title: "P03 — IP Addressing, L3 EtherChannel & HSRP"
created: 2025-01-01
updated: 2025-01-01
tags:
  - ccna
  - netbridge
  - networking
  - ip-addressing
  - hsrp
  - etherchannel
  - layer3
  - svi
  - routing
part: 3
topic: IP Addressing, L3 EtherChannel & HSRP
status: reviewed
lab: CCNA Mega Lab
source: CCNA_Mega_Lab_Step_By_Step_Guide.md
---

# P03 — IP Addressing, L3 EtherChannel & HSRP

> [!info] Part Summary
> **Topic:** Assign IP addresses to all L3 interfaces, build the routed EtherChannel between core switches, and configure HSRP for redundant default gateways on each VLAN
> **NetBridge Scenario:** With VLANs propagating cleanly, it's time to add Layer 3 — IP addresses on every SVI and routed interface, a routed EtherChannel linking the two core switches, and HSRP so hosts always have a working gateway even if one distribution switch fails.
> **Key Concepts:** `ip routing`, SVIs, routed ports (`no switchport`), L3 EtherChannel, loopback interfaces, HSRP v2, virtual IP, priority, preempt
> **Devices involved:** R1, CSW1, CSW2, DSW-A1, DSW-A2, DSW-B1, DSW-B2

---

## 🗺️ Big Picture

> [!tip] Mental Model
> Part 3 turns the switches from dumb L2 forwarders into proper routers. HSRP gives each subnet a single virtual gateway IP — hosts never need to know which physical switch is active.

```
Hosts in VLAN 10 → default gateway = HSRP Virtual IP (e.g. 10.1.0.1)
                              ↓
              DSW-A1 (Active, priority 105)  OR  DSW-A2 (Standby, priority 100)
                     ↕ HSRP negotiation via hello/dead timers
              If DSW-A1 fails → DSW-A2 becomes active automatically
              If DSW-A1 recovers → preempt reclaims active role
```

> [!cross-ref] Cross-Reference
> → **[[P02-VLANs-and-L2-EtherChannel]]:** SVIs are created for VLANs defined in Part 2
> → **[[P05-OSPF-and-Static-Routing]]:** OSPF runs over the L3 interfaces configured here

---

## 📚 Sections

### Section 1 — Enable `ip routing` on Switches

> [!note] Key Concept
> By default, Cisco multilayer switches act as pure L2 devices. `ip routing` enables the routing engine — turning SVIs and routed ports into actual L3 interfaces that participate in routing.

```
! Required on CSW1, CSW2, DSW-A1, DSW-A2, DSW-B1, DSW-B2
ip routing
```

> [!warning] Exam Flag 🎯
> Forgetting `ip routing` on a multilayer switch means SVIs have IP addresses but don't route traffic. Symptom: hosts can ping their own SVI but not reach other subnets.

---

### Section 2 — R1 Interface Configuration

> [!note] Key Concept
> R1 has two WAN links (DHCP from ISPs) and a LAN-facing link to the core. A **loopback interface** provides a stable, always-up identity address used as the OSPF router ID and DHCP relay target.

```
! WAN interfaces — get IP from ISP via DHCP
interface GigabitEthernet0/3
 ip address dhcp
 no shutdown
 exit

interface GigabitEthernet0/2
 ip address 203.0.113.6 255.255.255.252
 no shutdown
 exit

! LAN-facing interfaces to core
interface GigabitEthernet0/1
 ip address 10.0.0.33 255.255.255.252
 no shutdown
 exit

interface GigabitEthernet0/0
 ip address 10.0.0.37 255.255.255.252
 no shutdown
 exit

! Loopback — stable identity; never goes down
interface Loopback0
 ip address 10.0.0.76 255.255.255.255
 exit
```

**Why a Loopback?**
- Physical interfaces go down when cables are pulled; loopbacks never go down
- Used as OSPF router ID (stable, predictable)
- Used as DHCP relay target — `ip helper-address 10.0.0.76` — so any distribution switch can relay to R1 regardless of which physical path is used

---

### Section 3 — Layer-3 EtherChannel (CSW1 ↔ CSW2)

> [!note] Key Concept
> A **routed EtherChannel** (L3) bonds the physical links between core switches into one logical routed link — the IP address lives on the `Port-channel` interface, not the physical members.

```
! === CSW1 ===

! Step 1: Convert physical interfaces to routed ports
interface range Ethernet0/0 - 1
 no switchport              ! removes L2 switchport config → becomes routed port
 channel-group 1 mode on
 exit

! Step 2: Assign IP to the Port-Channel interface
interface Port-channel1
 no switchport
 ip address 10.0.0.41 255.255.255.252
 exit

! === CSW2 (mirror config, different IP) ===
interface range Ethernet0/0 - 1
 no switchport
 channel-group 1 mode on
 exit

interface Port-channel1
 no switchport
 ip address 10.0.0.42 255.255.255.252
 exit
```

> [!warning] Exam Flag 🎯
> On a multilayer switch, `no switchport` converts a port from switchport (L2) to routed port (L3). You cannot assign an IP to a switchport — the command will be rejected. Always `no switchport` first on L3 EtherChannel members.

---

### Section 4 — SVIs on Distribution Switches

> [!note] Key Concept
> A **Switch Virtual Interface (SVI)** is a virtual L3 interface for a VLAN — it acts as the default gateway for hosts in that VLAN. Each distribution switch gets an SVI per VLAN with a unique IP; HSRP adds the shared virtual IP on top.

```
! === DSW-A1 SVIs ===
interface Vlan10
 ip address 10.1.0.2 255.255.255.0
 no shutdown
 exit

interface Vlan20
 ip address 10.2.0.2 255.255.255.0
 no shutdown
 exit

interface Vlan40
 ip address 10.6.0.2 255.255.255.0
 no shutdown
 exit

interface Vlan99
 ip address 10.0.0.2 255.255.255.0
 no shutdown
 exit

! DSW-A2 gets .3 on the same subnets
! DSW-B1/B2 get IPs on their own subnets (e.g. 10.3.x.x for Office B Mgmt)
```

---

### Section 5 — HSRP v2

> [!note] Key Concept
> **HSRP** (**Hot Standby Router Protocol**) creates a **virtual IP** shared between two routers. Hosts use the virtual IP as their default gateway — HSRP decides which physical router actually handles traffic. Only one router is **active** at a time; the other is **standby**.

**HSRP key concepts:**
- **Virtual IP** — the gateway IP hosts are configured with (e.g. `10.1.10.1`)
- **Active router** — currently forwarding traffic; elected by highest priority (default 100)
- **Standby router** — monitoring; takes over if active fails
- **Preempt** — active router reclaims its role when it comes back after a failure
- **Version 2** — supports IPv6, millisecond timers, more groups than v1

```
! === DSW-A1 — HSRP Active for VLANs 10 and 99 ===

interface Vlan10
 standby version 2
 standby 1 ip 10.1.10.1            ! virtual IP — what hosts use as gateway
 standby 1 priority 105            ! higher than default 100 → wins election
 standby 1 preempt                 ! reclaim active when recovered
 exit

interface Vlan99
 standby version 2
 standby 2 ip 10.1.99.1
 standby 2 priority 105
 standby 2 preempt
 exit

! DSW-A1 is STANDBY for VLANs 20 and 40
interface Vlan20
 standby version 2
 standby 3 ip 10.1.20.1
 ! No priority bump — default 100 = standby
 exit

interface Vlan40
 standby version 2
 standby 4 ip 10.1.40.1
 exit


! === DSW-A2 — HSRP Active for VLANs 20 and 40 ===

interface Vlan20
 standby version 2
 standby 3 ip 10.1.20.1
 standby 3 priority 105
 standby 3 preempt
 exit

interface Vlan40
 standby version 2
 standby 4 ip 10.1.40.1
 standby 4 priority 105
 standby 4 preempt
 exit

! DSW-A2 is STANDBY for VLANs 10 and 99 (no priority bump)
interface Vlan10
 standby version 2
 standby 1 ip 10.1.10.1
 exit

interface Vlan99
 standby version 2
 standby 2 ip 10.1.99.1
 exit
```

**HSRP load-balancing via split active/standby:**

| VLAN | HSRP Group | Active | Standby |
|---|---|---|---|
| 10 Mgmt | 1 | DSW-A1 (105) | DSW-A2 (100) |
| 20 Staff | 3 | DSW-A2 (105) | DSW-A1 (100) |
| 40 Servers | 4 | DSW-A2 (105) | DSW-A1 (100) |
| 99 Mgmt | 2 | DSW-A1 (105) | DSW-A2 (100) |

> [!warning] Exam Flags 🎯
> - HSRP virtual IP must be in the same subnet as the SVI IPs but NOT the same as any physical SVI IP
> - `standby preempt` is essential — without it, DSW-A1 won't reclaim active role after recovering from a failure; DSW-A2 stays active permanently
> - HSRP v2 group numbers: 0–4095 (v1 supports 0–255 only)
> - Align HSRP active with STP root (done in Part 4) — misalignment causes suboptimal L2 paths to the L3 gateway

---

## 🖥️ NetBridge Applied — Full Config Block

> [!example] DSW-A1 — Complete Part 3 Configuration

```
! === DSW-A1 — IP Addressing + HSRP ===

! Enable routing
ip routing

! Uplink to CSW1
interface Ethernet1/1
 no switchport
 ip address 10.0.0.46 255.255.255.252
 no shutdown
 exit

! Uplink to CSW2
interface Ethernet1/2
 no switchport
 ip address 10.0.0.62 255.255.255.252
 no shutdown
 exit

! SVIs + HSRP
interface Vlan10
 ip address 10.1.0.2 255.255.255.0
 no shutdown
 standby version 2
 standby 1 ip 10.1.0.1
 standby 1 priority 105
 standby 1 preempt
 exit

interface Vlan20
 ip address 10.2.0.2 255.255.255.0
 no shutdown
 standby version 2
 standby 3 ip 10.2.0.1
 exit

interface Vlan40
 ip address 10.6.0.2 255.255.255.0
 no shutdown
 standby version 2
 standby 4 ip 10.6.0.1
 exit

interface Vlan99
 ip address 10.0.0.2 255.255.255.0
 no shutdown
 standby version 2
 standby 2 ip 10.0.0.1
 standby 2 priority 105
 standby 2 preempt
 exit

write memory
```

---

## ✅ Verification Commands

| Command | What to Look For |
|---|---|
| `show ip interface brief \| exclude un` | All SVIs and uplinks show correct IPs and `up/up` |
| `show standby brief` | Active/Standby state per group; virtual IP correct |
| `show standby vlan 10` | Priority 105 + preempt on active switch |
| `show etherchannel summary` | Po1 shows `RU` (Layer 3, in use) on L3 EtherChannel |
| `show ip route` | Connected routes for all SVIs present |
| `ping 10.1.10.1` | Ping the HSRP virtual IP from the switch itself |

---

## ⚠️ Common Pitfalls

> [!warning] Watch Out
> - **Forgetting `ip routing`** — SVIs won't route; hosts can reach their SVI but nothing beyond
> - **`no switchport` on wrong ports** — only use on uplink/EtherChannel member ports; access/trunk ports to hosts should remain switchports
> - **HSRP virtual IP in wrong subnet** — virtual IP must be in the same /24 as the SVI physical IPs
> - **Forgetting `preempt`** — without it, the standby switch becomes active after a failover and stays active permanently even after the original active recovers
> - **HSRP group number mismatch** — both switches must use the same group number for the same VLAN; mismatched groups = two active routers = split-brain
> - **Not aligning HSRP with STP root** — covered in Part 4; skipping this causes traffic to take an inefficient L2 path to the gateway

---

## 📊 Concepts Summary

| Concept | What It Does | Exam Tip |
|---|---|---|
| `ip routing` | Enables L3 routing on multilayer switch | Required before SVIs can route |
| SVI (Vlan interface) | L3 gateway for a VLAN | Must match VLAN number exactly |
| `no switchport` | Converts port from L2 to L3 routed port | Required before assigning IP to a switch port |
| Loopback interface | Always-up virtual interface | Used as OSPF router ID and DHCP relay target |
| L3 EtherChannel | Routed port-channel between switches | IP on Port-channel, not member ports |
| HSRP v2 | Shared virtual gateway between two routers | Virtual IP = what hosts use as default gateway |
| `standby priority 105` | Makes this router the HSRP active | Default priority 100; higher wins |
| `standby preempt` | Reclaim active role after recovery | Without it, standby stays active permanently |
| HSRP split active/standby | Load balance traffic across two switches | Different VLANs have different active routers |

---

## 🛠️ Practice Tasks

1. **HSRP failover test:** Configure HSRP on two distribution switches. Ping the virtual IP from a host continuously (`ping -t`). Shut down the active switch's uplink. Verify pings resume within ~3 seconds (HSRP dead timer). Re-enable the uplink and verify preempt reclaims the active role.

2. **L3 EtherChannel:** Bond two links between CSW1 and CSW2 as a routed EtherChannel. Assign IPs to the Port-channel interfaces. Verify with `show etherchannel summary` (look for `RU` flag). Then `ping` across the channel and shut one member port — verify traffic continues on the remaining link.

3. **`ip routing` effect:** On a multilayer switch with `ip routing` disabled, assign an IP to a VLAN SVI. Try to ping another subnet. Observe the failure. Enable `ip routing` and retry. Document what changes in `show ip route`.

4. **HSRP priority tuning:** Change DSW-A1's HSRP priority for VLAN 10 from 105 to 90 (lower than default 100). Observe which switch becomes active. Restore 105 and verify preempt restores DSW-A1 to active.
