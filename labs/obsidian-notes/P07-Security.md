# P07 — Security (ACLs, Port Security, DHCP Snooping, DAI)

> [!NOTE] Part Summary
> **Topic:** Restrict inter-office traffic with an extended ACL, protect access ports with Port Security, and deploy DHCP Snooping + Dynamic ARP Inspection to prevent network attacks
> **NetBridge Scenario:** The network is functional but open — any PC in Office A can freely access Office B's servers, and nothing stops a rogue DHCP server or ARP poisoning attack. Part 7 locks this down: ACLs control inter-office traffic, Port Security limits which MACs can connect, and DHCP Snooping + DAI protect the switching fabric from common L2 attacks.
> **Key Concepts:** Extended ACLs, ACL placement, Port Security (sticky MAC), DHCP Snooping, DAI, trust ports
> **Devices involved:** DSW-A1, DSW-A2, DSW-B1, DSW-B2, ASW-A1, ASW-A2, ASW-A3, ASW-B1, ASW-B2, ASW-B3

---

## 🗺️ Big Picture

> [!TIP] Mental Model
> Think of Part 7 as the building's security system: ACLs are the access control policy (who can go where), Port Security is the door badge reader (only known MACs get in), DHCP Snooping is the fake-key detector (block rogue DHCP servers), and DAI is the identity check (block ARP spoofing).

```
ACL (extended, near source):
  Office A PC subnet → Office B: ICMP only; everything else denied
  Applied on BOTH DSW-A1 and DSW-A2 VLAN 10 SVIs (either could be HSRP active)

Port Security (access switches):
  Max MACs = minimum needed (1 or 2 per port)
  Violation = restrict (log + drop; don't shut port)
  Sticky MAC = auto-learn and save to config

DHCP Snooping:
  Enable per VLAN → trust only uplinks toward DHCP server → rate-limit untrusted

DAI:
  Enable per VLAN → trust same ports as DHCP Snooping → validate src-mac dst-mac ip
```

---

## Live Config Evidence (Harvested 2026-09-14)

