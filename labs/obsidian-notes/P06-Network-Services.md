# P06 — Network Services (DHCP, DNS, NTP, SNMP, SSH, NAT)

> [!NOTE] Part Summary
> **Topic:** Study DHCP, DNS, NTP, SNMP/Syslog, SSH, NAT, and service verification.
> **NetBridge Scenario:** This guide combines concepts and example configurations. Several described services and examples are not present in the harvested lab configuration.
> **Key Concepts:** DHCP pools, excluded addresses, relay (`ip helper-address`), NTP authentication, SNMP community strings, SSH v2, ACL + VTY, static NAT, dynamic PAT, NAT inside/outside
> **Devices involved:** R1, DSW-A1, DSW-A2, DSW-B1, DSW-B2, WIN-SV1 (DNS), WLC1

> [!IMPORTANT] Compare with the running configuration before using commands
> The harvested configs show DHCP pools on R1, DNS service at WIN-SV1 (`10.5.0.4`), an SNMP read-only community, syslog to `10.5.0.4`, and PAT through R1 Gi0/3. They do **not** establish that NTP is synchronized, an IOS image was upgraded by FTP, or static NAT exists. R1's `A-Mgmt` DHCP pool currently advertises `10.5.0.4` as its default router; the addressing table identifies `10.0.0.1` as the intended VLAN 99 gateway. Treat this as a live configuration discrepancy, not as an instruction to copy.

---

## 🗺️ Big Picture

> [!TIP] Mental Model
> Part 6 is the "services layer" — all the things that make a network usable. For each service, identify the actual server, configure clients where needed, then verify end-to-end behavior.

```
DHCP:    R1 pools → relays on SVIs → intended host address assignment
DNS:     WIN-SV1 (10.5.0.4)
SNMP:    Community configured; manager polling not verified
Syslog:  Configured to send to 10.5.0.4; receipt not verified
SSH:     SSHv2 configured; access policy varies by device
NAT:     PAT overload via R1 Gi0/3; no static NAT shown
```

---

## 📚 Sections

### Section 1 — DHCP on R1

> [!NOTE] Key Concept
> R1 has DHCP pools for the listed client networks. **Excluded addresses** reserve IPs for network devices (routers, switches, SVIs). Pools define the network, gateway, DNS, and domain for each subnet. Compare each pool with the addressing table: the harvested `A-Mgmt` pool has a wrong default-router value (`10.5.0.4` instead of the planned `10.0.0.1`).

```
! === R1 — DHCP Excluded Addresses (reserve first 10 usable IPs) ===
ip dhcp excluded-address 10.1.0.1 10.1.0.10    ! VLAN 10 — Office A PCs
ip dhcp excluded-address 10.2.0.1 10.2.0.10    ! VLAN 20 — Office A Phones
ip dhcp excluded-address 10.6.0.1 10.6.0.10    ! VLAN 40 — Office A Servers/Other
ip dhcp excluded-address 10.0.0.1 10.0.0.10    ! VLAN 99 — Management A
ip dhcp excluded-address 10.3.0.1 10.3.0.10    ! VLAN 10 — Office B PCs
ip dhcp excluded-address 10.4.0.1 10.4.0.10    ! VLAN 20 — Office B Phones
ip dhcp excluded-address 10.5.0.1 10.5.0.10    ! VLAN 30 — Office B Staff/Other
ip dhcp excluded-address 10.0.0.17 10.0.0.26    ! VLAN 99 — Office B Mgmt


! === Illustrative DHCP pool syntax; validate every value against the live pool ===

ip dhcp pool VLAN10_OFFICEA
 network 10.1.0.0 255.255.255.0
 default-router 10.1.0.1          ! HSRP virtual IP — the gateway
 dns-server 10.5.0.4               ! WIN-SV1
 domain-name SankeyLab
 exit

ip dhcp pool VLAN20_OFFICEA
 network 10.2.0.0 255.255.255.0
 default-router 10.2.0.1
 dns-server 10.5.0.4
 domain-name SankeyLab
 exit

ip dhcp pool VLAN40_WIFI
 network 10.6.0.0 255.255.255.0
 default-router 10.6.0.1
 dns-server 10.5.0.4
 domain-name SankeyLab
 exit

ip dhcp pool VLAN99_MGMT_A
 network 10.0.0.0 255.255.255.240
 default-router 10.0.0.1
 dns-server 10.5.0.4
 domain-name SankeyLab
 option 43 ip 10.0.0.7            ! WLC IP — LWAPs use this to find the WLC
 exit

! Office B pools use VLAN 10: 10.3.0.0/24, VLAN 20: 10.4.0.0/24,
! VLAN 30: 10.5.0.0/24, and Management VLAN 99: 10.0.0.16/28.
```

