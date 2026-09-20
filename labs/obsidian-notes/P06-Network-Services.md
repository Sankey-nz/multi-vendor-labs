---
title: "P06 — Network Services (DHCP, DNS, NTP, SNMP, SSH, NAT)"
created: 2025-01-01
updated: 2025-01-01
tags:
  - ccna
  - netbridge
  - networking
  - dhcp
  - nat
  - ssh
  - ntp
  - snmp
  - syslog
  - dns
  - ftp
part: 6
topic: Network Services
status: reviewed
lab: CCNA Mega Lab
source: CCNA_Mega_Lab_Step_By_Step_Guide.md
---

# P06 — Network Services (DHCP, DNS, NTP, SNMP, SSH, NAT)

> [!info] Part Summary
> **Topic:** Configure all enterprise network services — DHCP, DNS, NTP, SNMP/Syslog, FTP-based IOS upgrade, SSH hardening, and NAT for internet access
> **NetBridge Scenario:** The physical and logical network is up. Now it needs services — hosts need automatic IP assignment (DHCP), time synchronisation (NTP), management monitoring (SNMP/Syslog), secure remote access (SSH), and internet connectivity (NAT). This is the longest part of the lab.
> **Key Concepts:** DHCP pools, excluded addresses, relay (`ip helper-address`), NTP authentication, SNMP community strings, SSH v2, ACL + VTY, static NAT, dynamic PAT, NAT inside/outside
> **Devices involved:** R1, DSW-A1, DSW-A2, DSW-B1, DSW-B2, SRV1 (DNS), WLC1

---

## 🗺️ Big Picture

> [!tip] Mental Model
> Part 6 is the "services layer" — all the things that make a network actually usable. Each service follows the same shape: configure the server (R1 or SRV1), configure the clients (switches/routers point to the server), and verify end-to-end.

```
DHCP:    R1 pools → relay on SVIs (ip helper-address) → hosts get IPs
NTP:     R1 authoritative → all devices sync to R1 with auth key
SNMP:    All devices → community string → SRV1 (SNMP manager)
Syslog:  All devices → logging SRV1 IP → SRV1 collects logs
SSH:     RSA 4096-bit → SSHv2 only → ACL restricts source IPs → VTY lines
NAT:     Static NAT for SRV1 (fixed public IP) + PAT for all others
```

---

## 📚 Sections

### Section 1 — DHCP on R1

> [!note] Key Concept
> R1 acts as the DHCP server for all subnets. **Excluded addresses** reserve IPs for network devices (routers, switches, SVIs). Pools define the network, gateway, DNS, and domain for each subnet.

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


! === R1 — DHCP Pools ===

ip dhcp pool VLAN10_OFFICEA
 network 10.1.0.0 255.255.255.0
 default-router 10.1.0.1          ! HSRP virtual IP — the gateway
 dns-server 10.5.0.4               ! SRV1
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

! Repeat for Office B pools (VLAN10, 20, 30, 99 with 10.2.x.x addressing)
```

**`option 43`** — tells Lightweight Access Points (LWAPs) the IP of the WLC so they can associate with it during boot. Without this, LWAPs have no way to find the WLC.

---

### Section 2 — DHCP Relay (ip helper-address)

> [!note] Key Concept
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

> [!warning] Exam Flags 🎯
> - `ip helper-address` goes on the **client-side SVI** (where hosts send DHCP requests), not on R1
> - Using R1's **loopback** IP (not a physical interface IP) ensures relay works even if one path to R1 fails — loopback is always reachable via any OSPF path
> - Verify with `show ip dhcp binding` on R1 — assigned leases appear here

---

### Section 3 — NTP

> [!note] Key Concept
> **NTP** (Network Time Protocol) synchronises clocks. R1 is the **authoritative time source** with an authentication key — every device points to R1 and validates the key before accepting time updates.

```
! === R1 — NTP Server (authoritative) ===
ntp authenticate
ntp authentication-key 1 md5 0007100805 7
ntp trusted-key 1
ntp master 5          ! stratum 5 — R1 acts as authoritative source


