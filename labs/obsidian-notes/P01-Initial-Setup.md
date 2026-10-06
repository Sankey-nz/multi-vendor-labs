# P01 — Initial Setup & Device Hardening

> [!NOTE] Part Summary
> **Topic:** Baseline security hardening on every router and switch before any network config
> **SankeyLab Scenario:** Before configuring VLANs or routes, establish a consistent identity and secure management access on each network device.
> **Key Concepts:** `hostname`, `enable secret` (type 9 vs type 5), local user accounts, console line security, `write memory`
> **Devices involved:** R1, CSW1, CSW2, DSW-A1, DSW-A2, DSW-B1, DSW-B2, ASW-A1, ASW-A2, ASW-A3, ASW-B1, ASW-B2

---

## 🗺️ Big Picture

> [!TIP] Mental Model
> Part 1 establishes a baseline: identify the device, secure administrative access, and save the configuration. No VLAN or routing changes are made here.

```
Every device in the topology:
  hostname → use the agreed device name
  enable secret → encrypted privileged access
  local user → console login requires credentials
  console line → forces local login
  write memory → saves the current running-config to startup-config
```

> [!WARNING] Save Deliberately
> `write memory` saves the current running configuration so it persists after a restart. In a live lab, save after a verified change; do not assume an external grader or evaluator is present.

---

## 📚 Sections

### Section 1 — Hostname

> [!NOTE] Key Concept
> Use one consistent hostname per device so command output, diagrams, and configuration files can be correlated. IOS hostnames are case-preserving; case alone is not normally a functional difference.

```
hostname DSW-A1
```

**Why it matters:** Clear names reduce mistakes when connecting to multiple devices and make logs easier to interpret.

---

### Section 2 — Enable Secret (Privileged Mode Password)

> [!NOTE] Key Concept
> `enable secret` hashes the password before storing it in the config — unlike `enable password` which stores it in plaintext (or weak Type 7 reversible encoding). Use **type 9** (SCRYPT) if the platform supports it.

```
! Type 9 (SCRYPT — strongest, use if supported)
enable algorithm-type scrypt secret class

! Type 5 (MD5 — fallback for older platforms)
enable secret class
```

**Type 9 vs Type 5:**

| Type | Algorithm | Strength |
|---|---|---|
| Type 5 | MD5 | Weak — offline crackable |
| Type 8 | PBKDF2-SHA256 | Strong |
| **Type 9** | **SCRYPT** | **Strongest — use this** |

> [!WARNING] Exam Flag
> `enable secret` always wins over `enable password` if both are configured. In the config you'll see `enable secret 9 $9$...` for SCRYPT or `enable secret 5 $1$...` for MD5.

---

### Section 3 — Local User Account

> [!NOTE] Key Concept
> A local user account can authenticate console or SSH access. Choose a unique, strong secret for your own lab; do not reuse credentials from examples or publish real secrets in configuration files.

```
! Example only: replace the placeholders with your lab's non-reused credentials.
username <local-user> privilege 15 algorithm-type scrypt secret <strong-secret>
```

**`privilege 15`** gives the user immediate exec-level access without needing `enable` — useful for SSH management (Part 6).

---

### Section 4 — Console Line Hardening

> [!NOTE] Key Concept
> By default the console line has no password — anyone with physical access gets in. `login local` forces credential verification against the local user database.

```
line console 0
  login local
  logging synchronous
  exec-timeout 30 0
```

**`logging synchronous`** — prevents syslog messages from interrupting mid-command. **`exec-timeout 30 0`** — logs out idle sessions after 30 minutes (security hygiene).

---

### Section 5 — Save Configuration

> [!NOTE] Key Concept
> These commands save running-config to startup-config (NVRAM). Use a form supported by the device and verify the save succeeded.

```
! Option 1 — full form
copy running-config startup-config

! Option 2 — shorthand
write memory

! Option 3 — even shorter (from any mode with 'do')
do write
```

> [!TIP] Verify the Save
> After saving, compare the relevant section of `show running-config` and `show startup-config`. Saving does not verify that the configuration is correct or operational.

---

### Section 6 — Discovery Protocols (CDP & LLDP)

> [!NOTE] Key Concept
> Discovery protocols allow devices to share information (hostname, IP, capabilities) with neighbors. **CDP** is Cisco proprietary; **LLDP** is the industry standard (IEEE 802.1AB) used for multi-vendor environments.

```
! Enable LLDP globally (standard)
lldp run

! Disable CDP on specific untrusted interfaces (Security best practice)
interface GigabitEthernet0/0
  no cdp enable
```