> [!check] Live Verification — configs harvested 2026-09-14, evidence section added 2026-09-21
>
> ### ACLs — DSW-A1 and DSW-A2
>
> Both distribution switches have the `OfficeA_to_OfficeB` ACL defined and applied inbound on Vlan10. ✅
>
> **DSW-A1** (`ip access-group OfficeA_to_OfficeB in` on Vlan10):
> ```
> ip access-list extended OfficeA_to_OfficeB
>  permit icmp 10.1.0.0 0.0.0.255 10.3.0.0 0.0.0.255
>  deny   ip 10.1.0.0 0.0.0.255 10.3.0.0 0.0.0.255
>  permit ip any any
> ```
>
> **DSW-A2** — identical ACL, also applied `ip access-group OfficeA_to_OfficeB in` on Vlan10. ✅
>
> The live policy matches Office A VLAN 10 (`10.1.0.0/24`) to Office B VLAN 10 (`10.3.0.0/24`); use these current subnets rather than older example ranges.
>
> ---
>
> ### DHCP Snooping — ASW-A1, ASW-A2, ASW-A3
>
> All three Office A access switches have DHCP Snooping enabled on VLANs 10, 20, 40, 99 with `no ip dhcp snooping information option`. ✅
>
> **ASW-A1:**
> ```
> ip dhcp snooping vlan 10,20,40,99
> no ip dhcp snooping information option
> ip dhcp snooping
> ! Trusted uplinks:
> interface Ethernet0/0  → ip dhcp snooping trust  (uplink to DSW-A1)
> interface Ethernet0/1  → ip dhcp snooping trust  (uplink to DSW-A2)
> interface Ethernet1/1  → ip dhcp snooping trust  (additional trunk uplink)
> interface Ethernet0/2  → ip dhcp snooping limit rate 15  (WLC trunk — rate-limited)
> interface Ethernet0/2  → ip dhcp snooping trust  (WLC uplink also trusted)
> ```
>
> **ASW-A2:**
> ```
> ip dhcp snooping vlan 10,20,40,99
> no ip dhcp snooping information option
> ip dhcp snooping
> ! Trusted uplinks:
> interface Ethernet0/0  → ip dhcp snooping trust
> interface Ethernet0/1  → ip dhcp snooping trust
> interface Ethernet0/2  → ip dhcp snooping limit rate 15  (host-facing access port)
> ```
>
> **ASW-A3:**
> ```
> ip dhcp snooping vlan 10,20,40,99
> no ip dhcp snooping information option
> ip dhcp snooping
> ! Trusted uplinks:
> interface Ethernet0/0  → ip dhcp snooping trust
> interface Ethernet0/1  → ip dhcp snooping trust
> interface Ethernet0/2  → ip dhcp snooping limit rate 15  (host-facing access port)
> ```
>
> **⚠️ Note — VLAN 40:** Live configs include VLAN 40 in snooping scope. The note's planned config example shows VLANs 10,20,99 — the actual lab adds VLAN 40 (appears to be a wireless/additional data VLAN present in this topology).
>
> ---
>
> ### DAI — ASW-A1, ASW-A2, ASW-A3
>
> All three Office A access switches have DAI enabled on the same VLANs as DHCP Snooping, with `validate src-mac dst-mac ip`. ✅
>
> **All three ASW-A switches (identical DAI config):**
> ```
> ip arp inspection vlan 10,20,40,99
> ip arp inspection validate src-mac dst-mac ip
> ! Trusted uplinks (mirror DHCP Snooping trust):
> interface Ethernet0/0  → ip arp inspection trust
> interface Ethernet0/1  → ip arp inspection trust
> ! (ASW-A1 also trusts Et0/2, Et0/3, Et1/0, Et1/1)
> ```
>
> **⚠️ Deviation — validate order:** The note's planned config specifies `ip arp inspection validate dst-mac src-mac ip`. The live configs use `ip arp inspection validate src-mac dst-mac ip` (src-mac listed first). Both enable all three checks — the keyword order on this command doesn't affect behaviour; all three checks are active either way. ✅
>
> **⚠️ Deviation — ASW-A1 DAI trust scope:** ASW-A1 has `ip arp inspection trust` on nearly all interfaces including host-facing ports (Et0/3, Et1/0). This is broader than the intended design (trust only uplinks). Host-facing ports with DAI trust means ARP from hosts on those ports is not validated — potential gap worth reviewing.
>
> ---
>
> ### Port Security — ASW-A1, ASW-A2, ASW-A3
>
> Port security is partially deployed — not uniformly applied to all access ports as the plan describes.
>
> **ASW-A1** — port-security on Ethernet0/1 (trunk port) and partial on Ethernet0/2:
> ```
> interface Ethernet0/1   ! ← this is a trunk port — deviation
>  switchport port-security violation restrict
>  switchport port-security mac-address sticky
>  switchport port-security             ! no explicit maximum set (defaults to 1)
>
> interface Ethernet0/2   ! trunk to WLC
>  switchport port-security maximum 5
>  ! (no violation mode set — defaults to shutdown)
>  ! (no sticky — no mac-address sticky)
> ```
> **⚠️ Deviation:** Port-security on a trunk port (Et0/1) goes against the design principle (port-security should only be on access ports). Et0/2 has a maximum without violation mode — defaults to `shutdown`, not `restrict`. No port-security on the actual host-facing access ports (Et0/3, Et1/0).
>
> **ASW-A2** — port-security on Ethernet0/2 (access port VLAN 10 + voice VLAN 20): ✅
> ```
> interface Ethernet0/2
>  switchport access vlan 10
>  switchport voice vlan 20
>  switchport port-security violation restrict
>  switchport port-security mac-address sticky
>  switchport port-security mac-address sticky 0050.7966.6845   ! learned MAC saved
>  switchport port-security                                      ! max defaults to 1
> ```
> Violation mode: `restrict` ✅ | Sticky: enabled ✅ | One MAC learned (0050.7966.6845) ✅
>
> **ASW-A3** — port-security only on Ethernet0/3, which is `shutdown`:
> ```
> interface Ethernet0/3
>  switchport mode access
>  switchport port-security violation restrict
>  switchport port-security mac-address sticky
>  switchport port-security
>  shutdown                   ! port is administratively down
> ```
> **⚠️ Deviation:** Port-security is configured but the port is shut down, so it provides no active protection. The active host-facing port (Et0/2) has no port-security configured on ASW-A3.
>
> ---
>
> ### ASW-B1, ASW-B2, ASW-B3 — Office B Findings
>
> The current files contain distinct Office B access-switch configurations, so the previous capture warning is obsolete.
>
> - **ASW-B1:** DHCP Snooping and DAI cover VLANs 10, 20, 30, and 99; Ethernet0/0 and Ethernet0/1 are trusted uplinks. Ethernet0/2 has port security with `restrict` and sticky learning.
> - **ASW-B2:** Same snooping/DAI VLANs and trusted uplinks; Ethernet0/2 has port security with `restrict` and sticky learning. The configured hostname is `AWS-B2` (A/S transposed).
> - **ASW-B3:** Same snooping/DAI VLANs and trusted uplinks. Ethernet0/2 is a server-facing VLAN 30 port with voice VLAN 20, maximum five sticky MACs, and is also trusted for DAI. Trusting a host-facing port bypasses DAI validation and should be reviewed. Ethernet0/3 has port security with `restrict` and sticky learning but is shut down.
>
> These configs confirm command presence only; verify the snooping binding table, DAI counters, and actual host behavior on the running devices.
>
> ---
>
> ### Summary Table
>
> | Device | Port-Security | Violation Mode | DHCP Snooping VLANs | DAI VLANs | DAI Validate |
> |--------|--------------|----------------|----------------------|-----------|--------------|
> | ASW-A1 | Partial (trunk port + WLC trunk — not host ports) | restrict (Et0/1) / **shutdown default** (Et0/2) | 10,20,40,99 ✅ | 10,20,40,99 ✅ | src-mac dst-mac ip ✅ |
> | ASW-A2 | Et0/2 only (access port) ✅ | restrict ✅ | 10,20,40,99 ✅ | 10,20,40,99 ✅ | src-mac dst-mac ip ✅ |
> | ASW-A3 | Et0/3 only (shutdown port) ⚠️ | restrict | 10,20,40,99 ✅ | 10,20,40,99 ✅ | src-mac dst-mac ip ✅ |
> | ASW-B1 | Ethernet0/2 (restrict, sticky) | restrict | 10,20,30,99 ✅ | 10,20,30,99 ✅ | src-mac dst-mac ip ✅ |
> | ASW-B2 (`AWS-B2`) | Ethernet0/2 (restrict, sticky) | restrict | 10,20,30,99 ✅ | 10,20,30,99 ✅ | src-mac dst-mac ip ✅ |
> | ASW-B3 | Ethernet0/2 (max 5, sticky; default violation mode) and shut Ethernet0/3 | Mixed | 10,20,30,99 ✅ | 10,20,30,99 ✅ | src-mac dst-mac ip ✅; Et0/2 trusted |
> | DSW-A1 | N/A | N/A | N/A | N/A | ACL OfficeA_to_OfficeB on Vlan10 in ✅ |
> | DSW-A2 | N/A | N/A | N/A | N/A | ACL OfficeA_to_OfficeB on Vlan10 in ✅ |

