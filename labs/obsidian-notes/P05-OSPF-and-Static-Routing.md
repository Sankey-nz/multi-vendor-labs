# P05 — OSPF & Static Routing

> [!NOTE] Part Summary
> **Topic:** Enable OSPF across all L3 devices, configure dual default routes on R1 for ISP redundancy, and advertise the default route into OSPF
> **NetBridge Scenario:** VLANs have IPs and gateways — but traffic can't reach the internet or cross between offices without routing. NetBridge deploys OSPF Area 0 across the entire network, adds a floating static route for ISP failover, and lets R1 inject a default route so every device knows how to reach the internet.
> **Key Concepts:** OSPF process, Area 0, router ID, `network` command, passive interfaces, `network-type point-to-point`, default route, `default-information originate`, floating static route, AD
> **Devices involved:** R1, CSW1, CSW2, DSW-A1, DSW-A2, DSW-B1, DSW-B2

---

## 🗺️ Big Picture

> [!TIP] Mental Model
> OSPF is the "GPS system" — it discovers all routes and shares them across the network. Static routes are the "hardcoded fallback" — when the GPS doesn't know a route (like the internet), you tell it manually. The floating static provides a backup ISP path that only activates if the primary disappears.

```
Internet
   ↕ ISP A (primary, AD=1)     ↕ ISP B (backup, AD=2 floating)
         R1 (ASBR — default-information originate)
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
! === R1 ===
router ospf 1
 router-id 10.0.0.76                  ! loopback IP — stable, never goes down
 network 10.0.0.76 0.0.0.0 area 0    ! loopback0 — /32 wildcard = exact match
 network 10.0.0.33 0.0.0.0 area 0    ! LAN uplink to CSW1
 network 10.0.0.37 0.0.0.0 area 0    ! LAN uplink to CSW2
 passive-interface Loopback0          ! loopback can't form OSPF neighbors
 default-information originate        ! inject default route into OSPF
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
 passive-interface Vlan99             ! EXCEPT Management — see note below
 exit
```

---

### Section 2 — Passive Interfaces

> [!NOTE] Key Concept
> **Passive interface** stops OSPF Hello packets on an interface — it still advertises the network into OSPF but doesn't try to form neighbors. Used on loopbacks (can't have neighbors) and user-facing SVIs (hosts aren't OSPF routers).

**Rule for distribution switches:**
- Make **all** SVIs passive **except Management VLAN 99**
- Why: without Management VLAN passive, the two distribution switches form redundant OSPF adjacencies over every shared VLAN (10, 20, 40, 99) — wasting resources and creating unnecessary SPF calculations
- Management VLAN 99 SVI is kept active so the two distribution switches can communicate via Management VLAN for other protocols if needed

```
! === DSW-A1 — Selective passive interfaces ===
router ospf 1
 passive-interface Loopback0
 passive-interface Vlan10
 passive-interface Vlan20
 passive-interface Vlan40
 ! Note: Vlan99 (Management) is NOT passive — kept active
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

### Section 4 — Default Routes on R1 (Primary + Floating)

> [!NOTE] Key Concept
> R1 has two ISP connections. The **primary** static default route (AD=1) handles normal traffic. The **floating static** (AD=2) is a backup — its higher AD means it's only installed in the routing table when the primary disappears.

**Administrative Distance (AD):**

| Route Type | Default AD |
|---|---|
| Connected | 0 |
| Static | 1 |
| OSPF | 110 |
| RIP | 120 |

```
! === R1 — Dual Default Routes ===

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

> [!TIP] R1 — Complete Part 5 Configuration

```
! === R1 — OSPF + Static Routes ===

! Static default routes
ip route 0.0.0.0 0.0.0.0 203.0.113.1          ! primary via ISP A, AD=1
ip route 0.0.0.0 0.0.0.0 GigabitEthernet0/3 203.0.113.5 2  ! floating backup

! OSPF
router ospf 1
 router-id 10.0.0.76
 network 10.0.0.76 0.0.0.0 area 0
 network 10.0.0.33 0.0.0.0 area 0
 network 10.0.0.37 0.0.0.0 area 0
 passive-interface Loopback0
 default-information originate
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
| `show ip route 0.0.0.0` | Primary static (AD 1) active; floating not installed |
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
| Static route AD=1 | Primary default route | Installed by default; lower AD wins |
| Floating static AD=2 | Backup default route | Higher AD = only installed if primary gone |
| Recursive static | Next-hop only; fails if next-hop unreachable | Good for primary route — auto-fails gracefully |
| Fully-specified static | Interface + next-hop; always in table while IF up | Good for floating backup |
| ASBR | Router that imports external routes into OSPF | R1 role when `default-information originate` is set |

---

## 🛠️ Practice Tasks

1. **OSPF neighbor verification:** After configuring OSPF, run `show ip ospf neighbor` on every device. Verify all expected neighbors appear in FULL state. Troubleshoot any that are stuck in INIT or 2-WAY.

2. **Floating static failover:** Verify primary default route is active (`show ip route 0.0.0.0`). Shut R1's primary WAN interface. Confirm the floating static takes over. Restore the WAN link and verify the primary route returns.

3. **`default-information originate` verification:** On DSW-A1, run `show ip route` — look for `O*E2 0.0.0.0/0` (OSPF external default route injected by R1). Verify you can ping an internet IP (8.8.8.8) from a distribution switch.

4. **Passive interface check:** Run `show ip ospf interface brief` on DSW-A1. Verify VLAN 10/20/40 SVIs show as passive. Then verify `show ip route` on CSW1 still shows the VLAN 10 subnet (passive doesn't stop advertisement — only Hellos).
