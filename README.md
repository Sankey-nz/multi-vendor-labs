# multi-vendor-labs

> Hands-on network engineering labs using virtual vendor network operating systems — by Sankey Silva

**Sankey Silva** | CCNA · JNCIA · ISC2 CC · MSc Cybersecurity | Auckland, NZ

---

## About

This repository documents practical network engineering labs built in PNetLab with virtual Cisco IOL and IOSv devices. The labs use Cisco IOS-style configuration and real routing and switching protocols inside a virtual topology; they are not physical hardware deployments. The goal is to connect network design decisions to configuration, verification, and troubleshooting.

### The business problem

The first scenario is a fictional growing company, SankeyLab, with two offices. It needs a network that can:

- Separate user, staff/voice, server, wireless, and management traffic.
- Keep office connectivity available through redundant distribution switches and routed paths.
- Provide shared DHCP, DNS, time, and file services, plus controlled Internet access.
- Support secure device management, wireless access, and IPv4/IPv6 learning objectives.
- Be diagnosable when links, VLANs, routing, or security controls are misconfigured.

The engineering task is to turn those needs into an address and VLAN plan, build the topology, configure the network services and controls, and prove the intended paths with operational checks. Each lab documents the design brief, implementation guides, device configurations, and known differences between the intended design and the current lab state.

---

## Labs

| Lab | Platform | Status | Description |
|-----|----------|--------|-------------|
| [Lab 01 — CCNA Megalab](./labs/lab01-ccna-megalab) | PNetLab + Cisco IOL/IOSv | Built; live-state notes included | Two-office enterprise scenario for VLANs, subnetting, switching, routing, services, security, IPv6, wireless, and troubleshooting |
| Lab 02 *(planned)* | — | Planned | — |

The [Lab 01 topology diagram](./labs/lab01-ccna-megalab/topology/topology.png) shows the device and link layout. Its [addressing table](./labs/lab01-ccna-megalab/addressing-table.md) explains the subnet sizes, masks, and allocations.

---

## Tools & Stack

- **Emulation:** PNetLab
- **Virtual network OS images:** Cisco IOL, Cisco IOSv (images are not included in this repository)
- **Automation:** Python, Netmiko, Paramiko
- **Security:** Kali Linux
- **Infrastructure:** Windows Server 2008 R2

---

## Author

**Sankey Silva**
- LinkedIn: [linkedin.com/in/sankey-silva](https://www.linkedin.com/in/sankey-silva/)
- GitHub: [github.com/Sankey](https://github.com/Sankey)
