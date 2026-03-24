# House Network LAB — Project Status Report

> **Date:** 2026-03-23 23:18 BRT  
> **Project:** Dual-ISP Home Network with L3 Switch Inter-VLAN Routing  
> **Repo:** https://github.com/cloud-labs-brazil/House_Network_LAB.git  
> **Overall Progress: ~80%**

---

## 1. Project Objectives

| # | Objective | Status |
|---|-----------|--------|
| 1 | Full audit of all 4 network devices | ✅ DONE |
| 2 | VLAN segmentation on ONTi L3 switch (VLAN 1 = TIM, VLAN 15 = Vivo) | ✅ DONE |
| 3 | Inter-VLAN routing enabled on switch (SVI gateway on each VLAN) | ✅ DONE |
| 4 | Dual-ISP failover (TIM primary metric 10, Vivo backup metric 20) | ✅ DONE |
| 5 | Static routes on ISP routers for full bidirectional inter-VLAN traffic | ❌ BLOCKED |
| 6 | Eliminate Huawei double-NAT (set to Bridge/AP mode) | ✅ DONE |
| 7 | Cross-subnet RDP (192.168.1.x ↔ 192.168.15.x) | ❌ BLOCKED |
| 8 | Switch security hardening (password encryption, VTY auth, IPv6 off) | ✅ DONE |
| 9 | Full documentation and GitHub repo | ✅ DONE |

---

## 2. Master Task Checklist

### Phase 0 — Network Audit
- [x] SSH into ONTi switch at 192.168.1.254 (admin/admin)
- [x] Backup `show running-config` → saved to `switch_backup_20260322_0850.txt`
- [x] Audit `show vlan` — found all ports on VLAN 1, VLAN 16 empty
- [x] Audit `show ip route` — found 5 routes, 4 were broken/stale
- [x] Audit TIM Kaon PG2447 (192.168.1.1) — ISP-locked, limited web UI
- [x] Audit Vivo Askey RTF8225VW (192.168.15.1) — standard ISP router
- [x] Audit Huawei WiFi BE3 (192.168.15.3) — was in router mode (double-NAT)
- [x] Document all findings

### Phase 1 — VLAN & SVI Configuration
- [x] Remove 4 broken/stale routes from switch
- [x] Fix ip host entries (removed netgear-rax120, lenovo; corrected lenovo-lab, huawei-be3)
- [x] Create VLAN 15 named ISP-VIVO
- [x] Assign port P1 (Eth1/0/1) → VLAN 15 (Vivo uplink)
- [x] Assign port P6 (Eth1/0/6) → VLAN 15 (Huawei WAN)
- [x] Create SVI Vlan15 with IP 192.168.15.254/24
- [x] Remove stale VLAN 16 SVI IP (192.168.16.254)
- [x] Set hostname to ONTi-L3

### Phase 2 — Static Routes & Failover on Switch
- [x] Verify default route: 0.0.0.0/0 via 192.168.1.1 metric 10 (TIM primary)
- [x] Add failover route: 0.0.0.0/0 via 192.168.15.1 metric 20 (Vivo backup)
- [x] Add Huawei LAN route: 192.168.16.0/24 via 192.168.15.3
- [x] Verify: ping 192.168.1.1 → 5/5 ✅
- [x] Verify: ping 192.168.15.1 → 5/5 ✅
- [x] Save config with `write`

### Phase 3 — DNS / Name Resolution
- [x] Confirm `ip dns server` already active (serves local ip host entries)
- [x] Confirm no upstream DNS relay supported (firmware limitation — clients use ISP DNS)
- [x] Verify local entries: kaon-tim, msi-laptop, lenovo-lab, huawei-be3

### Phase 4 — IPv6 Disable
- [x] Apply `no ipv6 enable` — IPv6 stack disabled globally

### Phase 5 — Security Hardening
- [x] Apply `service password-encryption`
- [x] Apply `authentication line vty login local`
- [x] Save config with `write`

### Phase 6 — Post-Huawei Cleanup
- [x] User set Huawei BE3 to Bridge/AP mode (192.168.16.x subnet eliminated)
- [x] Remove obsolete route: `no ip route 192.168.16.0/24 192.168.15.3`
- [x] Remove stale host: `no ip host huawei-be3`
- [x] Verify clean routing table (4 routes remaining)
- [x] Save config with `write`

### Phase 7 — Workaround: Per-Device Static Routes
- [x] Add persistent route on Lenovo PC: `192.168.15.0/24 via 192.168.1.254`
- [x] Add persistent route on Lenovo PC: `192.168.16.0/24 via 192.168.1.254`
- [x] Verify forward path: ping 192.168.15.254 → ✅ 1ms (inter-VLAN works)
- [x] Verify return path: ping 192.168.15.1 → ❌ FAIL (asymmetric — no return route on Vivo)

### Phase 8 — ISP Router Static Routes ← **WE ARE HERE**

#### 8A — TIM Kaon PG2447 (192.168.1.1)
- [x] Research web UI for static route support → **NOT AVAILABLE** (only "Route Policy")
- [x] Scan SSH port 22 → First scan: OPEN, re-scan: **FILTERED/TIMEOUT**
- [x] Scan Telnet port 23 → First scan: OPEN, re-scan: **FILTERED/TIMEOUT**
- [x] Scan HTTP port 80 → **OPEN** (only accessible port)
- [x] Research Kaon PG2447 documentation → found potential credential `L1vt1m4eng`
- [x] Test SSH connection attempt → **Connection refused**
- [x] Test Telnet connection attempt → **Connection refused**
- [ ] 🔴 Research hidden web UI pages (e.g. `/cgi-bin/`, TR-069 pages)
- [ ] 🔴 Try accessing `192.168.1.1/main.html`, `/boaform/`, `/cgi-bin/` variants
- [ ] 🔴 If all fail → Contact TIM support to request static route OR accept per-device workaround

