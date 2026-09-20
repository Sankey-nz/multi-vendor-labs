---
title: "P04 — Rapid Spanning Tree (RSTP)"
created: 2025-01-01
updated: 2025-01-01
tags:
  - ccna
  - netbridge
  - networking
  - spanning-tree
  - rstp
  - portfast
  - bpdu-guard
  - stp-priority
part: 4
topic: Rapid Spanning Tree (RSTP)
status: reviewed
lab: CCNA Mega Lab
source: CCNA_Mega_Lab_Step_By_Step_Guide.md
---

# P04 — Rapid Spanning Tree (RSTP)

> [!info] Part Summary
> **Topic:** Switch from classic PVST+ to Rapid PVST+, align STP root with HSRP active router, and protect end-host ports with PortFast + BPDU Guard
> **NetBridge Scenario:** Classic STP has 30–50 second convergence times — unacceptable when a link fails. NetBridge upgrades all switches to Rapid PVST+ for sub-second convergence, then aligns STP root placement with the HSRP active router so traffic takes the most efficient path to its L3 gateway.
> **Key Concepts:** Rapid PVST+, STP root election, priority values (multiples of 4096), PortFast, BPDU Guard, STP/HSRP alignment
> **Devices involved:** DSW-A1, DSW-A2, DSW-B1, DSW-B2, ASW-A1, ASW-A2, ASW-A3, ASW-B1, ASW-B2

---

## 🗺️ Big Picture

> [!tip] Mental Model
> STP prevents loops by blocking redundant links. The root bridge is the "centre of the tree" — all traffic flows toward it. If the STP root and HSRP active are on different switches, traffic takes a detour: hosts send to the HSRP gateway (DSW-A1) but STP forces traffic through DSW-A2 first. Aligning them eliminates the detour.

```
BAD — STP root ≠ HSRP active:
Host → STP forces frame to DSW-A2 (root) → DSW-A2 forwards to DSW-A1 (HSRP active) → router
                                                ↑ suboptimal hop

GOOD — STP root = HSRP active (same switch):
Host → DSW-A1 directly (STP root AND HSRP active) → router
                ↑ optimal — one hop
```

> [!cross-ref] Cross-Reference
> → **[[P03-IP-Addressing-L3-EtherChannel-HSRP]]:** HSRP active roles set in Part 3 — STP root must match
> → **[[P02-VLANs-and-L2-EtherChannel]]:** VLANs and trunk ports from Part 2 are the STP topology

---

## 📚 Sections

### Section 1 — Enable Rapid PVST+

> [!note] Key Concept
> The default STP mode in Packet Tracer is classic **PVST+** (802.1D per-VLAN). **Rapid PVST+** (802.1w per-VLAN) converges in under a second using new port roles and states instead of waiting through the 15-second Listening + Learning timers.

**Verify the current mode first:**
```
show spanning-tree
! Look for:
! "Spanning tree enabled protocol ieee"   → classic PVST+ (default, SLOW)
! "Spanning tree enabled protocol rstp"   → Rapid PVST+ (what we want)
```

**Switch all access and distribution switches to Rapid PVST+:**
```
! Apply to: ASW-A1, ASW-A2, ASW-A3, ASW-B1, ASW-B2, DSW-A1, DSW-A2, DSW-B1, DSW-B2
spanning-tree mode rapid-pvst
```

**Classic PVST+ vs. Rapid PVST+:**

| Feature | Classic PVST+ (802.1D) | Rapid PVST+ (802.1w) |
|---|---|---|
| Convergence | 30–50 seconds | < 1 second |
| Port states | Blocking/Listening/Learning/Forwarding/Disabled | Discarding/Learning/Forwarding |
| BPDUs | Only root sends; others relay | Every switch sends its own BPDUs |
| Link types | All shared | Point-to-point (full-duplex) |

---

### Section 2 — STP Root Election and Priority

> [!note] Key Concept
> The **root bridge** is elected by lowest **Bridge ID** = Priority + MAC address. Priority is configured in increments of **4096** (STP only accepts multiples of 4096). Setting priority 0 guarantees root; 4096 guarantees backup root.

**Priority values:**

| Priority | Meaning |
|---|---|
| 0 | Guaranteed root bridge for this VLAN |
| 4096 | Backup root (second lowest) |
| 8192 | Third lowest |
| 32768 | Default (if not configured) |

