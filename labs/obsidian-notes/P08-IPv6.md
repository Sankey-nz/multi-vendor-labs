# P08 — IPv6

> [!NOTE] Part Summary
> **Topic:** Enable IPv6 routing on R1, CSW1, and CSW2 using three different address assignment methods, and configure dual IPv6 default routes mirroring the IPv4 ISP failover setup
> **NetBridge Scenario:** The client's infrastructure needs to support IPv6 alongside IPv4 (dual-stack). Part 8 is a light touch — IPv6 is only enabled on the core layer (R1, CSW1, CSW2) for this lab, demonstrating three different ways to assign IPv6 addresses.
> **Key Concepts:** `ipv6 unicast-routing`, global unicast address, EUI-64, link-local only (`ipv6 enable`), IPv6 floating static route, AD
> **Devices involved:** R1, CSW1, CSW2

---

## 🗺️ Big Picture

> [!TIP] Mental Model
> IPv6 addresses are 128-bit, written in hexadecimal, split into 8 groups of 4 hex digits (e.g. `2001:0db8:0001:0000:0000:0000:0000:0001`). Three ways to configure an address on an interface — full manual, EUI-64 (auto-generate host portion from MAC), and link-local only.

```
Three addressing methods demonstrated:
1. Full manual:  ipv6 address 2001:db8:0:1::1/64
2. EUI-64:       ipv6 address 2001:db8:0:2::/64 eui-64
                 (host portion auto-generated from interface MAC)
3. Link-local:   ipv6 enable
                 (only link-local address fe80::x/10 — auto-generated)
```

---

## Live Config Evidence (Harvested 2026-09-14)

