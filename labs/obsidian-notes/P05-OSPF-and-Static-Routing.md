# P05 — OSPF & Static Routing

> [!NOTE] Part Summary
> **Topic:** Study OSPF Area 0, default-route advertisement, and static-route failover concepts
> **NetBridge Scenario:** VLANs have IPs and gateways — routing connects subnets and provides a path upstream. The live lab uses OSPF Area 0 and advertises a default route; R1's IPv4 default is learned by DHCP, while static-route failover is a separate practice concept.
> **Key Concepts:** OSPF process, Area 0, router ID, `network` command, passive interfaces, `network-type point-to-point`, default route, `default-information originate`, floating static route, AD
> **Devices involved:** R1, CSW1, CSW2, DSW-A1, DSW-A2, DSW-B1, DSW-B2

> [!IMPORTANT] Current lab versus lesson example
> OSPF Area 0 and `default-information originate` are present in the harvested configs. R1's **IPv4** default route is learned through DHCP on Gi0/3; there is no IPv4 static/floating default route in the captured config. The static-route sections below are standalone learning examples, not a description of the live IPv4 failover setup. The live lab does have primary and floating **IPv6** defaults; see [P08](./P08-IPv6.md).

---

## 🗺️ Big Picture

> [!TIP] Mental Model
> OSPF is the "GPS system" — it discovers routes and shares them across the network. Static routes are manually configured paths. A floating static can serve as a backup in a design that uses static routes; R1's live IPv4 default in this lab is learned through DHCP, not a floating static.

```
Internet
   ↕ Upstream via Gi0/3 (IPv4 address/default route learned by DHCP)
         R1 (OSPF ASBR — default-information originate)
              ↕ OSPF Area 0
         CSW1 ══ CSW2
              ↕ OSPF Area 0
    DSW-A1/A2          DSW-B1/B2
         ↕ OSPF                 ↕ OSPF
    (SVIs advertised)      (SVIs advertised)
```

> [!cross-ref] Cross-Reference
> → **[P03-IP-Addressing-L3-EtherChannel-HSRP](./P03-IP-Addressing-L3-EtherChannel-HSRP.md):** All L3 interfaces configured in Part 3 are activated for OSPF here
> → **[P06-Network-Services](./P06-Network-Services.md):** DHCP relay (`ip helper-address`) uses R1's loopback — which OSPF makes reachable

---

## 📚 Sections

### Section 1 — OSPF Basic Configuration (All L3 Devices)

> [!NOTE] Key Concept
> **OSPF** (Open Shortest Path First) is a **link-state** routing protocol — every router builds a complete map of the network (LSDB) and independently runs Dijkstra's algorithm to find the best path. Process number is **locally significant** (doesn't need to match between devices).

```
! === R1 — live config uses interface-level OSPF activation ===
router ospf 1
 router-id 10.0.0.76
 passive-interface Loopback0
 default-information originate
 exit

interface Loopback0
 ip ospf 1 area 0
 exit

interface GigabitEthernet0/0
 ip ospf network point-to-point
 ip ospf 1 area 0
 exit

interface GigabitEthernet0/1
 ip ospf network point-to-point
 ip ospf 1 area 0
 exit

! === CSW1 ===
router ospf 1
 router-id 10.0.0.77
 network 10.0.0.34 0.0.0.0 area 0    ! uplink to R1
 network 10.0.0.41 0.0.0.0 area 0    ! Port-channel1 to CSW2
 network 10.0.0.77 0.0.0.0 area 0    ! loopback0
 network 10.0.0.46 0.0.0.0 area 0    ! downlink to DSW-A1
 network 10.0.0.54 0.0.0.0 area 0    ! downlink to DSW-B1
 passive-interface Loopback0
 exit


! === DSW-A1 ===
router ospf 1
 router-id 10.0.0.79
 network 10.0.0.79 0.0.0.0 area 0    ! loopback0
 network 10.0.0.46 0.0.0.0 area 0    ! uplink to CSW1
 network 10.0.0.62 0.0.0.0 area 0    ! uplink to CSW2
 network 10.1.0.2 0.0.0.0 area 0     ! VLAN 10 SVI
 network 10.2.0.2 0.0.0.0 area 0     ! VLAN 20 SVI
 network 10.6.0.2 0.0.0.0 area 0     ! VLAN 40 SVI
 network 10.0.0.2 0.0.0.0 area 0     ! VLAN 99 SVI
 passive-interface Loopback0
 passive-interface Vlan10             ! hosts can't be OSPF neighbors
 passive-interface Vlan20
 passive-interface Vlan40
 ! VLAN 99 is not passive in the harvested DSW-A1 config.
 exit
```

---

### Section 2 — Passive Interfaces

