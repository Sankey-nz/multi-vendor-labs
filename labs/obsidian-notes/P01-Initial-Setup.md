# P01 — Initial Setup & Device Hardening

> [!NOTE] Part Summary
> **Topic:** Baseline security hardening on every router and switch before any network config
> **NetBridge Scenario:** Before touching a single VLAN or route, NetBridge's security policy requires every device to be named, password-protected, and locked down. This is the foundation every other part builds on.
> **Key Concepts:** `hostname`, `enable secret` (type 9 vs type 5), local user accounts, console line security, `write memory`
> **Devices involved:** R1, CSW1, CSW2, DSW-A1, DSW-A2, DSW-B1, DSW-B2, ASW-A1, ASW-A2, ASW-A3, ASW-B1, ASW-B2

---

## 🗺️ Big Picture

> [!TIP] Mental Model
> Part 1 is pure hygiene — no routing, no VLANs, just making sure every device has an identity and a locked front door. Do this wrong and the grader can't even verify the hostname.

```
Every device in the topology:
  hostname → must match diagram exactly (grader checks this)
  enable secret → encrypted privileged access
  local user → console login requires credentials
  console line → forces local login
  write memory → saves to startup-config (grader reads THIS, not running-config)
```

> [!WARNING] The One Rule That Matters Everywhere
> **`write memory` after every device.** The grader only reads **startup-config** (what loads on boot). A perfect running-config that hasn't been saved scores zero.

---

## 📚 Sections

### Section 1 — Hostname

> [!NOTE] Key Concept
> The hostname must match the topology diagram **exactly** — case-sensitive. The grader is literal; `dsw-a1` and `DSW-A1` are treated as different.

```
hostname DSW-A1
```

**Why it matters:** The grader checks `show running-config | include hostname` against its expected value. One wrong character = zero points for that check.

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
> A local user account provides credential-based login for console (and later SSH) access. The username and password must match what the grader expects — use the lab's specified credentials.

```
username cisco privilege 15 algorithm-type scrypt secret CCNA
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
> Three equivalent ways to save — all write running-config to startup-config (NVRAM). Pick one, use it consistently.

```
! Option 1 — full form
copy running-config startup-config

! Option 2 — shorthand
write memory

! Option 3 — even shorter (from any mode with 'do')
do write
```

> [!WARNING] Never Skip This
> The grader reads startup-config only. If you configure 100 things and forget to save, you score 0. Build `write memory` into muscle memory — type it after every device, every part.

---

## 🖥️ NetBridge Applied — Full Config Block

> [!TIP] Part 1 — Repeat on Every Device (substituting the correct hostname)

```
! === INITIAL SETUP — apply to EVERY device ===

! Step 1: Set hostname (match topology diagram exactly)
hostname DSW-A1

! Step 2: Privileged mode password
enable algorithm-type scrypt secret class

! Step 3: Local user account
username cisco privilege 15 algorithm-type scrypt secret CCNA

! Step 4: Secure the console line
line console 0
 login local
 logging synchronous
 exec-timeout 30 0
 exit

! Step 5: SAVE — do this before moving to any other device
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
| `show running-config \| include hostname` | Exact match to topology diagram name |
| `show running-config \| include enable secret` | `enable secret 9 $9$...` (Type 9) or `enable secret 5 $1$...` (Type 5) |
| `show running-config \| include username` | `username jeremy privilege 15 secret 9 ...` |
| `show running-config \| section line con` | `login local` present |
| `show startup-config \| include hostname` | Confirms `write memory` was done — if this differs from running-config, you forgot to save |

---

## ⚠️ Common Pitfalls

> [!WARNING] Watch Out
> - **Wrong hostname case** — `dsw-a1` fails if grader expects `DSW-A1`; match the topology diagram exactly
> - **`enable password` instead of `enable secret`** — stores password in plaintext or weak Type 7; always use `enable secret`
> - **Forgetting `write memory`** — most common single cause of lost points; make it a reflex after every device
> - **`login` instead of `login local`** — `login` requires a line password set with `password <pw>`; `login local` uses the username/password database (which is what you want)
> - **Configuring the wrong device** — always confirm `show version` or check the hostname prompt before entering config mode

---

## 📊 Concepts Summary

| Concept | What It Does | Exam Tip |
|---|---|---|
| `hostname` | Sets the device name shown in the prompt | Must match topology exactly — grader is case-sensitive |
| `enable secret` | Hashed privileged password | Always beats `enable password`; Type 9 > Type 5 |
| `username privilege 15 secret` | Local user with full admin rights | Needed for `login local` on console and SSH |
| `login local` | Require username/password on console | Use `login local` not bare `login` |
| `logging synchronous` | Prevents syslog messages interrupting typing | Best practice on all line configs |
| `write memory` | Save running-config → startup-config | Grader reads startup-config ONLY |
| `copy running-config startup-config` | Identical to `write memory` | Three equivalent forms — all do the same thing |
| startup-config | Config loaded on boot (NVRAM) | What the grader checks |
| running-config | Active config in RAM | Lost on reboot if not saved |

---

## 🛠️ Practice Tasks

1. **Hostname drill:** Configure all 9 devices with correct hostnames from memory. Verify each with `show running-config | include hostname`. Common mistake: forgetting a hyphen or getting the case wrong.

2. **Password types:** On a router, set `enable password cisco` then `enable secret class`. Exit to user exec and try `enable`. Which password works? Then check `show running-config` — what do you see for each? Remove `enable password` and explain why it's redundant.

3. **Console lockout simulation:** Configure `login local` on the console. Disconnect and reconnect — confirm you're prompted for username and password. Try a wrong password — verify it's rejected.

4. **Save verification:** Make a config change (add a banner), do NOT save, and reload. Verify the change is gone. Then make the same change, do `write memory`, reload, and verify it persists. This proves why saving matters.