**`option 43`** — tells Lightweight Access Points (LWAPs) the IP of the WLC so they can associate with it during boot. Without this, LWAPs have no way to find the WLC.

---

### Section 2 — DHCP Relay (ip helper-address)

> [!NOTE] Key Concept
> DHCP uses broadcast — broadcasts don't cross router boundaries. `ip helper-address` on a distribution-switch SVI converts DHCP broadcasts into **unicast** packets directed at R1's loopback (`10.0.0.76`), allowing R1 to serve DHCP requests from any VLAN.

```
! === DSW-A1 — DHCP relay on all SVIs ===
interface Vlan10
 ip helper-address 10.0.0.76    ! R1 loopback — always reachable via OSPF
 exit

interface Vlan20
 ip helper-address 10.0.0.76
 exit

interface Vlan40
 ip helper-address 10.0.0.76
 exit

interface Vlan99
 ip helper-address 10.0.0.76
 exit

! Apply the same on DSW-A2, DSW-B1, DSW-B2 for their respective VLANs
```

> [!WARNING] Exam Flags 🎯
> - `ip helper-address` goes on the **client-side SVI** (where hosts send DHCP requests), not on R1
> - Using R1's **loopback** IP (not a physical interface IP) ensures relay works even if one path to R1 fails — loopback is always reachable via any OSPF path
> - Verify with `show ip dhcp binding` on R1 — assigned leases appear here

---

### Section 3 — NTP (Concept Example)

> [!NOTE] Key Concept
> **NTP** (Network Time Protocol) synchronises clocks. R1 is the **authoritative time source** with an authentication key — every device points to R1 and validates the key before accepting time updates.

```
! === R1 — NTP Server (authoritative) ===
ntp authenticate
ntp authentication-key 1 md5 <key-string> 7
ntp trusted-key 1
ntp master 5          ! stratum 5 — R1 acts as authoritative source


! === All other devices (CSW1, CSW2, DSW-A1/A2, DSW-B1/B2, ASWs) ===
ntp authenticate
ntp authentication-key 1 md5 <key-string> 7
ntp trusted-key 1
ntp server 10.0.0.76 key 1    ! point to R1's loopback with key validation
```

> [!WARNING] Exam Flag 🎯
> NTP authentication key must match exactly on both server and clients — including the key number (1), algorithm (md5), and passphrase. Mismatch = clients reject R1's time updates silently.

The harvested R1 config does not show `ntp master` or an NTP server association. Client configs contain authentication-key settings, but that alone does not demonstrate a synchronized clock. Verify live with `show ntp status` and `show ntp associations`.

---

### Section 4 — SNMP and Syslog

> [!NOTE] Key Concept
> **SNMP** lets a management station poll device statistics. **Syslog** sends log messages to a collector. The harvested device configs contain SNMP and syslog settings, but manager polling and log receipt have not been verified.

```
! === All devices — SNMP + Syslog ===

! SNMP read-only community string
snmp-server community <read-only-community> RO

! Syslog
logging 10.5.0.4                    ! WIN-SV1 IP
logging trap debugging               ! severity 7 = send all messages
logging buffered 8192                ! buffer 8 KB of logs locally too
```

**Syslog severity levels (0 = most critical, 7 = most verbose):**

| Level | Name | Meaning |
|---|---|---|
| 0 | Emergency | System unusable |
| 1 | Alert | Immediate action needed |
| 2 | Critical | Critical conditions |
| 3 | Error | Error conditions |
| 4 | Warning | Warning conditions |
| 5 | Notice | Normal but significant |
| 6 | Informational | Informational |
| 7 | Debugging | All messages |