**Why it matters:** In a real network, you use these to map the topology without having to log into every device. However, leaving CDP/LLDP active on WAN interfaces is a security risk (information leakage).

---



## 🖥️ NetBridge Applied — Full Config Block

> [!TIP] Part 1 — Baseline Example (adapt for the device and image)

```
! === INITIAL SETUP — apply to EVERY device ===

! Step 1: Set hostname (match topology diagram exactly)
hostname DSW-A1

! Step 2: Privileged mode password
enable algorithm-type scrypt secret class

! Step 3: Local user account
! Use placeholders; configure a unique, strong secret locally.
username <local-user> privilege 15 algorithm-type scrypt secret <strong-secret>

! Step 4: Secure the console line
line console 0
 login local
 logging synchronous
 exec-timeout 30 0
 exit

! Step 5: Discovery Protocols
lldp run
! (Note: cdp is on by default, disable on WAN interfaces manually)

! Step 6: SAVE — do this before moving to any other device
write memory
```

**Device hostname reference:**

| Device | Hostname |
|---|---|
| Edge router | R1 |
| Core switches | CSW1, CSW2 |
| Distribution (Office A) | DSW-A1, DSW-A2 |
| Distribution (Office B) | DSW-B1, DSW-B2 |
| Access (Office A) | ASW-A1, ASW-A2, ASW-A3 |
| Access (Office B) | ASW-B1, ASW-B2 |
| Wireless controller | WLC1 |
| Server | SRV1 |

---

## ✅ Verification Commands

| Command | What to Look For |
|---|---|
| `show running-config \| include hostname` | Expected device name |
| `show running-config \| include enable secret` | `enable secret 9 $9$...` (Type 9) or `enable secret 5 $1$...` (Type 5) |
| `show running-config \| include username` | The intended local username and a hashed secret; never paste the full output into a public report |
| `show running-config \| section line con` | `login local` present |
| `show startup-config \| include hostname` | Confirms the saved hostname matches the running configuration |
| `show cdp neighbors` | Confirms Cisco neighbor visibility |
| `show lldp neighbors` | Confirms multi-vendor neighbor visibility |

---

## ⚠️ Common Pitfalls

> [!WARNING] Watch Out
> - **Wrong hostname** — confirm you are connected to the intended device before making changes
> - **`enable password` instead of `enable secret`** — stores password in plaintext or weak Type 7; always use `enable secret`
> - **Forgetting `write memory`** — most common single cause of lost points; make it a reflex after every device
> - **`login` instead of `login local`** — `login` requires a line password set with `password <pw>`; `login local` uses the username/password database (which is what you want)
> - **Configuring the wrong device** — always confirm `show version` or check the hostname prompt before entering config mode

---

## 📊 Concepts Summary

| Concept | What It Does | Exam Tip |
|---|---|---|
| `hostname` | Sets the device name shown in the prompt | Use the agreed name consistently in diagrams and configs |
| `enable secret` | Hashed privileged password | Always beats `enable password`; Type 9 > Type 5 |
| `username privilege 15 secret` | Local user with full admin rights | Needed for `login local` on console and SSH |
| `login local` | Require username/password on console | Use `login local` not bare `login` |
| `logging synchronous` | Prevents syslog messages interrupting typing | Best practice on all line configs |
| `write memory` | Save running-config → startup-config | Verify after saving; unsaved changes can be lost on restart |
| `copy running-config startup-config` | Identical to `write memory` | Three equivalent forms — all do the same thing |
| startup-config | Config loaded on boot (NVRAM) | Persists saved changes across restarts |
| running-config | Active config in RAM | Lost on reboot if not saved |
| `cdp` | Cisco discovery protocol | Default on; disable on WAN interfaces for security |
| `lldp` | Industry standard discovery | Must be enabled manually with `lldp run` |

---

## 🛠️ Practice Tasks

1. **Hostname drill:** Configure all 9 devices with correct hostnames from memory. Verify each with `show running-config | include hostname`. Common mistake: forgetting a hyphen or getting the case wrong.

2. **Password types:** In an isolated lab, set `enable password <weak-test-password>` then `enable secret <strong-test-password>`. Exit to user exec and try `enable`. Which password works? Then check `show running-config` — what do you see for each? Remove `enable password` and explain why it's redundant.

3. **Console lockout simulation:** Configure `login local` on the console. Disconnect and reconnect — confirm you're prompted for username and password. Try a wrong password — verify it's rejected.

4. **Save verification:** Make a config change (add a banner), do NOT save, and reload. Verify the change is gone. Then make the same change, do `write memory`, reload, and verify it persists. This proves why saving matters.
