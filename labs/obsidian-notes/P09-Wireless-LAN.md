---
title: "P09 — Wireless LAN (WLC GUI)"
created: 2025-01-01
updated: 2026-09-21
tags:
  - ccna
  - netbridge
  - networking
  - wireless
  - wlc
  - lwap
  - wpa2
  - ssid
  - dynamic-interface
part: 9
topic: Wireless LAN (WLC GUI)
status: live-verified
lab: CCNA Mega Lab
source: CCNA_Mega_Lab_Step_By_Step_Guide.md
---

# P09 — Wireless LAN (WLC GUI)

> [!info] Part Summary
> **Topic:** Configure a Wi-Fi WLAN through the WLC1 web GUI — create a dynamic interface, build a WLAN with WPA2-AES, and verify LWAPs associate
> **NetBridge Scenario:** Office A needs a wireless network for employees. All the switching infrastructure (VLAN 40, trunks, DHCP pool) was set up in earlier parts. Part 9 completes the wireless side through the WLC's web interface — the way enterprise wireless is actually managed.
> **Key Concepts:** WLC GUI (`https://`), dynamic interface (maps WLAN to VLAN), WLAN (SSID + security), LWAP association, WPA2-AES PSK, CAPWAP tunnel
> **Devices involved:** WLC1, LWAP-A1, LWAP-A2 (access points), wireless clients

---

## 🗺️ Big Picture

> [!tip] Mental Model
> The WLC is the brain — all LWAPs are dumb radios that tunnel all traffic back to the WLC via CAPWAP. The WLC then forwards traffic into the correct VLAN via its dynamic interface. This is why the VLAN config (Part 2), DHCP pool with option 43 (Part 6), and WLC uplink trunk (Part 2) had to be done first.

```
Wireless Client
    ↓ 802.11 Wi-Fi
LWAP (Lightweight AP — just a radio)
    ↓ CAPWAP tunnel (all traffic tunnelled back to WLC)
WLC1 (Wireless LAN Controller)
    ↓ Dynamic Interface (maps WLAN → VLAN 40)
Access Switch trunk → Distribution Switch SVI (VLAN 40, HSRP virtual IP)
    ↓ Routed to DHCP server (R1) for IP assignment
```

**LWAP discovery flow (how APs find the WLC):**
1. LWAP boots → sends DHCP request
2. DHCP response includes **option 43** with WLC IP (`10.1.99.5`)
3. LWAP sends CAPWAP Join Request to WLC IP
4. WLC accepts → LWAP becomes associated and managed centrally

---

## Live Config Evidence (Harvested 2026-09-14)

> [!warning] Design Deviations — Lab Actuals Differ from Plan
> The running lab diverges from the documented design in three ways. The evidence below reflects what is actually configured, not the Packet Tracer walkthrough values.
>
> | Parameter | Planned (Note) | Actual (Running Lab) |
> |---|---|---|
> | WLC management IP | `192.168.30.20` (implicit from docs) | **`10.0.0.7/28`** |
> | Management VLAN | VLAN 40 / VLAN 60 | **VLAN 99** |
> | WLC uplink switch | DSW-A1 | **ASW-A1** |
> | WLC gateway | — | **`10.0.0.1`** |

> [!example] Actual vWLC Wiring — ASW-A1 Port Assignments
>
> | vWLC Port | ASW-A1 Port | Role |
> |---|---|---|
> | `GigabitEthernet0/0` | `Ethernet0/2` | Service / Out-of-band port *(wrong port — caused original outage)* |
> | `GigabitEthernet0/1` | `Ethernet1/1` | Data / Management port ✅ *(correct port — management access confirmed)* |
>
> **Wiring fix lesson:** The vWLC came up unreachable because `g0/0/0` (service/OOB port) was patched instead of `g0/0/1` (data port). The management interface only communicates through the data port. Once the cable was moved to `Ethernet1/1`, management access via VLAN 99 was immediately confirmed.