---

## 📚 Sections

### Section 1 — Extended ACL: Inter-Office Traffic Control

> [!NOTE] Key Concept
> **Extended ACLs** filter on source IP, destination IP, and protocol/port. The cardinal rule: place extended ACLs **as close to the source as possible** — this blocks unwanted traffic early, saving bandwidth on transit links.

**Policy:**
- Office A PCs (VLAN 10) **can ping** Office B PCs (VLAN 10) — ICMP permitted
- Office A PCs **cannot access** Office B for anything else — everything else between the two offices denied
- All other traffic (internet, intra-office) is permitted normally

```
! === Create the extended ACL on DSW-A1 AND DSW-A2 ===
! (both must have it — either could be the HSRP active gateway)

ip access-list extended OfficeA_to_OfficeB
 permit icmp 10.1.0.0 0.0.0.255 10.3.0.0 0.0.0.255     ! allow ping A VLAN 10 → B VLAN 10
 deny ip 10.1.0.0 0.0.0.255 10.3.0.0 0.0.0.255         ! block other A VLAN 10 → B VLAN 10 traffic
 permit ip any any                                         ! permit everything else
 exit

! Apply to VLAN 10 SVI — inbound (traffic coming FROM PC subnet)
interface Vlan10
 ip access-group OfficeA_to_OfficeB in
 exit
```