> [!check] Verified Live — R1, CSW1, CSW2 configs harvested Mon Sep 14 2026 07:32 UTC
>
> ### ✅ ipv6 unicast-routing
> Confirmed present on all three devices:
> ```
> ! R1   — ipv6 unicast-routing  ✅
> ! CSW1 — ipv6 unicast-routing  ✅
> ! CSW2 — ipv6 unicast-routing  ✅
> ```
>
> ---
>
> ### ✅ R1 — IPv6 Addresses (live)
> R1 runs IOSv flat interface numbering (Gi0/x), not the sub-slot Gi0/x/x shown in the note's planned config.
> ```
> interface GigabitEthernet0/0
>  description connection ETH0/2 CSW2
>  ipv6 address 2001:DB8:A2::/64 eui-64       ! EUI-64 — uplink to CSW2
>
> interface GigabitEthernet0/1
>  description connection ETH0/2 CSW1
>  ipv6 address 2001:DB8:A1::/64 eui-64       ! EUI-64 — uplink to CSW1
>
> interface GigabitEthernet0/2
>  ipv6 address 2001:DB8:B::2/64              ! Manual — ISP-A (primary WAN)
>
> interface GigabitEthernet0/3
>  description ISP-B
>  ipv6 address 2001:DB8:A::2/64             ! Manual — ISP-B (floating WAN)
> ```
> No IPv6 address on Loopback0 (note planned `2001:db8:0:ff::1/128` — not implemented in live lab).
>
> ---
>
> ### ✅ R1 — IPv6 Static Routes (live)
> ```
> ! Primary default — recursive next-hop only, no AD specified (AD=1)
> ipv6 route ::/0 2001:DB8:A::1
>
> ! Floating backup — fully specified (interface + next-hop) + AD=2
> ipv6 route ::/0 GigabitEthernet0/2 2001:DB8:B::1 2
> ```
> Dual default route pattern confirmed. Primary via ISP-B (`Gi0/3`, next-hop `2001:DB8:A::1`); floating via ISP-A (`Gi0/2`, next-hop `2001:DB8:B::1`, AD=2). Note: ISP naming is swapped vs. planned design — `Gi0/3` is labelled `ISP-B` in the description but carries the primary (no-AD) IPv6 default.
>
> ---
>
> ### ✅ CSW1 — IPv6 Addresses (live)
> ```
> interface Ethernet0/2
>  description connection R2 Gig 0/1
>  ipv6 address 2001:DB8:A1::/64 eui-64       ! EUI-64 — uplink to R1 ✅ matches plan
>
> interface Port-channel1
>  ipv6 enable                                  ! Link-local only — CSW1↔CSW2 EtherChannel ✅ matches plan
> ```
>
> ---
>
> ### ✅ CSW2 — IPv6 Addresses (live)
> ```
> interface Ethernet0/2
>  description connection R1 Gig 0/0
>  ipv6 address 2001:DB8:A2::/64 eui-64       ! EUI-64 — uplink to R1
>
> interface Port-channel1
>  ipv6 enable                                  ! Link-local only — CSW2↔CSW1 EtherChannel ✅ matches plan
> ```
>
> ---
>
> ### Addressing Method Summary (live)
> | Device | Interface | Method | Address |
> |--------|-----------|--------|---------|
> | R1 | Gi0/0 (→ CSW2) | EUI-64 | `2001:DB8:A2::/64 eui-64` |
> | R1 | Gi0/1 (→ CSW1) | EUI-64 | `2001:DB8:A1::/64 eui-64` |
> | R1 | Gi0/2 (ISP-A) | Manual | `2001:DB8:B::2/64` |
> | R1 | Gi0/3 (ISP-B) | Manual | `2001:DB8:A::2/64` |
> | CSW1 | Ethernet0/2 (→ R1) | EUI-64 | `2001:DB8:A1::/64 eui-64` |
> | CSW1 | Port-channel1 (→ CSW2) | Link-local only | `ipv6 enable` |
> | CSW2 | Ethernet0/2 (→ R1) | EUI-64 | `2001:DB8:A2::/64 eui-64` |
> | CSW2 | Port-channel1 (→ CSW1) | Link-local only | `ipv6 enable` |
>
> ---
>
> ### ⚠️ Deviations from Planned Design
> 1. **Interface numbering** — Note uses Cisco ISR sub-slot notation (`Gi0/0/0`, `Gi0/1/0`). Live lab runs IOSv with flat interfaces (`Gi0/0`, `Gi0/1`, `Gi0/2`, `Gi0/3`). Functionally equivalent.
> 2. **R1 uplinks use EUI-64, not full manual** — Note planned `ipv6 address 2001:db8:0:1::1/64` (full manual) for the LAN-facing interface. Live lab uses EUI-64 on both R1→CSW uplinks (`2001:DB8:A1::/64` and `2001:DB8:A2::/64`). WAN interfaces use full manual instead.
> 3. **Loopback0 — no IPv6 address** — Note planned `2001:db8:0:ff::1/128` on R1 Loopback0. Not present in the live config.
> 4. **ISP-B WAN interface** — Note planned `ipv6 enable` (link-local only) on the ISP-B interface. Live config has a full manual GUA (`2001:DB8:A::2/64`) on `Gi0/3 ISP-B`.
> 5. **Subnet naming** — Note uses `2001:db8:0:x::` prefixes. Live lab uses `2001:DB8:Ax::` style (e.g., `A1`, `A2`, `A`, `B`) reflecting the actual lab topology subnets.

---

## 📚 Sections

### Section 1 — Enable IPv6 Routing

> [!NOTE] Key Concept
> `ipv6 unicast-routing` is the IPv6 equivalent of `ip routing` — it must be enabled on every device that needs to route IPv6 traffic (not just have IPv6 addresses).

```
! === R1, CSW1, CSW2 ===
ipv6 unicast-routing
```

> [!WARNING] Exam Flag 🎯
> Without `ipv6 unicast-routing`, a device with IPv6 addresses will NOT forward IPv6 traffic — it will only process packets destined for itself. This is the most commonly forgotten command in IPv6 configurations.

---

### Section 2 — IPv6 Address Types

> [!NOTE] Key Concept
> Three address types used in this lab, all within the interface configuration.

**Global Unicast Address (GUA)** — the IPv6 equivalent of a public IP:
```
2000::/3 range — currently 2001:: through 3fff::
```

**Link-Local Address** — only valid on a single link; auto-generated or manually set:
```
fe80::/10 range — always starts with fe80
```

