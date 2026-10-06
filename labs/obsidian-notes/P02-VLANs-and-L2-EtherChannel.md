# P02 — VLANs & Layer-2 EtherChannel

> [!NOTE] Part Summary
> **Topic:** Bond redundant switch links and propagate VLANs cleanly across the access/distribution layers
> **NetBridge Scenario:** The client's offices each have dual distribution switches for redundancy. Part 2 bonds selected links into EtherChannels, configures trunks, and assigns ports to VLANs. VTP is an optional concept example; it is not explicitly configured in the harvested lab. Inter-office reachability depends on routing and policy, not VLAN separation alone.
> **Key Concepts:** EtherChannel (PAgP vs LACP), trunking, DTP, native VLAN security, VTP, VLAN assignment, PortFast/BPDU Guard on access ports
> **Devices involved:** DSW-A1, DSW-A2, DSW-B1, DSW-B2, ASW-A1, ASW-A2, ASW-A3, ASW-B1, ASW-B2, ASW-B3

> [!IMPORTANT] How to use the examples
> The harvested configs confirm the VLANs, trunks, native VLAN 1000, PAgP on the Office A distribution pair, and LACP on the Office B pair. They do **not** contain explicit VTP configuration. The commands below are teaching examples; interface names and VLAN purposes must be checked against the live configs before use.
> The trunks specify native VLAN ID 1000, but the harvested configs do not show an explicit VLAN 1000 database entry. Check `show vlan brief` on the running switches before describing that VLAN as active.

---

## 🗺️ Big Picture

> [!TIP] Mental Model
> Think of Part 2 as building the roads before adding traffic lights (STP) or directions (routing). EtherChannels bundle links; VLANs separate Layer 2 broadcast domains. VTP is an optional VLAN-database distribution protocol, not a live dependency in this lab.

```
Office A:                          Office B:
DSW-A1 ══ PAgP ══ DSW-A2          DSW-B1 ══ LACP ══ DSW-B2
   ↕ trunk             ↕ trunk        ↕ trunk            ↕ trunk
ASW-A1  ASW-A2  ASW-A3             ASW-B1  ASW-B2

Office A: VLAN 10 (user/data), 20 (voice/staff), 40 (wireless clients), 99 (network management)
Office B: VLAN 10 (user/data), 20 (voice/staff), 30 (servers/staff), 99 (network management)
```

VLAN IDs are scoped locally to each Layer 2 site; VLAN 10 in Office A and VLAN 10 in Office B are separate subnets. The topology also labels VLAN 999 as a parking VLAN, but VLAN 999 is not confirmed in the harvested switch configs.

> [!cross-ref] Cross-Reference
> → **[P03-IP-Addressing-L3-EtherChannel-HSRP](./P03-IP-Addressing-L3-EtherChannel-HSRP.md):** SVIs for each VLAN are configured in Part 3
> → **[P04-Rapid-Spanning-Tree](./P04-Rapid-Spanning-Tree.md):** STP root alignment with HSRP active router done in Part 4

---

## 📚 Sections

### Section 1 — EtherChannel: PAgP (Office A) and LACP (Office B)

> [!NOTE] Key Concept
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

> [!WARNING] Exam Flags 🎯
> - PAgP: **desirable-desirable** or **desirable-auto** forms a channel; **auto-auto** does NOT
> - LACP: **active-active** or **active-passive** forms a channel; **passive-passive** does NOT
> - `on` mode: forces EtherChannel with no negotiation — both sides must use `on`; never mix `on` with PAgP/LACP modes

---

### Section 2 — Trunk Configuration on All Inter-Switch Links

> [!NOTE] Key Concept
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

**`switchport trunk native vlan 1000` — configured native VLAN ID:**
- The **native VLAN** carries untagged frames on a trunk
- If two trunks share the same native VLAN, an attacker can inject frames that "hop" between VLANs
- Using a dedicated, otherwise-unused native VLAN reduces accidental exposure; it does not by itself eliminate VLAN-hopping risks. Keep trunk configuration consistent at both ends and use other layer-2 protections as appropriate.

> [!WARNING] Exam Flags 🎯
> - Native VLAN mismatch between two trunk ends → CDP warning; traffic issues — both ends must match
> - VLAN 1 is the default native VLAN — always change it
> - `allowed vlan` list only — unlisted VLANs are pruned from the trunk; don't forget to include Management VLAN 99

---

### Section 3 — VTP (VLAN Trunking Protocol)