**Why apply to BOTH DSW-A1 and DSW-A2:**
- HSRP determines which distribution switch is the active gateway for VLAN 10
- If DSW-A1 fails, DSW-A2 becomes active
- If the ACL is only on DSW-A1, traffic routed through DSW-A2 bypasses the policy
- **ACL must be on every possible active gateway** for that VLAN

**ACL placement rule:**
```
Extended ACL → as close to SOURCE as possible (saves bandwidth on transit links)
Standard ACL → as close to DESTINATION as possible (standard ACLs only match source IP)
```

> [!WARNING] Exam Flags 🎯
> - Extended ACL: filter by src IP + dst IP + protocol/port
> - Standard ACL: filter by src IP only
> - Implicit deny at end: if no `permit ip any any` at the end → all other traffic blocked!
> - `ip access-group X in` on the SVI = filter traffic ENTERING from that VLAN
> - `ip access-group X out` on the SVI = filter traffic LEAVING toward that VLAN

---

### Section 2 — Port Security

> [!NOTE] Key Concept
> **Port Security** limits which MAC addresses can communicate on a switchport. **Sticky learning** auto-populates the allowed MAC list and saves it to the running-config. Violation mode `restrict` logs and drops unauthorized traffic without shutting the port.

```
! === Apply on every access-switch host-facing port ===

! Single device port (PC only)
interface FastEthernet0/3
 switchport mode access
 switchport port-security
 switchport port-security maximum 1              ! only 1 MAC allowed
 switchport port-security violation restrict     ! log + drop (don't shutdown)
 switchport port-security mac-address sticky     ! learn and save MAC automatically
 exit

! Dual device port (PC + IP phone)
interface FastEthernet0/4
 switchport mode access
 switchport port-security
 switchport port-security maximum 2              ! PC + phone = 2 MACs
 switchport port-security violation restrict
 switchport port-security mac-address sticky
 exit
```

**Violation modes:**

| Mode | What Happens | Port Status |
|---|---|---|
| `protect` | Drop bad frames silently | Still up |
| `restrict` | Drop bad frames + log + increment counter | Still up |
| `shutdown` | Err-disable the port | Err-disabled (requires manual recovery) |

> [!WARNING] Exam Flags 🎯
> - Default violation mode is `shutdown` — changes to `restrict` explicitly
> - Sticky MACs are saved to running-config (`write memory` to persist)
> - `show port-security interface Fa0/3` shows learned MACs and violation counts
> - Port security only works on **access ports** — not on trunk ports

---

### Section 3 — DHCP Snooping

> [!NOTE] Key Concept
> **DHCP Snooping** inspects DHCP messages and builds a **binding table** (MAC → IP → port → VLAN). It blocks DHCP offers from untrusted ports (only uplinks toward the real DHCP server are trusted), preventing rogue DHCP servers from assigning bad IPs.

```
! === Apply on every access switch — per VLAN ===

! Step 1: Enable DHCP Snooping globally
ip dhcp snooping

! Step 2: Enable per VLAN (must match VLANs active on this switch)
ip dhcp snooping vlan 10,20,99     ! Office A access switch

! Step 3: Disable option 82 (CRITICAL — without this, DHCP silently breaks)
no ip dhcp snooping information option

! Step 4: Trust the uplinks toward the distribution switches (toward DHCP server)
interface GigabitEthernet0/1
 ip dhcp snooping trust    ! uplink to DSW-A1
 exit

interface GigabitEthernet0/2
 ip dhcp snooping trust    ! uplink to DSW-A2
 exit

! Step 5: Rate-limit untrusted ports (host-facing ports)
interface range FastEthernet0/1 - 10
 ip dhcp snooping limit rate 15    ! max 15 DHCP packets per second
 exit

! WLC uplink — higher rate limit (legitimate DHCP traffic from many wireless clients)
interface GigabitEthernet0/3
 ip dhcp snooping limit rate 100
 exit
```