> [!WARNING] Exam Flag 🎯
> `logging trap debugging` sends severity 7 and **all levels below it** (0–7) — everything. In production, use level 6 (informational) or lower to avoid overwhelming the syslog server.

---

### Section 5 — SSH Hardening (Concept Example)

> [!NOTE] Key Concept
> SSH v2 with a locally selected key size, restricted by an example ACL, applied to VTY lines with `login local` and `transport input ssh`. Check each device's VTY configuration before relying on the example.

```
! === All devices — SSH Configuration ===

! Step 1: Set domain name (required for RSA key generation)
ip domain-name SankeyLab

! Step 2: Generate RSA key pair (4096-bit = strongest)
crypto key generate rsa
! When prompted: How many bits in the modulus [512]: 4096

! Step 3: Force SSH version 2 (v1.99 = ambiguous compatibility mode)
ip ssh version 2

! Step 4: ACL restricting SSH source to Office A's Mgmt subnet only
ip access-list standard SSH_ACCESS
 permit 10.1.0.0 0.0.0.255    ! Example: Office A VLAN 10, not the management subnet
 exit

! Step 5: Apply to VTY lines
line vty 0 15
 login local
 transport input ssh       ! block Telnet completely
 access-class SSH_ACCESS in
 logging synchronous
 exec-timeout 30 0
 exit
```

> [!WARNING] Exam Flags 🎯
> - `transport input ssh` disables Telnet on VTY — Telnet sends passwords in plaintext
> - `ip ssh version 2` without `ip domain-name` and `crypto key generate rsa` first → SSH won't work
> - ACL for SSH: applied with `access-class <acl> in` (not `ip access-group`) — `access-class` is specifically for VTY/Console lines
> - RSA key size must be ≥ 768 bits for SSHv2; 4096-bit is the lab requirement

---

### Section 6 — IOS Image Maintenance (Outside This Lab)

The harvested configs do not document an FTP-based IOS upgrade. This lab uses virtual IOSv/IOL images managed by the PNetLab environment; do not apply an unrelated physical-router image or reload a shared device as part of this study guide. For image maintenance, follow the emulator/platform's image lifecycle and use an isolated, backed-up environment.

---

### Section 7 — NAT on R1

> [!NOTE] Key Concept
> **NAT** translates private (RFC 1918) addresses for upstream access. The harvested R1 config has **PAT overload** on Gi0/3; it does not show a static NAT mapping or a public address pool.

```
! === Live R1 PAT rule ===
! Gi0/0 and Gi0/1 are inside; Gi0/2 and Gi0/3 are outside.
! ACL 2 selects inside source subnets (see configs/R1.txt).
ip nat inside source list 2 interface GigabitEthernet0/3 overload
```

**Static NAT vs. Dynamic PAT:**

| | Static NAT | Dynamic PAT |
|---|---|---|
| Mapping | 1:1 fixed | Many:1 with port multiplexing |
| Use case | Server needing fixed public IP | Outbound client traffic |
| Direction | Both inbound and outbound | Outbound only |
| Pool | Not needed — one IP per translation | May use a public pool or the outside-interface address |

**CDP → LLDP migration:**
```
! Globally disable CDP, enable LLDP
no cdp run
lldp run

! On access switch host-facing ports — disable LLDP transmit
interface range FastEthernet0/1 - 10
 no lldp transmit    ! don't reveal device info to end users
 exit
```

---

## Live Configuration Reference

Use the harvested [R1 configuration](../lab01-ccna-megalab/configs/R1.txt) and the device-specific configs as the authoritative command record. The lab's R1 uses interface-based PAT on Gi0/3, and its DHCP pools have distinct names and values. The generic examples above are not a combined paste-ready configuration.

---

## ✅ Verification Commands