**EUI-64** — auto-generates a 64-bit interface ID from the 48-bit MAC address:
```
MAC:  00:1A:2B:3C:4D:5E
EUI-64 process:
  1. Insert FFFE in the middle:  001A:2BFF:FE3C:4D5E
  2. Flip bit 7 (universal/local bit) of first byte:
     001A → 021A (binary: 00000000 → 00000010)
  Result: 021A:2BFF:FE3C:4D5E
Full address: 2001:db8:0:2:021A:2BFF:FE3C:4D5E/64
```

---

### Section 3 — Three Addressing Methods

> [!NOTE] Key Concept
> Each interface on R1, CSW1, and CSW2 uses a different method — demonstrating all three in the same lab.

**Method 1 — Full manual (R1 LAN interface):**
```
interface GigabitEthernet0/1/0
 ipv6 address 2001:db8:0:1::1/64
 no shutdown
 exit
```

**Method 2 — EUI-64 (CSW1 uplink to R1):**
```
interface GigabitEthernet1/0/1
 ipv6 address 2001:db8:0:2::/64 eui-64
 ! Host portion auto-generated from the interface's MAC address
 no shutdown
 exit
```

**Method 3 — Link-local only (CSW1 ↔ CSW2 link):**
```
interface Port-channel1
 ipv6 enable
 ! Only generates an fe80:: link-local address
 ! No global unicast — this link only needs reachability for routing
 no shutdown
 exit
```

**When to use each method:**

| Method | Use Case |
|---|---|
| Full manual | Servers, routers, anything needing a predictable IPv6 address |
| EUI-64 | Clients and non-critical infrastructure where the exact host portion doesn't matter |
| Link-local only (`ipv6 enable`) | Transit/backbone links where only routing adjacencies are needed |

---

### Section 4 — IPv6 Default Routes (Dual ISP Failover)

> [!NOTE] Key Concept
> Mirrors the IPv4 floating static setup from Part 5 — primary route via ISP A (lower AD), floating backup via ISP B (higher AD).

```
! === R1 — IPv6 Default Routes ===

! Primary via ISP A — recursive (next-hop IPv6 address only)
ipv6 route ::/0 2001:db8:a:1::1          ! ::/0 = IPv6 default route (like 0.0.0.0/0)

! Floating backup via ISP B — fully specified (interface + next-hop) + higher AD
ipv6 route ::/0 GigabitEthernet0/0/1 2001:db8:b:1::1 2
!                                                      ↑ AD = 2 (floating)
```

**IPv4 vs. IPv6 default route comparison:**

| | IPv4 | IPv6 |
|---|---|---|
| Default route notation | `0.0.0.0 0.0.0.0` | `::/0` |
| Static route command | `ip route` | `ipv6 route` |
| Routing enable | `ip routing` | `ipv6 unicast-routing` |
| Address types | Class A/B/C/D/E | GUA, Link-local, Multicast, Anycast |

> [!WARNING] Exam Flags 🎯
> - `::/0` is the IPv6 default route (all zeros, prefix length 0 — matches everything)
> - IPv6 floating static: same AD concept as IPv4 — higher AD = lower preference = backup
> - `show ipv6 route` — verify primary and floating routes; floating shows only when primary is down

---

## 🖥️ NetBridge Applied — Full Config Block

> [!TIP] R1 — Complete Part 8 Configuration

```
! === R1 — IPv6 ===

! Enable IPv6 routing
ipv6 unicast-routing

! LAN interface — full manual address
interface GigabitEthernet0/1/0
 ipv6 address 2001:db8:0:1::1/64
 no shutdown
 exit

! WAN interface ISP A — full manual
interface GigabitEthernet0/0/0
 ipv6 address 2001:db8:a:1::2/64
 no shutdown
 exit

! WAN interface ISP B — link-local only
interface GigabitEthernet0/0/1
 ipv6 enable
 no shutdown
 exit

! Loopback0 — full manual
interface Loopback0
 ipv6 address 2001:db8:0:ff::1/128
 exit

! Dual IPv6 default routes
ipv6 route ::/0 2001:db8:a:1::1          ! primary via ISP A
ipv6 route ::/0 GigabitEthernet0/0/1 2001:db8:b:1::1 2  ! floating via ISP B

write memory
```

