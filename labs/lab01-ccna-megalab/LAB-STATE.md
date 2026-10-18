# Lab 01 — Configuration Handoff

> Updated by **GitHub Copilot** during the repository-hygiene and documentation-accuracy review.

## Source of truth

The files in `configs/` are the source for claims about configured Cisco state. They are harvested configuration snapshots with authentication directives and SNMP community values redacted. They do not prove that a service, adjacency, failover, or end-to-end path is operational. No credentials or external lab access endpoints belong in this handoff.

## Configured topology

- R1 is the configured edge router; FW1 is not present in the current design.
- CSW1 and CSW2 are configured as a routed Layer 3 core with an inter-switch routed EtherChannel.
- The distribution switches host the documented user/server VLAN SVIs and HSRP configuration.
- The R1-to-core links and inter-switch links are configured for OSPF. Adjacency state is not captured in the repository.
- R1 Gi0/3 obtains its IPv4 address through DHCP and is the configured IPv4 default-route egress. The saved R1 config contains no floating IPv4 static default route.
- IPv6 configuration is present on R1, CSW1, and CSW2 only. R1 has a floating IPv6 default route via Gi0/2; runtime route selection is not captured.

## Known configuration findings

- R1 DHCP pool `A-Mgmt` advertises `10.5.0.4` as the default router; the intended Office A management gateway is `10.0.0.1`.
- DSW-A2 VLAN 10, 20, and 40 SVIs are administratively down. HSRP failover is configured but unverified.
- The ASW-B2 config sets its hostname to `AWS-B2`.
- ASW-B3 has DAI trust configured on a server-facing port.
- VTY ACLs differ by device. R1 and the distribution switches permit `10.1.0.0/24` only. ASW-A1 and ASW-B1/B2/B3 also permit `10.0.0.0/24`; ASW-A2/A3 also permit `10.0.0.0/28`. VLAN 99 is within `10.0.0.0/28`, so those access-switch ACLs do not all block VLAN 99. SSH behavior itself is not independently verified.
- Wireless management on VLAN 99 is reported in older notes, but the repository contains no WLC config or captured show-command output. Treat it as configured, unverified. AP registration and client service are unverified.

## Reported issues without committed test output

- Older handoff notes report that outbound HTTPS/TLS stalls after connection setup and suspect a PNetLab/host MTU or PMTUD issue. No test transcript is committed, and the cause is not established. Keep this as an open, unverified issue.
- Older handoff notes report that WIN-SV1 is a Windows Server 2008 R2 lab-only system at `10.5.0.4` and describe DNS, SMB, and RDP behavior. No server configuration or captured show/scan output is committed, so those service claims remain unverified.

## Scripts

Credential-aware utilities are under `scripts/`. Use `scripts/harvest/README.md` for environment-variable names and usage. The ASW-B collection utility is `scripts/harvest/harvest_aswb_v2.py`.

Never store a real password, secret, SNMP community, PNetLab server address, or SSH forwarding detail in this file. Older Git commits may retain previous lab credentials; those credentials have been changed, and repository history has not been rewritten.