#### 8B — Vivo Askey RTF8225VW (192.168.15.1)
- [ ] 🟡 Scan ports on Vivo router (22, 23, 80, 443)
- [ ] 🟡 Research Askey RTF8225VW manual for static route capability
- [ ] 🟡 Access web UI and find routing configuration
- [ ] 🟡 Add static route: `192.168.1.0/24 via 192.168.15.254`
- [ ] 🟡 Save and verify

### Phase 9 — End-to-End Verification
- [ ] ⬜ Ping from 192.168.1.9 → 192.168.15.1 (full round-trip)
- [ ] ⬜ Ping from 192.168.15.x → 192.168.1.9 (reverse direction)
- [ ] ⬜ Traceroute validation (should show switch as intermediate hop)
- [ ] ⬜ RDP test: 192.168.1.9 → 192.168.15.x:3389
- [ ] ⬜ Internet access unchanged on both ISPs

### Phase 10 — Final Documentation & Push
- [ ] ⬜ Update PROJECT_TRANSITION_DOCUMENT.md with final results
- [ ] ⬜ Commit and push final state to GitHub
- [ ] ⬜ Create README.md for the repo

---

## 3. What Is Blocking Project Completion

### BLOCKER 1: TIM Kaon PG2447 — No Static Route Interface

| Detail | Finding |
|--------|---------|
| **Web UI** | `192.168.1.1/normal` → Has "Route Policy" but NO traditional static routes |
| **SSH (22)** | Port FILTERED — connection refused |
| **Telnet (23)** | Port FILTERED — connection refused |
| **HTTP (80)** | OPEN — only available management interface |
| **What was tried** | Port scanning, SSH with admin/admin, Telnet raw connect |
| **What was NOT tried** | Hidden web URLs, TR-069 pages, contacting TIM support |

**Impact:** Without a route `192.168.15.0/24 via 192.168.1.254` on this router, packets from TIM-side devices going to Vivo subnet get sent out the WAN (internet) instead of to the switch.

### BLOCKER 2: Vivo Askey RTF8225VW — Not Yet Attempted

| Detail | Finding |
|--------|---------|
| **Status** | No configuration attempted yet |
| **Expected** | Askey routers typically support static routes via web UI |
| **Needed** | Route `192.168.1.0/24 via 192.168.15.254` |

**Impact:** Without this route, return packets from Vivo-side devices to TIM subnet get sent out the WAN instead of back through the switch (asymmetric routing).

---

## 4. What Went Wrong / Limitations Found

| # | Issue | When Found | Impact | Current Status |
|---|-------|-----------|--------|----------------|
| 1 | Switch had 4 broken routes from previous admin | Phase 0 | Low | ✅ Fixed — routes removed |
| 2 | TIM Kaon web UI has no static route feature | Phase 8A | **HIGH** | ❌ Unresolved — blocks inter-VLAN |
| 3 | SSH/Telnet ports on TIM gave false positive then refused | Phase 8A | Medium | ❌ Confirmed FILTERED on re-scan |
| 4 | Huawei was in router mode causing double-NAT | Phase 0 | Medium | ✅ Fixed — user set to bridge mode |
| 5 | Switch DNS relay not supported by firmware | Phase 3 | Low | ⚠️ Accepted — clients use ISP DNS |
| 6 | VTY session timeouts during config work | All phases | Low | ⚠️ Accepted — reconnect as needed |
| 7 | Commands attempted without checking manual first | Early phases | Low | ✅ Corrected approach — manual-first |

---

## 5. Current Network State (Working)

```
Switch Routing Table (CLEAN — 4 routes):
  S*  0.0.0.0/0       via 192.168.1.1   metric 10  (TIM primary)
  S   0.0.0.0/0       via 192.168.15.1  metric 20  (Vivo failover)
  C   192.168.1.0/24   connected         Vlan1
  C   192.168.15.0/24  connected         Vlan15

What WORKS today:
  ✅ Internet via TIM (primary)
  ✅ Internet via Vivo (failover)
  ✅ Switch routes between VLANs (forward path)
  ✅ Per-device route on Lenovo reaches Vivo subnet (192.168.15.254)
  ✅ Huawei WiFi 7 in bridge mode (no more double-NAT)
  ✅ Switch security hardened

What DOES NOT work today:
  ❌ Full round-trip between subnets (return path broken)
  ❌ RDP cross-subnet (needs both directions)
  ❌ TIM router doesn't route 192.168.15.0/24 to switch
  ❌ Vivo router doesn't route 192.168.1.0/24 to switch
```

---

## 6. Proposed Next Steps (Awaiting Approval)

| # | Action | Risk | Needs Your Approval? |
|---|--------|------|---------------------|
| 1 | Research hidden web pages on TIM Kaon (web search only, no commands) | None | No |
| 2 | Port scan Vivo router 192.168.15.1 (read-only, no config changes) | None | Yes |
| 3 | Research Askey RTF8225VW manual (web search only) | None | No |
| 4 | Access Vivo web UI via browser to add static route | Low — adds 1 route | Yes |
| 5 | If TIM has no solution → document as permanent limitation, use per-device routes | None | Yes |

> **Nothing will be executed until you approve specific items from this list.**