> [!TIP] CSW1 — Complete Part 8 Configuration

```
! === CSW1 — IPv6 ===

ipv6 unicast-routing

! Uplink to R1 — EUI-64
interface GigabitEthernet1/0/1
 ipv6 address 2001:db8:0:2::/64 eui-64
 no shutdown
 exit

! L3 EtherChannel to CSW2 — link-local only
interface Port-channel1
 ipv6 enable
 no shutdown
 exit

! Downlinks to distribution — full manual
interface GigabitEthernet1/0/3
 ipv6 address 2001:db8:0:3::1/64
 no shutdown
 exit

write memory
```

---

## ✅ Verification Commands

| Command | What to Look For |
|---|---|
| `show ipv6 interface brief` | All IPv6 interfaces with addresses and `up/up` |
| `show ipv6 route` | Connected, local, and static routes; `::/0` default |
| `show ipv6 route static` | Primary default (lower AD) and floating (if primary down) |
| `ping ipv6 2001:db8:0:2::1` | IPv6 reachability test |
| `show ipv6 interface Gi0/1/0` | Full address including EUI-64 generated portion |

---

## ⚠️ Common Pitfalls

> [!WARNING] Watch Out
> - **Forgetting `ipv6 unicast-routing`** — device won't route IPv6; same trap as forgetting `ip routing` on switches
> - **EUI-64 bit-flip confusion** — the 7th bit of the first octet is inverted; MAC `00:` becomes `02:` in the EUI-64 address (universal → locally administered bit)
> - **`::/0` vs `0.0.0.0/0`** — the IPv6 default route is `::/0`; `0.0.0.0/0` is IPv4 only; don't mix them
> - **Link-local only on transit links** — this works for routing protocol adjacencies but hosts can't reach these interfaces by global address (no GUA assigned)
> - **Missing `no shutdown`** — IPv6 interfaces behave the same as IPv4; must be `no shutdown`

---

## 📊 Concepts Summary

| Concept | What It Does | Exam Tip |
|---|---|---|
| `ipv6 unicast-routing` | Enable IPv6 routing on the device | Required on all routers and L3 switches |
| Global Unicast Address | Globally routable IPv6 (like public IP) | Starts with 2000::/3 (currently 2001:: range) |
| Link-Local Address | Only valid on one link (fe80::/10) | Auto-generated; required for IPv6 to work |
| `ipv6 address X/64` | Full manual IPv6 address assignment | Most predictable; always know the address |
| `ipv6 address X::/64 eui-64` | Auto-generate host portion from MAC | Use where exact address doesn't matter |
| `ipv6 enable` | Generate link-local only | Transit links needing only routing adjacency |
| EUI-64 | MAC → 64-bit interface ID | Insert FFFE in middle; flip bit 7 |
| `::/0` | IPv6 default route | Equivalent of IPv4 `0.0.0.0/0` |
| `ipv6 route ::/0 X 2` | IPv6 floating static | Higher AD = backup; same concept as IPv4 |

---

## 🛠️ Practice Tasks

1. **EUI-64 calculation:** Take a switch's MAC address (find with `show interfaces`). Manually calculate the EUI-64 interface ID. Configure an IPv6 address using EUI-64. Verify with `show ipv6 interface` that the host portion matches your calculation.

2. **IPv6 routing verification:** After Part 8 config, `ping ipv6` from R1 to CSW1's GUA. Then `ping ipv6` from CSW1 to CSW2 using link-local (remember to specify the exit interface for link-local: `ping ipv6 fe80::1 Gi1/0/1`).

3. **IPv6 floating static failover:** Verify `show ipv6 route` shows `::/0` via ISP A. Shut ISP A interface on R1. Verify the floating route via ISP B activates. Restore the interface and verify failback.

4. **Dual-stack comparison:** On R1, compare `show ip route` and `show ipv6 route` side by side. Identify the equivalent entries: connected routes, static defaults, and floating statics. Note how the structures mirror each other.