| Command | What to Look For |
|---|---|
| `show ip dhcp binding` | All assigned leases with MAC and IP |
| `show ip dhcp pool` | Pool name, network, utilisation |
| `show ntp status` | Clock is synchronised; stratum matches |
| `show ntp associations` | A current peer marked `*` (synchronized); an R1 loopback is not confirmed as a live time source |
| `show ip ssh` | SSH enabled, version 2.0 |
| `show ip nat translations` | Dynamic PAT entries for active translated flows; no static server mapping is configured in the harvested config |
| `show ip nat statistics` | Hits counter incrementing for active NAT |
| `show users` | Active SSH sessions on VTY lines |
| `show lldp neighbors` | Replaces CDP output after migration |

---

## ⚠️ Common Pitfalls

> [!WARNING] Watch Out
> - **`ip helper-address` on wrong interface** — must be on the SVI that DHCP clients are in, not on R1's interface
> - **`option 43` missing from management pool** — LWAPs won't find the WLC; they'll be stuck in discovery phase
> - **NTP key mismatch** — check key number, algorithm, and passphrase are identical on all devices; NTP will appear to work but clock won't sync
> - **`transport input all` instead of `transport input ssh`** — allows Telnet (plaintext passwords); always restrict to `ssh` only
> - **NAT inside/outside on wrong interface** — ISP links must be `outside`; LAN facing must be `inside`; backward mapping = NAT breaks completely
> - **`crypto key generate rsa` without `ip domain-name`** — RSA generation fails; domain name required

---

## 📊 Concepts Summary

| Concept | What It Does | Exam Tip |
|---|---|---|
| `ip dhcp excluded-address` | Reserve IPs for static assignment | Configure before pool; first 10 usable IPs |
| `ip dhcp pool` | Define DHCP parameters for a subnet | One pool per subnet |
| `ip helper-address` | Relay DHCP broadcasts to unicast | Applied on client SVI, pointing to R1 loopback |
| `option 43` | Tells LWAPs the WLC's IP | Required in Management VLAN DHCP pool |
| `ntp master` | R1 acts as NTP time source | `ntp master 5` = stratum 5 |
| `ntp server X key Y` | Point device to NTP server with auth | Key number must match server's trusted-key |
| `snmp-server community X RO` | SNMP read-only string | RO = read only; RW = read-write (risky) |
| `logging X` | Send syslog to server IP X | `logging trap debugging` = all severities |
| `crypto key generate rsa` | Generate RSA key for SSH | Requires `ip domain-name` first |
| `ip ssh version 2` | Force SSHv2 | Eliminates v1.99 ambiguous mode |
| `transport input ssh` | Block Telnet on VTY | Telnet = plaintext; always restrict to SSH |
| `access-class X in` | Apply ACL to VTY lines | Different from `ip access-group` (which is for interfaces) |
| Static NAT | 1:1 fixed mapping | Not shown in the harvested config |
| Dynamic PAT | Many:1 with ports | Live rule uses ACL 2 and Gi0/3's interface address |
| NAT inside | Internal (private) interface | LAN-facing interfaces |
| NAT outside | External (public) interface | ISP-facing interfaces |

---

## 🛠️ Practice Tasks

> [!CAUTION] Practice safely
> DHCP, SSH, routing, and service changes can lock out users or disrupt the lab. Perform failure tests in an isolated copy or agreed maintenance window, save a known-good backup, and restore the original config after each test.

1. **DHCP relay test:** On a PC in VLAN 10, request a DHCP address. Verify on R1 with `show ip dhcp binding` that the lease appears. Remove `ip helper-address` from the SVI and retry — verify DHCP fails. Re-add and confirm recovery.

2. **NTP verification:** Configure NTP on two devices pointing to R1. Wait 60 seconds. Run `show ntp status` — verify `Clock is synchronized`. Change the NTP key passphrase on one device to something wrong — verify it falls out of sync.

3. **SSH access-policy test (isolated practice):** Configure an SSH VTY ACL for Office A VLAN 10 (`10.1.0.0/24`) on a test device. Test from VLAN 10 and another subnet, then verify the active VTY policy and sessions. Do not infer that every live device currently uses this policy.

4. **PAT verification:** Generate a permitted outbound flow, then inspect `show ip nat translations` and `show ip nat statistics` on R1. The captured IPv4 default route is DHCP on Gi0/3; no IPv4 floating static backup is shown, so do not use this as an IPv4 failover test.