> [!note] ASW-A1 Trunk Config Supporting the WLC (from running config)
>
> **Ethernet0/2** — vWLC `g0/0/0` (service port, OOB):
> ```
> interface Ethernet0/2
>  switchport trunk allowed vlan 40,99
>  switchport trunk encapsulation dot1q
>  switchport trunk native vlan 1000
>  switchport mode trunk
>  switchport nonegotiate
>  switchport port-security maximum 5
>  ip arp inspection trust
>  spanning-tree portfast edge trunk
>  spanning-tree bpduguard enable
>  ip dhcp snooping limit rate 15
>  ip dhcp snooping trust
> ```
>
> **Ethernet1/1** — vWLC `g0/0/1` (data/management port ✅):
> ```
> interface Ethernet1/1
>  switchport trunk allowed vlan 40,99
>  switchport trunk encapsulation dot1q
>  switchport trunk native vlan 1000
>  switchport mode trunk
>  switchport nonegotiate
>  ip arp inspection trust
>  ip dhcp snooping trust
> ```
>
> Both ports are trunks allowing **VLAN 40 and VLAN 99** — VLAN 99 carries the WLC management interface (`10.0.0.7/28`, gateway `10.0.0.1`).

> [!tip] Key Takeaway
> In this lab the WLC management lives on **VLAN 99** (`10.0.0.x/28` subnet), not on a dedicated wireless management VLAN as the Packet Tracer guide assumes. Always verify the actual management IP and VLAN before attempting GUI access — `https://10.0.0.7` is the correct URL for this deployment.

---

## 📚 Sections

### Section 1 — Access the WLC GUI

> [!note] Key Concept
> The WLC is managed via HTTPS web GUI — not CLI (for this lab). Navigate to the WLC's management IP from a PC on the Management VLAN.

```
! From a browser on a PC in the Management VLAN:
https://10.1.99.5

! Login credentials (set during WLC initial setup)
Username: admin
Password: Cisco123
```

> [!warning] Always Use HTTPS
> HTTP may not be enabled on the WLC by default. Use `https://` — if you get a certificate warning, accept it (self-signed cert in the lab).

---

### Section 2 — Create a Dynamic Interface (VLAN Mapping)

> [!note] Key Concept
> A **dynamic interface** on the WLC maps a WLAN to a specific VLAN — it's the WLC-side configuration that connects Wi-Fi traffic to the wired VLAN infrastructure.

**Navigation:** `Controller` → `Interfaces` → `New`

**Fields to configure:**