> [!NOTE] Learning concept — not configured in the harvested lab
> **VTP** can distribute VLAN database changes among switches in a VTP domain. This lab's harvested configs do not show explicit VTP domain, version, or server/client configuration. Do not assume VLANs are being synchronized by VTP; verify the VLAN database and trunks directly.

```
! === VTP Server (one per office — e.g. DSW-A1 for Office A) ===
vtp mode server
vtp domain <lab-domain>
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
vtp domain <lab-domain>
vtp version 2
! VLANs propagate automatically — do NOT create VLANs on clients
```

**VLAN reference table:**

| VLAN | Name | Office A | Office B |
|---|---|---|---|
| 10 | User/data | ✅ (`10.1.0.0/24`) | ✅ (`10.3.0.0/24`) |
| 20 | Voice/staff | ✅ (`10.2.0.0/24`) | ✅ (`10.4.0.0/24`) |
| 30 | Servers/staff | — | ✅ (`10.5.0.0/24`) |
| 40 | Wireless clients | ✅ (`10.6.0.0/24`) | — |
| 99 | Network management | ✅ (`10.0.0.0/28`) | ✅ (`10.0.0.16/28`) |
| 999 | Parking VLAN (topology label) | Not confirmed in harvested configs | Not confirmed in harvested configs |
| 1000 | Configured native VLAN ID; VLAN database presence unverified | ✅ (trunk setting) | ✅ (trunk setting) |

> [!WARNING] VTP Gotcha 🎯
> VTP revision numbers can cause unexpected VLAN database changes when switches join a domain. Before connecting a switch to a VTP domain, verify its mode, domain, version, and revision; use transparent/off mode when centralized VLAN propagation is not required.

---

### Section 4 — Access Port Configuration

> [!NOTE] Key Concept
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

> [!NOTE] Key Concept
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

## 🧪 Example Configuration Templates

> [!NOTE]
> These command blocks are practice templates, not harvested configs. In particular, do not configure VTP unless you have deliberately selected and verified a VTP design for an isolated exercise.

> [!TIP] DSW-A1 — Complete Part 2 Configuration

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
vtp domain <lab-domain>
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

> [!TIP] ASW-A1 — Complete Part 2 Configuration

```
! === ASW-A1 — Access Switch ===

! Step 1: VTP client
vtp mode client
vtp domain <lab-domain>
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
| `show vlan brief` | Required VLANs exist locally and match the site plan |
| `show vtp status` | Check only when VTP is intentionally configured for an exercise |
| `show interfaces status` | Unused ports showing `disabled`; access ports showing correct VLAN |
| `show spanning-tree vlan 10` | Port-channel shows as trunk |

---

## ⚠️ Common Pitfalls

> [!WARNING] Watch Out
> - **`desirable-auto` works; `auto-auto` doesn't** — one side must be active/desirable
> - **Forgetting `switchport nonegotiate`** — DTP still runs even in trunk mode without it; could be exploited
> - **Native VLAN mismatch** — both sides of a trunk must have the same native VLAN or CDP alerts and VLAN tagging breaks
> - **Assuming VTP is active** — verify the domain, mode, and version on every switch; the harvested lab configs do not show explicit VTP setup
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
| VLAN hopping | Attack exploiting trunk/native-VLAN behavior | A dedicated native VLAN is one mitigation; it is not a complete fix |
| VTP | Optional VLAN database distribution protocol | Not explicitly configured in the harvested lab |
| VTP revision number | Helps determine which database update is newer | Check mode/domain/revision before joining a domain |
| Access port | Single VLAN, untagged | End devices connect here |
| Voice VLAN | Separate VLAN for IP phones on same port | `switchport voice vlan 20` |

---

## 🛠️ Practice Tasks

1. **EtherChannel negotiation matrix:** Draw a 3×3 grid with `on/desirable/auto` (PAgP) on each axis. Fill in whether each combination forms a channel. Repeat for LACP with `on/active/passive`.

2. **VLAN hopping demo:** Configure two switches with matching native VLAN 1. Attempt to send an 802.1Q-tagged frame with VLAN 10 across the trunk — observe how it's treated. Then change native VLAN to 1000 and verify the attack no longer works.

3. **VTP revision reset:** Take a switch configured as VTP client in domain "OldDomain" with revision 50. Add it to your lab. What happens to your VLAN database? How do you prevent this? Reset the revision number and re-add safely.

4. **Allowed VLAN troubleshooting:** Remove VLAN 99 from the allowed list on one trunk. Try to ping the Management SVI from that VLAN. Observe the failure. Re-add VLAN 99 and verify connectivity restores.