! === All other devices (CSW1, CSW2, DSW-A1/A2, DSW-B1/B2, ASWs) ===
ntp authenticate
ntp authentication-key 1 md5 0007100805 7
ntp trusted-key 1
ntp server 10.0.0.76 key 1    ! point to R1's loopback with key validation
```

> [!warning] Exam Flag 🎯
> NTP authentication key must match exactly on both server and clients — including the key number (1), algorithm (md5), and passphrase. Mismatch = clients reject R1's time updates silently.

---

### Section 4 — SNMP and Syslog

> [!note] Key Concept
> **SNMP** lets a management station (SRV1) poll device statistics. **Syslog** sends log messages to SRV1 for centralised monitoring. Both are configured on every network device.

```
! === All devices — SNMP + Syslog ===

! SNMP read-only community string
snmp-server community SNMPSTRING RO    ! Read-Only — monitoring only

! Syslog
logging 10.5.0.4                    ! SRV1 IP
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

> [!warning] Exam Flag 🎯
> `logging trap debugging` sends severity 7 and **all levels below it** (0–7) — everything. In production, use level 6 (informational) or lower to avoid overwhelming the syslog server.

---

### Section 5 — SSH Hardening

> [!note] Key Concept
> SSH v2 with RSA 4096-bit keys, restricted by ACL to only Office A's PC subnet, applied to VTY lines with `login local` and `transport input ssh`.

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
 permit 10.1.0.0 0.0.0.255
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

> [!warning] Exam Flags 🎯
> - `transport input ssh` disables Telnet on VTY — Telnet sends passwords in plaintext
> - `ip ssh version 2` without `ip domain-name` and `crypto key generate rsa` first → SSH won't work
> - ACL for SSH: applied with `access-class <acl> in` (not `ip access-group`) — `access-class` is specifically for VTY/Console lines
> - RSA key size must be ≥ 768 bits for SSHv2; 4096-bit is the lab requirement

---

### Section 6 — FTP-Based IOS Upgrade on R1

> [!note] Key Concept
> R1's IOS is upgraded by downloading a new image from SRV1 via FTP, setting the boot system variable, saving, and reloading. This is a slow process — the file transfer can take several minutes.

```
! === R1 — IOS Upgrade via FTP ===

! Step 1: Configure FTP credentials
ip ftp username cisco
ip ftp password cisco123

! Step 2: Download new IOS image from SRV1 (10.5.0.4)
copy ftp://10.5.0.4/c2900-universalk9-mz.SPA.155-3.M4a.bin flash:
! Confirm filename and flash destination when prompted
! (This step takes several minutes — wait for it to complete)

! Step 3: Set boot system to new image
boot system flash:c2900-universalk9-mz.SPA.155-3.M4a.bin

! Step 4: Save config
write memory

! Step 5: Reload
reload

! After reload — Step 6: Verify new version
show version
! Look for the new image filename in the output

! Step 7: Delete old image (reclaim flash space)
delete flash:c2900-universalk9-mz.SPA.151-4.M4.bin
```

---

### Section 7 — NAT on R1

> [!note] Key Concept
> **NAT** translates private (RFC 1918) addresses to public addresses for internet access. Two types configured: **static NAT** gives SRV1 a fixed public IP; **dynamic PAT** shares one public IP pool across all other hosts.

```
! === R1 — NAT Configuration ===

! Mark interfaces
interface GigabitEthernet0/0/0
 ip nat outside    ! ISP A link — public internet side
 exit

interface GigabitEthernet0/0/1
 ip nat outside    ! ISP B link — public internet side
 exit

interface GigabitEthernet0/1/0
 ip nat inside     ! LAN side
 exit


! Static NAT: SRV1 private IP → fixed public IP
ip nat inside source static 10.5.0.4 203.0.113.113


! Dynamic PAT: all internal subnets → shared public IP pool
! Step 1: ACL defines which traffic gets NAT'd
ip access-list standard NAT_SUBNETS
 permit 10.1.10.0 0.0.0.255    ! Office A PCs
 permit 10.1.20.0 0.0.0.255    ! Office A Phones
 permit 10.1.40.0 0.0.0.255    ! Wi-Fi
 permit 10.1.99.0 0.0.0.255    ! Management
 permit 10.2.10.0 0.0.0.255    ! Office B PCs
 permit 10.2.20.0 0.0.0.255    ! Office B Phones
 exit

! Step 2: Define public IP pool
ip nat pool POOL1 203.0.113.200 203.0.113.210 netmask 255.255.255.0

! Step 3: Apply PAT (overload = many-to-one, using port numbers)
ip nat inside source list NAT_SUBNETS pool POOL1 overload
```

**Static NAT vs. Dynamic PAT:**