| Field | Value |
|---|---|
| Interface Name | `Wi-Fi` |
| VLAN ID | `40` |
| Port Number | `1` (the WLC's physical uplink port) |
| IP Address | `10.1.40.5` (management IP for this interface) |
| Netmask | `255.255.255.0` |
| Gateway | `10.1.40.1` (HSRP virtual IP for VLAN 40) |
| Primary DHCP Server | `10.0.0.76` (R1's loopback) |

**Apply and Save** after entering all fields.

**Why a dynamic interface?**
The WLC itself needs an IP in VLAN 40 so it can communicate on that VLAN (for management and DHCP relay). The WLC's physical port is a trunk — the dynamic interface adds VLAN 40 to that trunk logically.

---

### Section 3 — Create the WLAN

> [!note] Key Concept
> A **WLAN** is the WLC-side definition of an 802.11 wireless network — it defines the SSID, security, and which dynamic interface (VLAN) traffic goes to.

**Navigation:** `WLANs` → `Create New` → `Go`

**General tab:**

| Field | Value |
|---|---|
| Profile Name | `Wi-Fi` |
| SSID | `Wi-Fi` |
| WLAN ID | `1` |
| Admin Status | `Enabled` |
| Interface/Group | `Wi-Fi` (the dynamic interface created above) |

**Security tab → Layer 2:**

| Field | Value |
|---|---|
| Layer 2 Security | `WPA+WPA2` |
| WPA2 Policy | `Enabled` |
| WPA2 Encryption | `AES` (CCMP — strongest option) |
| Auth Key Mgmt | `PSK` (pre-shared key) |
| PSK Format | `ASCII` |
| Pre-Shared Key | `JeremysITLab` (or whatever the lab specifies) |

**Advanced tab:**
- Ensure the WLAN is not mapped to the Management interface — it should use the Wi-Fi dynamic interface
- P2P blocking: disabled for basic operation

**Apply and Save.**

> [!warning] WPA2-AES vs. WPA-TKIP
> **WPA2 with AES (CCMP)** is the current standard — use this. WPA with TKIP is deprecated and weak. In the WLC GUI, ensure WPA2 checkbox is ticked and AES is selected under encryption.

---

### Section 4 — Verify LWAP Association

> [!note] Key Concept
> After configuring the WLAN, lightweight APs should automatically discover the WLC (via option 43 from DHCP) and associate. Verify in the WLC GUI under the Monitor tab.

**Navigation:** `Monitor` → `Summary` → check AP count

**Navigation:** `Wireless` → `Access Points` → `Summary`
- Both LWAP-A1 and LWAP-A2 should appear with status `Registered`

**What to look for:**
- AP Name
- AP Model
- Status: **Registered** (not Disconnected)
- IP Address: should have received IP from DHCP Management pool

**If an AP isn't showing up, check:**
1. Is `option 43` in the Management VLAN DHCP pool on R1?
2. Is the LWAP's port connected to an access port on VLAN 99 (Management)?
3. Is the trunk between the access switch and distribution switch carrying VLAN 99?
4. Is the WLC uplink port configured as a trunk with VLAN 40 and 99 allowed?

---

### Section 5 — Save WLC Configuration

> [!note] Key Concept
> The WLC has its own save mechanism — completely separate from `write memory` on IOS devices. Always save through the GUI.

**Navigation:** `Commands` → `Save Configuration` → `Save`

This is the WLC equivalent of `write memory` — without it, config is lost on WLC reboot.

---

### Section 6 — Known Packet Tracer Limitation

> [!note] Key Concept
> A specific Packet Tracer limitation applies to wireless DHCP — worth knowing so you don't chase a ghost problem.

> [!warning] Packet Tracer Wireless DHCP Limitation
> In Packet Tracer, wireless clients connecting to the Wi-Fi WLAN may receive an IP from the **Management VLAN pool** (`10.1.99.x`) instead of the **Wi-Fi VLAN 40 pool** (`10.1.40.x`). This is a **simulator limitation, not a configuration error**. In a real network with real hardware, clients would correctly receive IPs from the Wi-Fi DHCP pool. **Do not reconfigure DHCP or change the dynamic interface trying to fix this** — it cannot be fixed in Packet Tracer.

---

## 🖥️ NetBridge Applied — GUI Click-Through Summary

> [!example] Complete Part 9 — Step-by-Step GUI

```
Step 1: Open browser → https://10.1.99.5 → Login (admin / Cisco123)

Step 2: Create Dynamic Interface
  Controller → Interfaces → [New]
  Name: Wi-Fi
  VLAN: 40
  Port: 1
  IP: 10.1.40.5 / 255.255.255.0
  Gateway: 10.1.40.1
  DHCP: 10.0.0.76
  [Apply]

Step 3: Create WLAN
  WLANs → [Create New] → [Go]
  Profile/SSID: Wi-Fi
  ID: 1
  Status: Enabled
  Interface: Wi-Fi
  [Apply]

  Security tab:
  Layer 2: WPA+WPA2
  WPA2: Enabled
  Encryption: AES
  Auth: PSK
  Key: JeremysITLab
  [Apply]

Step 4: Verify AP Association
  Monitor → Summary → check AP Count = 2
  Wireless → Access Points → confirm LWAP-A1 and LWAP-A2 show Registered

Step 5: Save WLC Config
  Commands → Save Configuration → [Save]
```

---

## ✅ Verification Checklist

| Check | Location | Expected Result |
|---|---|---|
| Dynamic interface created | Controller → Interfaces | `Wi-Fi` interface with VLAN 40 |
| WLAN created and enabled | WLANs → Summary | `Wi-Fi` WLAN, Status: Enabled |
| WLAN security | WLANs → Wi-Fi → Security | WPA2, AES, PSK |
| WLAN interface binding | WLANs → Wi-Fi → General | Interface: Wi-Fi (not Management) |
| AP association | Wireless → Access Points | LWAP-A1, LWAP-A2 both Registered |
| Config saved | Commands → Save Config | No unsaved changes |

---

## ⚠️ Common Pitfalls

> [!warning] Watch Out
> - **Using HTTP instead of HTTPS** — WLC GUI may only be available via HTTPS; browser will show security warning (accept it)
> - **WLAN mapped to Management interface** — all wireless traffic would go into VLAN 99; should use the `Wi-Fi` dynamic interface (VLAN 40)
> - **WPA2 not enabled, only WPA** — WPA-TKIP is deprecated; verify WPA2 + AES (CCMP) is selected, not WPA + TKIP
> - **Forgetting to Save in WLC GUI** — WLC config is RAM-based; must use Commands → Save or config is lost on reboot
> - **LWAPs not associating** — check: option 43 in DHCP pool, Management VLAN trunked to access switch, LWAP port on VLAN 99 access port
> - **Chasing the Packet Tracer DHCP bug** — wireless clients getting 10.1.99.x IPs is a simulator limitation; it's not fixable in PT; move on

---

## 📊 Concepts Summary

| Concept | What It Does | Exam Tip |
|---|---|---|
| WLC (Wireless LAN Controller) | Central brain that manages all LWAPs | GUI-managed; not CLI for this lab |
| LWAP (Lightweight AP) | Dumb radio; tunnels all traffic to WLC | Discovers WLC via DHCP option 43 |
| CAPWAP | Tunnel protocol between LWAP and WLC | Control + data tunnelled back to WLC |
| Dynamic Interface | WLC mapping of WLAN → VLAN | One dynamic interface per WLAN/VLAN |
| WLAN | SSID + security policy on the WLC | Bound to a dynamic interface |
| WPA2-AES | Wi-Fi security — current standard | WPA2 + AES (CCMP); WPA + TKIP is deprecated |
| PSK (Pre-Shared Key) | Wi-Fi password for WPA2 Personal | Alternative to 802.1X (enterprise auth) |
| option 43 | DHCP option: tells LWAPs the WLC IP | Must be in Management VLAN DHCP pool |
| Save Configuration (GUI) | WLC equivalent of `write memory` | Commands → Save Configuration |

---

## 🛠️ Practice Tasks

1. **LWAP discovery trace:** Remove `option 43` from the Management VLAN DHCP pool on R1. Reboot a LWAP. Observe it failing to associate (check WLC Monitor → AP count = 0). Re-add option 43 and verify the LWAP re-associates.

2. **WLAN security comparison:** Create two WLANs — one with WPA + TKIP and one with WPA2 + AES. Connect a wireless client to each. Verify both work. Then explain why WPA-TKIP is considered insecure and should be avoided in production.

3. **Dynamic interface troubleshooting:** Change the dynamic interface to map to VLAN 50 (a VLAN that doesn't exist). Observe wireless clients failing to get IPs. Change back to VLAN 40 and verify recovery.

4. **Full wireless path trace:** Connect a wireless client to the Wi-Fi SSID. Trace the full path: client → LWAP → CAPWAP → WLC → dynamic interface → VLAN 40 trunk → DSW-A SVI → DHCP relay → R1 → DHCP pool → IP assigned. Verify at each stage.

---

## 🎓 Lab Complete — NetBridge Deployment Summary

> [!info] What Was Built Across 9 Parts

| Part | What Was Configured |
|---|---|
| P01 | Hostname, enable secret, local user, console login — every device |
| P02 | EtherChannel (PAgP/LACP), trunking, DTP disabled, native VLAN, VTP, VLANs, access ports |
| P03 | `ip routing`, SVIs, L3 EtherChannel, loopbacks, HSRP v2 (split active/standby) |
| P04 | Rapid PVST+, STP root = HSRP active per VLAN, PortFast + BPDU Guard |
| P05 | OSPF Area 0, passive interfaces, point-to-point links, dual default routes, floating static, `default-information originate` |
| P06 | DHCP pools + relay, NTP auth, SNMP, Syslog, FTP IOS upgrade, SSH v2 + ACL, static NAT + PAT, CDP→LLDP |
| P07 | Extended ACL (both HSRP switches), Port Security (sticky, restrict), DHCP Snooping (no option 82), DAI |
| P08 | `ipv6 unicast-routing`, three addressing methods (manual/EUI-64/link-local), IPv6 floating static |
| P09 | WLC dynamic interface (VLAN 40), WLAN (WPA2-AES PSK), LWAP association, save config |

> [!tip] Jeremy's Grading Reminders
> 1. `write memory` on **every device** after every part
> 2. Match **names exactly** — hostnames, ACL names, VTP domain, pool names
> 3. If under 100%: *Check Results → Assessment Items → Show Incorrect Items*