> [!WARNING] Critical Gotcha — option 82
> `no ip dhcp snooping information option` **must** be configured. Option 82 (DHCP relay agent information) is inserted by snooping-enabled switches into DHCP packets. When these packets reach R1 (which isn't expecting option 82), it silently drops them. The result: DHCP requests disappear without any error message. Always disable option 82 insertion.

> [!WARNING] Exam Flags 🎯
> - DHCP Snooping builds the **binding table** used by DAI (Part 7.4)
> - Trusted ports: only uplinks toward the real DHCP server — never host-facing ports
> - `show ip dhcp snooping binding` — verify binding table populated after DHCP works
> - `show ip dhcp snooping` — verify enabled VLANs and trusted ports

---

### Section 4 — Dynamic ARP Inspection (DAI)

> [!NOTE] Key Concept
> **DAI** validates ARP packets against the DHCP Snooping binding table — if a device claims an IP/MAC combination not in the table, the ARP packet is dropped. This blocks **ARP poisoning** (a man-in-the-middle attack where an attacker sends fake ARP replies to redirect traffic through their device).

```
! === Apply on every access switch — per VLAN ===

! Enable DAI per VLAN (no global on/off — only per-VLAN)
ip arp inspection vlan 10,20,99     ! same VLANs as DHCP Snooping

! Optional: enable additional ARP validation checks
ip arp inspection validate dst-mac src-mac ip

! Trust the same uplinks as DHCP Snooping (DAI uses the same trust concept)
interface GigabitEthernet0/1
 ip arp inspection trust    ! uplink to DSW-A1
 exit

interface GigabitEthernet0/2
 ip arp inspection trust    ! uplink to DSW-A2
 exit
```

**What DAI validates:**
- **dst-mac** — ARP reply's destination MAC matches the Ethernet header
- **src-mac** — ARP sender MAC matches the Ethernet header source
- **ip** — ARP request/reply doesn't contain 0.0.0.0, 255.255.255.255, or other invalid IPs

> [!WARNING] Exam Flags 🎯
> - DAI depends on the DHCP Snooping binding table — configure DHCP Snooping first
> - For static IPs (servers, switches), add manual **ARP ACL entries** so DAI doesn't block them (they won't appear in the DHCP binding table since they don't use DHCP)
> - `show ip arp inspection` — shows forwarded/dropped ARP counts per VLAN
> - Trust the same ports for DAI as DHCP Snooping — configuration should mirror exactly

---

## 🖥️ NetBridge Applied — Full Config Block

> [!TIP] DSW-A1 — Extended ACL Configuration

```
! === DSW-A1 — Extended ACL (also configure identically on DSW-A2) ===

ip access-list extended OfficeA_to_OfficeB
 permit icmp 10.1.0.0 0.0.0.255 10.3.0.0 0.0.0.255
 deny ip 10.1.0.0 0.0.0.255 10.3.0.0 0.0.0.255
 permit ip any any
 exit

interface Vlan10
 ip access-group OfficeA_to_OfficeB in
 exit

write memory
```

> [!TIP] ASW-A1 — Port Security + DHCP Snooping + DAI

```
! === ASW-A1 — Complete Part 7 Configuration ===

! Port Security
interface range FastEthernet0/1 - 8
 switchport port-security
 switchport port-security maximum 2
 switchport port-security violation restrict
 switchport port-security mac-address sticky
 exit

! DHCP Snooping
ip dhcp snooping
ip dhcp snooping vlan 10,20,99
no ip dhcp snooping information option

interface GigabitEthernet0/1
 ip dhcp snooping trust
 exit
interface GigabitEthernet0/2
 ip dhcp snooping trust
 exit

interface range FastEthernet0/1 - 8
 ip dhcp snooping limit rate 15
 exit

! DAI
ip arp inspection vlan 10,20,99
ip arp inspection validate dst-mac src-mac ip

interface GigabitEthernet0/1
 ip arp inspection trust
 exit
interface GigabitEthernet0/2
 ip arp inspection trust
 exit

write memory
```

---

## ✅ Verification Commands

| Command | What to Look For |
|---|---|
| `show ip access-lists OfficeA_to_OfficeB` | Hit counts incrementing on permit/deny entries |
| `show ip interface Vlan10` | ACL name appears under "Inbound access list" |
| `show port-security interface Fa0/3` | Learned MACs, violation count, status |
| `show port-security` | Summary of all port security configs |
| `show ip dhcp snooping` | Enabled VLANs, trusted ports listed |
| `show ip dhcp snooping binding` | DHCP leases showing as snooped entries |
| `show ip arp inspection` | Forwarded/dropped ARP counts per VLAN |
| `show ip arp inspection interfaces` | Trust status per interface |

---

## ⚠️ Common Pitfalls

> [!WARNING] Watch Out
> - **ACL only on one distribution switch** — if HSRP fails over to the other switch, traffic bypasses the ACL; apply on both DSW-A1 and DSW-A2
> - **Missing `permit ip any any`** — ACL has implicit deny at end; without this, all non-ICMP traffic (HTTP, SSH, etc.) is blocked even within the same office
> - **`no ip dhcp snooping information option` forgotten** — DHCP silently breaks; this is the #1 DHCP Snooping gotcha
> - **DAI configured without DHCP Snooping** — DAI's binding table comes from DHCP Snooping; no snooping = no binding table = DAI drops all ARP packets
> - **Wrong trust port direction** — trust the uplinks toward the DHCP server/distribution switches; never trust host-facing ports
> - **Port security on trunk port** — port security only works on access ports; applying to trunks causes issues

---

## 📊 Concepts Summary

| Concept | What It Does | Exam Tip |
|---|---|---|
| Extended ACL | Filter on src IP + dst IP + protocol/port | Apply near source; standard ACL apply near dest |
| `permit icmp` | Allow ICMP (ping) between specified subnets | Only permits ping — not HTTP, SSH, etc. |
| `permit ip any any` | Allow all other traffic | Required to avoid implicit deny blocking everything |
| `ip access-group X in` | Apply ACL to interface for inbound traffic | `in` = from that VLAN; `out` = toward that VLAN |
| Port Security | Limit MACs allowed on an access port | Default violation = shutdown; use restrict in lab |
| Sticky MAC | Auto-learn + save MAC to config | `mac-address sticky` — saved to running-config |
| Violation restrict | Log + drop bad frames; keep port up | Use when you don't want ports to err-disable |
| DHCP Snooping | Block rogue DHCP servers; build binding table | `no ip dhcp snooping information option` is critical |
| Trusted port | Port allowed to send DHCP offers/ARP | Uplinks toward real DHCP server only |
| option 82 | DHCP relay agent info — disable it | Without `no ip dhcp snooping information option` DHCP breaks |
| DAI | Validate ARP vs DHCP Snooping binding table | Enable per-VLAN; trust same ports as snooping |
| ARP poisoning | Attacker sends fake ARP to redirect traffic | DAI prevents this |

---

## 🛠️ Practice Tasks

> [!CAUTION] Practice safely
> ACL, DHCP Snooping, and DAI experiments can block management or host traffic. Use an isolated copy or agreed change window, confirm console/recovery access, and restore the known-good config after testing.

1. **ACL testing:** Configure the OfficeA_to_OfficeB ACL on DSW-A1. From an Office A PC, ping an Office B PC — should succeed. Try HTTP to an Office B server — should fail. Check `show ip access-lists` hit counts to confirm the ACL is working.

2. **Port security violation:** Enable port security (max 2, restrict) with sticky on an access port. Connect a device — verify its MAC is learned. Connect a third device — verify it's blocked but port stays up. Check `show port-security interface` for violation count.

3. **DHCP Snooping rogue server:** Set up a rogue DHCP server on a host-facing port. Verify hosts get IPs from the rogue server when snooping is disabled. Enable DHCP Snooping — verify the rogue offers are now blocked and hosts only get IPs from R1.

4. **ARP poisoning detection:** Without DAI, use `arp -s` on an attacker to send a fake ARP reply. Verify victim's ARP table shows the wrong MAC. Enable DAI — verify the fake ARP is dropped and `show ip arp inspection` shows dropped count incrementing.