| | Static NAT | Dynamic PAT |
|---|---|---|
| Mapping | 1:1 fixed | Many:1 with port multiplexing |
| Use case | Server needing fixed public IP | Outbound client traffic |
| Direction | Both inbound and outbound | Outbound only |
| Pool | Not needed — one IP per translation | Shared pool of public IPs |

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

## 🖥️ NetBridge Applied — Full Config Block

> [!example] R1 — Complete Part 6 Configuration (condensed)

```
! === R1 — All Network Services ===

! DHCP excluded addresses + pools (see Section 1)
ip dhcp excluded-address 10.1.0.1 10.1.0.10
! ... (all excluded ranges)
ip dhcp pool VLAN10_OFFICEA
 network 10.1.0.0 255.255.255.0
 default-router 10.1.0.1
 dns-server 10.5.0.4
 domain-name SankeyLab

! NTP
ntp authenticate
ntp authentication-key 1 md5 0007100805 7
ntp trusted-key 1
ntp master 5

! SNMP + Syslog
snmp-server community JeremysITLabRO RO
logging 10.5.0.4
logging trap debugging
logging buffered 8192

! SSH
ip domain-name SankeyLab
crypto key generate rsa
! [4096 at prompt]
ip ssh version 2

ip access-list standard SSH_ACCESS
 permit 10.1.0.0 0.0.0.255

line vty 0 15
 login local
 transport input ssh
 access-class SSH_ACCESS in
 logging synchronous
 exec-timeout 30 0

! NAT
interface GigabitEthernet0/2
 ip nat outside
interface GigabitEthernet0/3
 ip nat outside
interface GigabitEthernet0/0
 ip nat inside
interface GigabitEthernet0/1
 ip nat inside

ip nat inside source static 10.5.0.4 203.0.113.113

ip access-list standard NAT_SUBNETS
 permit 10.1.0.0 0.0.255.255
 permit 10.2.0.0 0.0.255.255
 permit 10.3.0.0 0.0.255.255
 permit 10.4.0.0 0.0.255.255
 permit 10.5.0.0 0.0.255.255
 permit 10.0.0.0 0.0.255.255

ip nat pool POOL1 203.0.113.200 203.0.113.210 netmask 255.255.255.0
ip nat inside source list NAT_SUBNETS pool POOL1 overload

! CDP → LLDP
no cdp run
lldp run

write memory
```

---

## ✅ Verification Commands

| Command | What to Look For |
|---|---|
| `show ip dhcp binding` | All assigned leases with MAC and IP |
| `show ip dhcp pool` | Pool name, network, utilisation |
| `show ntp status` | Clock is synchronised; stratum matches |
| `show ntp associations` | R1 loopback marked with `*` (synced) |
| `show ip ssh` | SSH enabled, version 2.0 |
| `show ip nat translations` | Static entry for SRV1; dynamic PAT entries for hosts |
| `show ip nat statistics` | Hits counter incrementing for active NAT |
| `show users` | Active SSH sessions on VTY lines |
| `show lldp neighbors` | Replaces CDP output after migration |

---

## ⚠️ Common Pitfalls

> [!warning] Watch Out
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
| Static NAT | 1:1 fixed mapping | `ip nat inside source static <private> <public>` |
| Dynamic PAT | Many:1 with ports | `ip nat inside source list X pool Y overload` |
| NAT inside | Internal (private) interface | LAN-facing interfaces |
| NAT outside | External (public) interface | ISP-facing interfaces |

---

## 🛠️ Practice Tasks

1. **DHCP relay test:** On a PC in VLAN 10, request a DHCP address. Verify on R1 with `show ip dhcp binding` that the lease appears. Remove `ip helper-address` from the SVI and retry — verify DHCP fails. Re-add and confirm recovery.

2. **NTP verification:** Configure NTP on two devices pointing to R1. Wait 60 seconds. Run `show ntp status` — verify `Clock is synchronized`. Change the NTP key passphrase on one device to something wrong — verify it falls out of sync.

3. **SSH lockout test:** Configure the SSH ACL allowing only `10.1.10.0/24`. Try SSH from a host in VLAN 10 — should succeed. Try from VLAN 20 — should be refused. Verify with `show users` on the router.

4. **NAT failover:** Verify hosts can ping an internet IP through ISP A (NAT active). Shut R1's ISP A interface. Verify the floating static route activates and NAT traffic flows through ISP B. Check `show ip nat translations` for active PAT entries via the backup path.