> [!NOTE] Key Concept
> **Passive interface** stops OSPF Hello packets on an interface — it still advertises the network into OSPF but doesn't try to form neighbors. Used on loopbacks (can't have neighbors) and user-facing SVIs (hosts aren't OSPF routers).

**Guidance for distribution switches:**
- Make host-facing SVIs passive unless an OSPF adjacency is deliberately required on that VLAN.
- Do not automatically exempt the management VLAN. A non-passive SVI can form an adjacency only if both devices run OSPF on that shared subnet.
- In the harvested configs, DSW-A1 includes its VLAN 99 SVI in OSPF without marking it passive, while DSW-A2 does not include VLAN 99 in its OSPF network statements. Verify operational neighbors instead of assuming a redundant VLAN 99 adjacency exists.

```
! === DSW-A1 — Selective passive interfaces ===
router ospf 1
 passive-interface Loopback0
 passive-interface Vlan10
 passive-interface Vlan20
 passive-interface Vlan40
 ! VLAN 99 is not passive on the harvested DSW-A1; verify intended neighbor behavior.
 exit
```

---

### Section 3 — OSPF Network Type Point-to-Point

> [!NOTE] Key Concept
> On broadcast links (Ethernet), OSPF elects a **DR** (Designated Router) and **BDR** to reduce OSPF traffic. On a direct link between two switches, DR/BDR election is unnecessary overhead. `network type point-to-point` skips the election entirely.

```
! Apply to physical routed links between core and distribution switches
interface GigabitEthernet1/0/23
 ip ospf network point-to-point
 exit

interface GigabitEthernet1/0/24
 ip ospf network point-to-point
 exit

! On the L3 EtherChannel between CSW1 and CSW2
interface Port-channel1
 ip ospf network point-to-point
 exit
```

> [!WARNING] Exam Flag 🎯
> On a point-to-point network type, OSPF adjacency goes directly to **Full** state without DR/BDR election. On a broadcast link without `point-to-point`, the state progression is: Down → Init → 2-Way → Exstart → Exchange → Loading → **Full** (only with DR/BDR). Using `point-to-point` on direct links speeds up convergence.

---

### Section 4 — Static Default-Route Failover (Concept Example)

> [!NOTE] Key Concept
> **Concept example only:** Two static default routes can provide primary/backup paths when both next hops and link-failure behavior are known. This is not how the harvested R1 IPv4 route is configured.

**Administrative Distance (AD):**

| Route Type | Default AD |
|---|---|
| Connected | 0 |
| Static | 1 |
| OSPF | 110 |
| RIP | 120 |

```
! === Generic example — do not paste into the running lab ===

! Primary: via ISP A — recursive lookup (next-hop IP only)
! AD = 1 (default for static)
ip route 0.0.0.0 0.0.0.0 203.0.113.1

! Backup: via ISP B — fully specified (interface + next-hop)
! AD = 2 (floating — only activates if primary is gone)
ip route 0.0.0.0 0.0.0.0 GigabitEthernet0/3 203.0.113.5 2

! Advertise the default route into OSPF
! (already configured in router ospf 1 section above)
! default-information originate
```

**Recursive vs. fully-specified static routes:**
- **Recursive** (`ip route 0.0.0.0 0.0.0.0 203.0.113.1`) — R1 must look up `203.0.113.1` to find the exit interface. If ISP A's link goes down, the recursive lookup fails → route disappears → floating static activates. ✅
- **Fully-specified** (`ip route ... GigabitEthernet0/0/1 203.0.113.5 2`) — always in the table as long as the interface is up. Used for the floating backup so it stays ready.

> [!WARNING] Exam Flags 🎯
> - Floating static AD must be **higher** than the primary route's AD (1 for static; 110 for OSPF)
> - `default-information originate` injects a Type 5 LSA (external) into OSPF — only works if R1 has a default route in its routing table
> - `default-information originate always` injects the default route even if R1 has no default route — useful for testing but risky in production

---

## 🖥️ NetBridge Applied — Full Config Block

> [!TIP] R1 — OSPF and Current IPv4 Default Route

```
! === R1 — live IPv4 default route and OSPF config ===

! Live R1 default route is learned via DHCP on Gi0/3:
ip route 0.0.0.0 0.0.0.0 GigabitEthernet0/3 dhcp
! No IPv4 floating static default route appears in the harvested config.

! OSPF
router ospf 1
 router-id 10.0.0.76
 passive-interface Loopback0
 default-information originate
 exit

interface Loopback0
 ip ospf 1 area 0
 exit

interface GigabitEthernet0/0
 ip ospf network point-to-point
 ip ospf 1 area 0
 exit

interface GigabitEthernet0/1
 ip ospf network point-to-point
 ip ospf 1 area 0
 exit

write memory
```

> [!TIP] DSW-A1 — Complete Part 5 Configuration

```
! === DSW-A1 — OSPF ===

router ospf 1
 router-id 10.0.0.79
 network 10.0.0.79 0.0.0.0 area 0
 network 10.0.0.46 0.0.0.0 area 0
 network 10.0.0.62 0.0.0.0 area 0
 network 10.1.0.2 0.0.0.0 area 0
 network 10.2.0.2 0.0.0.0 area 0
 network 10.6.0.2 0.0.0.0 area 0
 network 10.0.0.2 0.0.0.0 area 0
 passive-interface Loopback0
 passive-interface Vlan10
 passive-interface Vlan20
 passive-interface Vlan40
 exit

! Point-to-point on uplinks
interface Ethernet1/1
 ip ospf network point-to-point
 exit

interface Ethernet1/2
 ip ospf network point-to-point
 exit

write memory
```

---

## ✅ Verification Commands

| Command | What to Look For |
|---|---|
| `show ip ospf neighbor` | All expected neighbors in `FULL` state |
| `show ip route ospf` | `O` routes for all remote subnets; `O*E2` for default route |
| `show ip route 0.0.0.0` | Check the DHCP-learned default via Gi0/3; no IPv4 floating static is configured in the harvested state |
| `show ip ospf interface brief` | All OSPF-activated interfaces listed with correct area |
| `show ip ospf` | Router ID, process ID, area memberships |
| `ping 10.0.0.76` from DSW-A1 | Reaches R1's loopback via OSPF |

---

## ⚠️ Common Pitfalls

> [!WARNING] Watch Out
> - **`network` command wildcard wrong** — `0.0.0.0` wildcard matches exactly one IP (/32); using `0.0.0.255` would match the whole /24 (may activate unwanted interfaces)
> - **Missing `passive-interface`** — OSPF sends Hellos on host-facing ports; hosts aren't OSPF routers → Hellos waste bandwidth and confuse debugging
> - **`default-information originate` with no default route** — without `always` keyword, R1 won't inject the default if it doesn't have one; verify with `show ip route 0.0.0.0`
> - **Floating static AD not higher than primary** — if both are AD=1, the floating route competes with the primary instead of being a backup
> - **No `point-to-point` on direct links** — DR/BDR election still runs; on a two-switch link, one becomes DR, the other BDR — wasted effort; use `point-to-point` to skip it

---

## 📊 Concepts Summary

| Concept | What It Does | Exam Tip |
|---|---|---|
| OSPF process 1 | Link-state routing protocol | Process number is locally significant |
| Router ID | Unique OSPF identity (highest loopback IP or configured) | Always configure manually for predictability |
| `network X 0.0.0.0 area 0` | Activate OSPF on exact interface IP | `/32` wildcard = exact match |
| Passive interface | Advertise network but don't send Hellos | Use on loopbacks and host-facing SVIs |
| `point-to-point` | Skip DR/BDR election on direct links | Faster convergence on switch-to-switch links |
| `default-information originate` | Inject default route into OSPF as E2 | R1 must have a default route itself |
| Static route AD=1 | Example primary route | Static-route example only; not the live IPv4 default |
| Floating static AD=2 | Example backup route | Higher AD = lower preference; not configured for live IPv4 |
| Recursive static | Next-hop only; fails if next-hop unreachable | Good for primary route — auto-fails gracefully |
| Fully-specified static | Interface + next-hop; always in table while IF up | Good for floating backup |
| ASBR | Router that imports external routes into OSPF | R1 role when `default-information originate` is set |

---

## 🛠️ Practice Tasks

> [!CAUTION] Practice safely
> Route/link failure tests can interrupt connectivity. Use an isolated copy or an agreed maintenance window, record the original state, and restore every changed route or interface after testing.

1. **OSPF neighbor verification:** After configuring OSPF, run `show ip ospf neighbor` on every device. Verify all expected neighbors appear in FULL state. Troubleshoot any that are stuck in INIT or 2-WAY.

2. **Static-route practice (optional):** In an isolated copy of the lab, configure two known static next hops and test route selection. Do not remove the live DHCP default route on R1; the harvested config does not show an IPv4 floating static backup.

3. **`default-information originate` verification:** On a distribution switch, run `show ip route` and check whether an OSPF external default is installed. Configuration alone does not establish that upstream connectivity or Internet access currently works.

4. **Passive interface check:** Run `show ip ospf interface brief` on DSW-A1. Verify VLAN 10/20/40 SVIs show as passive. Then verify `show ip route` on CSW1 still shows the VLAN 10 subnet (passive doesn't stop advertisement — only Hellos).