```
! === DSW-A1 — STP Root for VLANs 10 and 99 (matches HSRP active) ===
spanning-tree vlan 10 priority 0
spanning-tree vlan 99 priority 0

! === DSW-A1 — STP Backup Root for VLANs 20 and 40 (HSRP standby) ===
spanning-tree vlan 20 priority 4096
spanning-tree vlan 40 priority 4096


! === DSW-A2 — STP Root for VLANs 20 and 40 (matches HSRP active) ===
spanning-tree vlan 20 priority 0
spanning-tree vlan 40 priority 0

! === DSW-A2 — STP Backup Root for VLANs 10 and 99 (HSRP standby) ===
spanning-tree vlan 10 priority 4096
spanning-tree vlan 99 priority 4096
```

**STP/HSRP alignment table for Office A:**

| VLAN | HSRP Active | STP Root | HSRP Standby | STP Backup Root |
|---|---|---|---|---|
| 10 (Mgmt) | DSW-A1 | DSW-A1 (priority 0) | DSW-A2 | DSW-A2 (priority 4096) |
| 20 (Staff) | DSW-A2 | DSW-A2 (priority 0) | DSW-A1 | DSW-A1 (priority 4096) |
| 40 (Servers) | DSW-A2 | DSW-A2 (priority 0) | DSW-A1 | DSW-A1 (priority 4096) |
| 99 (Mgmt) | DSW-A1 | DSW-A1 (priority 0) | DSW-A2 | DSW-A2 (priority 4096) |

> [!warning] Exam Flags 🎯
> - STP priority MUST be a multiple of 4096 — any other value is rejected with an error
> - Priority 0 = lowest possible = always wins root election (unless another switch also has 0, then MAC breaks the tie)
> - `spanning-tree vlan X root primary` is a macro that automatically sets priority to 24576 (or lower if needed) — less precise than setting 0 explicitly

---

### Section 3 — PortFast on Access Ports

> [!note] Key Concept
> **PortFast** skips the Listening and Learning states on a port — it goes directly to Forwarding. This is safe on ports connected to end devices (PCs, phones) because they can never create a loop.

**Without PortFast:** PC connects → port waits 30 seconds (Listening 15s + Learning 15s) → then forwards. DHCP requests during this time are dropped — host gets no IP.

**With PortFast:** PC connects → port forwards immediately → DHCP works instantly.

```
! On every access port facing an end host (PC, phone, printer, server)
interface range FastEthernet0/1 - 10
 spanning-tree portfast
 exit

! On the WLC uplink (which is a trunk, not an access port)
interface GigabitEthernet0/1
 spanning-tree portfast trunk
 exit
```

> [!warning] PortFast on Trunks
> Normally PortFast is for access ports only. The WLC uplink is a trunk but it connects to a WLC (not another switch) — so PortFast is safe and necessary. Use `spanning-tree portfast trunk` for trunk ports that face non-switch devices.

---

### Section 4 — BPDU Guard

> [!note] Key Concept
> **BPDU Guard** shuts a PortFast-enabled port immediately if it receives a **BPDU** (Bridge Protocol Data Unit — the STP control packet). A PortFast port receiving a BPDU means someone plugged in a switch, which could create a loop.

```
! Enable BPDU Guard on every PortFast port
interface range FastEthernet0/1 - 10
 spanning-tree portfast
 spanning-tree bpduguard enable
 exit

! OR enable globally for all PortFast ports at once
spanning-tree portfast bpduguard default
```

**What happens when BPDU Guard triggers:**
1. BPDU received on a PortFast port
2. Port immediately goes to **err-disabled** state
3. Port LED goes amber; traffic stops
4. Admin intervention required to restore: `no shutdown` after fixing the cause

```
! Recover an err-disabled port (after removing the rogue switch)
interface FastEthernet0/3
 shutdown
 no shutdown
 exit

! OR configure automatic recovery (not best practice in production):
errdisable recovery cause bpduguard
errdisable recovery interval 30
```

> [!warning] Exam Flags 🎯
> - BPDU Guard + PortFast is the standard combination for all host-facing ports
> - An err-disabled port shows `err-disabled` in `show interfaces status`
> - BPDU Guard does NOT protect against physical loops without PortFast — it only fires on PortFast-enabled ports

---

## 🖥️ NetBridge Applied — Full Config Block

> [!example] ASW-A1 — Complete Part 4 Configuration

