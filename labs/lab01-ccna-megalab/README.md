# Lab 01 — CCNA Megalab

**Author:** Sankey Silva | CCNA | JNCIA | ISC2 CC | MSc Cybersecurity  
**Platform:** ![PNetLab](https://img.shields.io/badge/Platform-PNetLab-blue)  
**Reference:** [Jeremy's IT Lab — CCNA Mega Lab](https://www.youtube.com/watch?v=2p7-MluKAgE)  
**Repo:** [multi-vendor-labs](https://github.com/Sankey-nz/multi-vendor-labs)

---

## Topology

![Logical and physical topology for the two-office SankeyLab scenario.](topology/topology.png)

The diagram shows the virtual lab topology across Office A and Office B. Both sites connect through a shared routed core (CSW1/CSW2) and edge router (R1). Each office has a distribution pair, access switches, and end hosts. Office A includes the Cisco vWLC; Office B includes WIN-SV1 for domain, DNS, NTP, and file services. DHCP is provided by R1 in the current live configuration.

### Reading this lab

1. Read the scenario and follow the diagram from R1 through the routed core to a site's distribution and access layers.
2. Use [`addressing-table.md`](addressing-table.md) for the harvested IPv4/IPv6 addresses, VLAN purposes, and known live exceptions.
3. Follow Parts 1–9 for the concepts and example commands. The examples explain the intended learning task; they are not all a transcript of the current lab.
4. Compare examples with [`configs/`](configs/) before configuring a device. Configuration presence alone does not prove that a feature works end to end.

The lab is a learning environment, not a production deployment. Some exercises describe a design target, while the harvested configs and notes record what is actually present. Each status below distinguishes documented configuration from behavior that remains unverified.

---

## Business Problem and Engineering Request

**Scenario:** SankeyLab is a fictional company operating from two offices. It needs reliable communication between sites, separate networks for users, staff/voice, servers, wireless clients, and network management, and access to shared services and the Internet. The design must include redundancy, controlled access, and a way to verify and troubleshoot failures.

**Engineering request:** Plan the IPv4 subnets and VLANs; build the routed and switched topology; configure redundancy, routing, services, security, IPv6, and wireless; then verify end-to-end connectivity and diagnose injected faults. The nine study parts break this work into manageable stages rather than isolated protocol demonstrations.

This is a virtual lab built with PNetLab and Cisco IOL/IOSv software images—not a physical hardware deployment. The images are not distributed in this repository. Configurations use Cisco IOS-style commands, while the live-state notes call out where the current virtual lab differs from the original design or from a fully validated production network.

---

## Build Requirements and Current Status

The status column describes harvested configuration and verification evidence; it does not claim production readiness. Known live-state limitations are called out below.

| Part | Topic | Engineering task | Recorded status | Guide |
|------|-------|----------|--------|-------|
| 1 | Initial Device Setup | Hostnames, SSH, local authentication, CDP/LLDP | Baseline configuration is documented; see harvested configs for device-specific settings | [P01](../obsidian-notes/P01-Initial-Setup.md) |
| 2 | VLANs & L2 EtherChannel | VLAN membership, 802.1Q trunks, PAgP/LACP | VLANs, trunks, and distribution EtherChannels are present in the harvested configs; VTP use is not assumed | [P02](../obsidian-notes/P02-VLANs-and-L2-EtherChannel.md) |
| 3 | IP Addressing & L3 EtherChannel | Routed links, SVIs, HSRP | IPv4/HSRP configuration is documented; Office A user SVIs on DSW-A2 are administratively down in the recorded config | [P03](../obsidian-notes/P03-IP-Addressing-L3-EtherChannel-HSRP.md) |
| 4 | Spanning Tree | Rapid PVST+, root placement, PortFast, BPDU Guard | Configured settings are documented; verify operational state on the devices | [P04](../obsidian-notes/P04-Rapid-Spanning-Tree.md) |
| 5 | Routing | OSPFv2 Area 0 and default-route advertisement | OSPF and default-information originate are configured; IPv4 default route uses DHCP on R1 Gi0/3, with no IPv4 floating static route in the harvested config | [P05](../obsidian-notes/P05-OSPF-and-Static-Routing.md) |
| 6 | Network Services | DHCP, DNS, NTP, SNMP, Syslog, SSH, PAT | DHCP is configured on R1; DNS is provided by WIN-SV1; current NAT is PAT via Gi0/3. Consult P06 for verification gaps | [P06](../obsidian-notes/P06-Network-Services.md) |
| 7 | Security | ACLs, port security, DHCP snooping, DAI | ACLs and L2 controls are configured unevenly; P07 records the observed scope and limitations | [P07](../obsidian-notes/P07-Security.md) |
| 8 | IPv6 | IPv6 addressing and static routes | IPv6 is configured on R1 and the core switches only; distribution/access IPv6 and end-to-end IPv6 are not documented as verified | [P08](../obsidian-notes/P08-IPv6.md) |
| 9 | Wireless | vWLC management, WLAN/VLAN concepts, CAPWAP | WLC management on VLAN 99 is confirmed; AP registration and wireless-client service are unverified | [P09](../obsidian-notes/P09-Wireless-LAN.md) |

---

## Live Topology Notes

Deviations from the original lab design, confirmed against harvested running configs (September 2026):

**WAN & Routing**
- **Edge Connectivity:** R1 connects directly to ISP-B via Gi0/3 (DHCP).
- **Default Gateway:** Default route is `ip route 0.0.0.0 0.0.0.0 GigabitEthernet0/3 dhcp`.

**Core Architecture**
- **Pure L3 Core:** CSW1 and CSW2 function as a purely routed core.
- **SVI Placement:** No SVIs or HSRP on core switches; all VLAN SVIs and HSRP virtual IPs reside on the DSW distribution layer.

**Device Specifics**
- **WLC1 Management:** Live IP is `10.0.0.7/28` on VLAN 99 (connected to ASW-A1), replacing the original `192.168.30.20/24` on VLAN 60.
- **DHCP Services:** All pools (A-Mgmt, A-PC, A-Phone, B-Mgmt, B-PC, Wi-Fi) are hosted on R1 rather than WIN-SV1.

---

## Device Inventory

| Device | Hostname | Image | Role |
|--------|----------|-------|------|
| Edge Router | R1 | vios-adventerprisek9-m.SPA.158-3.M2 | OSPF ASBR, PAT, DHCP server, default route |
| Core L3 Switch | CSW1 | L3-IOL-15.4-2T | Pure L3 routed core — OSPF, L3 EtherChannel |
| Core L3 Switch | CSW2 | L3-IOL-15.4-2T | Pure L3 routed core — OSPF, L3 EtherChannel |
| Distribution Switch | DSW-A1 | L2-IOL-high_iron_20180510 | Office A — STP root, HSRP active (VLAN 10/99) |
| Distribution Switch | DSW-A2 | L2-IOL-high_iron_20180510 | Office A — STP secondary, HSRP active (VLAN 20/40) |
| Distribution Switch | DSW-B1 | L2-IOL-high_iron_20180510 | Office B — STP root, HSRP active (VLAN 10/99) |
| Distribution Switch | DSW-B2 | L2-IOL-high_iron_20180510 | Office B — STP secondary, HSRP active (VLAN 20/30) |
| Access Switch | ASW-A1 | L2-IOL-15.2d | Office A — PC1, WLC1 uplink |
| Access Switch | ASW-A2 | L2-IOL-15.2d | Office A — PC2 |
| Access Switch | ASW-A3 | L2-IOL-15.2d | Office A — PC3 |
| Access Switch | ASW-B1 | L2-IOL-15.2d | Office B — PC4 |
| Access Switch | ASW-B2 | L2-IOL-15.2d | Office B — PC5 |
| Access Switch | ASW-B3 | L2-IOL-15.2d | Office B — PC6, WIN-SV1 |
| Wireless LAN Controller | WLC1 | vwlc-8.7.102 | WLAN management (10.0.0.7/28, VLAN 99) |
| Windows Server | WIN-SV1 | winserver-S2008-R2-x64 | AD/DC, DNS, NTP, FTP (10.5.0.4, VLAN 30) |
| Management Host | Kali | Kali Linux | Management access, fault injection, packet capture |

---

## Skills Demonstrated

**Routing & L3 Services**
- **OSPFv2:** Area 0, passive interfaces, `default-information originate`.
- **L3 Connectivity:** Static routing, PAT/NAT overload, IPv6 dual-stack (EUI-64), static IPv6 routes.

**Switching & L2 Topology**
- **VLANs:** 802.1Q trunking, site-specific VLANs, Rapid PVST+ (STP); VTP is a study concept, not explicitly configured in the harvested configs.
- **Link Aggregation:** EtherChannel (LACP & PAgP), L2 and L3 channels.
- **Redundancy:** HSRP active/standby group distribution across DSW pairs.

**Security & Network Services**
- **Hardening:** SSHv2, Port Security (sticky MAC), Extended Named ACLs.
- **L2 Security:** DHCP Snooping, Dynamic ARP Inspection (DAI).
- **Infrastructure Services:** DHCP relay (`ip helper-address`), DNS, NTP authentication settings, SNMP v2c, Syslog. End-to-end service operation is not uniformly verified; an FTP-based IOS upgrade is a guide exercise, not a confirmed lab action.

**Wireless & Troubleshooting**
- **Cisco vWLC:** 8.7 version and VLAN 99 management confirmed; WLAN/VLAN mapping, CAPWAP registration, and WPA2 client service are not verified.
- **Diagnostics:** Structured fault injection (8 scenarios), OSI-layer isolation methodology.

---

## Repository Structure

```
multi-vendor-labs/
├── README.md
└── labs/
    ├── obsidian-notes/              ← per-part study notes (P01–P09)
    └── lab01-ccna-megalab/
        ├── README.md                ← this file
        ├── addressing-table.md      ← live-verified IP addressing
        ├── LAB-STATE.md             ← current lab state and access notes
        ├── topology/
        │   └── topology.png
        ├── configs/                 ← 13 device running configs (live harvested)
        │   ├── R1.txt
        │   ├── CSW1.txt  CSW2.txt
        │   ├── DSW-A1.txt  DSW-A2.txt  DSW-B1.txt  DSW-B2.txt
        │   └── ASW-A1.txt  ASW-A2.txt  ASW-A3.txt
        │       ASW-B1.txt  ASW-B2.txt  ASW-B3.txt
        └── scripts/
            ├── harvest/             ← Netmiko config collection scripts
            └── troubleshooting/     ← SSH and connectivity test scripts
```

---

## References

- [Jeremy's IT Lab — CCNA Mega Lab](https://www.youtube.com/watch?v=2p7-MluKAgE)
- [PNetLab Documentation](https://pnetlab.com/pages/documentation)
- [Cisco IOS Configuration Guides](https://www.cisco.com/c/en/us/support/index.html)

---

*Built as part of the [multi-vendor-labs](https://github.com/Sankey-nz/multi-vendor-labs) portfolio by Sankey Silva — Auckland, NZ.*