```
! === ASW-A1 — Rapid PVST + PortFast + BPDU Guard ===

! Step 1: Enable Rapid PVST+
spanning-tree mode rapid-pvst

! Step 2: PortFast + BPDU Guard on all host-facing ports
interface range FastEthernet0/1 - 10
 spanning-tree portfast
 spanning-tree bpduguard enable
 exit

! WLC uplink (trunk to non-switch device)
interface GigabitEthernet0/3
 spanning-tree portfast trunk
 spanning-tree bpduguard enable
 exit

write memory
```

> [!example] DSW-A1 — Complete Part 4 Configuration

```
! === DSW-A1 — Rapid PVST + STP Root ===

! Step 1: Enable Rapid PVST+
spanning-tree mode rapid-pvst

! Step 2: STP Root for VLANs where DSW-A1 is HSRP Active
spanning-tree vlan 10 priority 0
spanning-tree vlan 99 priority 0

! Step 3: STP Backup Root for VLANs where DSW-A1 is HSRP Standby
spanning-tree vlan 20 priority 4096
spanning-tree vlan 40 priority 4096

write memory
```

---

## ✅ Verification Commands

| Command | What to Look For |
|---|---|
| `show spanning-tree` | `Spanning tree enabled protocol rstp` (not `ieee`) |
| `show spanning-tree vlan 10` | DSW-A1 shows `This bridge is the root` for VLAN 10 |
| `show spanning-tree vlan 10 \| include Priority` | Priority 0 (or 4096 for backup) |
| `show interfaces status` | PortFast ports showing `connected` immediately after cable plug |
| `show spanning-tree interface Fa0/1 detail` | `The port is in the portfast mode` |
| `show errdisable recovery` | Lists err-disabled ports and recovery settings |

---

## ⚠️ Common Pitfalls

> [!warning] Watch Out
> - **`show spanning-tree` shows `ieee`** — still on classic PVST+; forgot `spanning-tree mode rapid-pvst`
> - **STP root ≠ HSRP active** — causes suboptimal traffic paths; always align the two per VLAN
> - **Priority not a multiple of 4096** — IOS rejects invalid values with an error message
> - **PortFast on inter-switch trunk links** — never use PortFast between switches; only on host-facing ports
> - **Forgetting BPDU Guard after PortFast** — PortFast alone is incomplete; without BPDU Guard, an unauthorized switch can plug in and disrupt STP without any automatic protection
> - **Not recovering err-disabled ports** — after removing a rogue switch, the port stays err-disabled until manually shut/no-shut

---

## 📊 Concepts Summary

| Concept | What It Does | Exam Tip |
|---|---|---|
| Rapid PVST+ | Per-VLAN STP with sub-second convergence | `spanning-tree mode rapid-pvst`; verify with `show spanning-tree` |
| Root bridge | Switch elected as centre of STP topology | Lowest Bridge Priority + MAC wins |
| `priority 0` | Guarantees root bridge election | Must be multiple of 4096 |
| `priority 4096` | Guarantees backup root | One increment above 0 |
| STP/HSRP alignment | Same switch is STP root and HSRP active per VLAN | Prevents suboptimal traffic paths |
| PortFast | Skip Listening/Learning → instant forwarding | Only on host-facing ports; never on switch-to-switch links |
| `portfast trunk` | PortFast on a trunk port facing a non-switch | Used on WLC uplink |
| BPDU Guard | Err-disable port if BPDU received | Protects PortFast ports from rogue switches |
| err-disabled | Port shut down by BPDU Guard (or other violation) | Recover with `shutdown` + `no shutdown` |

---

## 🛠️ Practice Tasks

1. **STP mode verification:** Before changing anything, run `show spanning-tree` on an access switch. Identify the mode (look for `ieee` = PVST+ or `rstp` = Rapid PVST+). Change to Rapid PVST+ and verify the output changes.

2. **Root bridge alignment:** Configure DSW-A1 as STP root for VLAN 10 (priority 0) and DSW-A2 as backup root (priority 4096). Run `show spanning-tree vlan 10` on both. Identify which shows "This bridge is the root." Verify the root port on access switches points toward DSW-A1.

3. **BPDU Guard simulation:** Enable PortFast + BPDU Guard on an access port. Connect another switch to that port. Observe the port go err-disabled. Check `show interfaces status` for the `err-disabled` state. Remove the rogue switch and recover the port.

4. **PortFast DHCP test:** On a PC connected to a non-PortFast port, capture the time from cable connect to DHCP IP assignment (typically 30+ seconds). Enable PortFast on that port and repeat — verify DHCP completes in under 2 seconds.
