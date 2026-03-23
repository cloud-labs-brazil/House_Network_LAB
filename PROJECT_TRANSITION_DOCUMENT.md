# House Network LAB — Project Transition Document

> **Document Type:** PM Handoff / Full Project Status  
> **Date:** 2026-03-23  
> **Repo:** https://github.com/cloud-labs-brazil/House_Network_LAB.git  
> **Branch:** `main`

---

## 1. Project Objective

**Build a fully segmented, dual-ISP home network using an ONTi L3 switch as the core router, enabling inter-VLAN connectivity between all subnets while maintaining independent internet access through each ISP.**

### Specific Goals

| # | Goal | Status |
|---|------|--------|
| G1 | Audit existing network (4 devices, 3 subnets) | ✅ DONE |
| G2 | Configure VLAN segmentation on ONTi L3 switch | ✅ DONE |
| G3 | Enable inter-VLAN routing through the switch | ✅ DONE |
| G4 | Implement dual-ISP failover (TIM primary, Vivo backup) | ✅ DONE |
| G5 | Add static routes on ISP routers for full bidirectional inter-VLAN traffic | ⏳ BLOCKED |
| G6 | Eliminate Huawei double-NAT (Bridge/AP mode) | ✅ DONE (by user) |
| G7 | Enable cross-subnet RDP access (e.g., 192.168.1.x ↔ 192.168.15.x) | ⏳ PARTIAL |
| G8 | Harden switch security (passwords, VTY auth, IPv6 disable) | ✅ DONE |
| G9 | Document everything for reproducibility | ✅ DONE |

---

## 2. Network Architecture Summary

```
                    ☁ INTERNET
            ┌────────┴────────┐
      ISP1: TIM          ISP2: Vivo
      PPPoE 1Gbps        DHCP
            │                  │
     ┌──────▼──────┐    ┌──────▼──────────┐
     │ R1 — TIM    │    │ R2 — Vivo       │
     │ Kaon PG2447 │    │ Askey RTF8225VW │
     │ .1.1/24     │    │ .15.1/24        │
     └──────┬──────┘    └───┬─────────────┘
            │ P8 (10G DAC)  │ P1 (1G SFP+)
     ┌──────▼───────────────▼──────────────┐
     │       SW1 — ONTi-L3 Switch          │
     │       ONT-S508CL-8S (8x SFP+ 10G)  │
     │       SVI V1:  192.168.1.254/24     │
     │       SVI V15: 192.168.15.254/24    │
     │       ip routing: ON                │
     └──────────────────┬──────────────────┘
                        │ P6 (10G DAC)
                 ┌──────▼──────────┐
                 │ AP1 — Huawei    │
                 │ WiFi BE3        │
                 │ Bridge/AP Mode  │
                 │ (WiFi 7)        │
                 └─────────────────┘
```

### Subnets

| VLAN | Subnet | Gateway (Router) | Gateway (Switch SVI) | Purpose |
|------|--------|-------------------|---------------------|---------|
| 1 | 192.168.1.0/24 | 192.168.1.1 (TIM) | 192.168.1.254 | ISP1 — Primary internet |
| 15 | 192.168.15.0/24 | 192.168.15.1 (Vivo) | 192.168.15.254 | ISP2 — Secondary internet |
| 16 | 192.168.16.0/24 | N/A (Huawei now in bridge) | N/A | ~~Huawei LAN~~ **DEPRECATED** |

---

## 3. Task Status — Complete Breakdown

### Phase 0 — Configuration Audit ✅ COMPLETE

| Task | Result |
|------|--------|
| SSH into switch (admin/admin @ 192.168.1.254) | ✅ Connected |
| Backup `show running-config` | ✅ Saved to `switch_backup_20260322_0850.txt` |
| Audit `show vlan` | ✅ All ports VLAN 1, VLAN 16 empty |
| Audit `show ip route` | ✅ Found 5 routes — 4 were broken/stale |
| Audit TIM Kaon PG2447 | ✅ ISP-locked router, limited web UI |
| Audit Vivo Askey RTF8225VW | ✅ Standard ISP router |
| Audit Huawei WiFi BE3 | ✅ Was in router/NAT mode (double-NAT problem) |

### Phase 1 — VLAN & SVI Configuration ✅ COMPLETE

| Task | Command / Action |
|------|-----------------|
| Remove 4 broken routes | `no ip route 192.168.16.0/24 ...` × 2, `no ip route 192.168.132.0/24 ...` × 2 |
| Fix ip host entries | Removed stale `netgear-rax120`, `lenovo`; corrected `lenovo-lab` → .1.9, `huawei-be3` → .15.3 |
| Create VLAN 15 (ISP-VIVO) | `vlan 15` / `name ISP-VIVO` |
| Assign ports P1, P6 → VLAN 15 | `switchport access vlan 15` on Eth1/0/1 and Eth1/0/6 |
| Create SVI Vlan15 | `interface Vlan15` / `ip address 192.168.15.254 255.255.255.0` |
| Remove stale VLAN 16 IP | Removed 192.168.16.254 from Vlan16 SVI |
| Set hostname | `hostname ONTi-L3` |

### Phase 2 — Static Routes & Failover ✅ COMPLETE

| Task | Command |
|------|---------|
| Default route TIM (primary) | `ip route 0.0.0.0/0 192.168.1.1 10` (already existed) |
| Failover route Vivo | `ip route 0.0.0.0/0 192.168.15.1 20` |
| Huawei LAN route | `ip route 192.168.16.0/24 192.168.15.3 1` |
| Verify ping TIM | ✅ 5/5 success |
| Verify ping Vivo | ✅ 5/5 success |
| Save config | `write` → startup-config updated |

### Phase 3 — DNS / Name Resolution ✅ COMPLETE

| Task | Result |
|------|--------|
| DNS server | Already active (`ip dns server`) — serves local `ip host` entries only |
| Upstream DNS relay | **Not supported** by firmware — clients use ISP DNS directly |
| Local entries | kaon-tim (.1.1), msi-laptop (.1.7), lenovo-lab (.1.9), huawei-be3 (.15.3) |

### Phase 4 — IPv6 Disable ✅ COMPLETE

| Task | Command |
|------|---------|
| Disable IPv6 globally | `no ipv6 enable` |

### Phase 5 — Security Hardening ✅ COMPLETE

| Task | Command |
|------|---------|
| Encrypt passwords in config | `service password-encryption` |
| VTY auth | `authentication line vty login local` |
| Save | `write` → startup-config updated |

### Phase 6 — Post-Huawei Cleanup ✅ COMPLETE

| Task | Result |
|------|--------|
| Remove obsolete route | `no ip route 192.168.16.0/24 192.168.15.3` (Huawei now in bridge, no .16.x subnet) |
| Remove stale host entry | `no ip host huawei-be3` |
| Verify routing table | Clean: 4 routes (2× default, 2× connected) |
| Save config | `write` ✅ |

### Phase 7 — ISP Router Static Routes ⏳ BLOCKED

> [!CAUTION]
> This is the **critical remaining task** to achieve full inter-VLAN connectivity.

| Task | Required Action | Status |
|------|----------------|--------|
| **TIM Router: add route** | `192.168.15.0/24 via 192.168.1.254` | ⏳ BLOCKED — see §4 |
| **Vivo Router: add route** | `192.168.1.0/24 via 192.168.15.254` | ⏳ NOT STARTED |
| Verify end-to-end ping | PC (.1.x) ↔ device (.15.x) | ⏳ WAITING |
| Verify RDP cross-subnet | 192.168.1.9 → 192.168.15.x:3389 | ⏳ WAITING |

### Phase 8 — Workaround: Per-Device Routes ✅ PARTIAL

As a workaround while ISP routers are blocked, static routes were added on the Lenovo PC:

```cmd
route -p add 192.168.15.0 mask 255.255.255.0 192.168.1.254
route -p add 192.168.16.0 mask 255.255.255.0 192.168.1.254
```

**Result:** Forward path works (PC → switch → VLAN 15 devices), but return path fails because Vivo router doesn't know how to send packets back to 192.168.1.x → asymmetric routing.

---

## 4. Blockers & Issues

### BLOCKER 1: TIM Kaon PG2447 — Cannot Add Static Routes (CRITICAL)

| Detail | Value |
|--------|-------|
| **Problem** | Router web UI (`192.168.1.1/normal`) does NOT have traditional static route configuration. Only has "Route Policy" which is not the same. |
| **SSH/Telnet** | Ports 22 and 23 are **OPEN** on the router |
| **OS** | Linux with BusyBox |
| **Potential credential** | `L1vt1m4eng` found in Scribd document for PG2447T model |
| **Default creds** | Web: admin/admin. Telnet/SSH: **unknown** — ISP-locked |
| **Research done** | Kaon Group website, YouTube tutorials, Adrenaline.com.br forums, Reddit, GitHub, Scribd firmware docs |
| **What was NOT tried** | Telnet/SSH connection attempts (user requested proper research first before attempting) |
| **Resolution options** | 1) Try SSH/Telnet with discovered credentials; 2) Call TIM support for static route; 3) Use per-device routes on all clients |

### BLOCKER 2: Vivo Askey RTF8225VW — Not Yet Attempted

| Detail | Value |
|--------|-------|
| **Problem** | Configuration not yet attempted — focus was on TIM first |
| **Expected** | Askey routers typically have static route support in web UI |
| **Action needed** | Access web UI at 192.168.15.1 and add route `192.168.1.0/24 via 192.168.15.254` |

### ISSUE 3: Asymmetric Routing (Consequence of Blockers 1 & 2)

```
OUTBOUND: PC .1.9 → Switch .1.254 → SVI V15 → device .15.x  ✅ WORKS
RETURN:   device .15.x → Vivo .15.1 → WAN (internet!)         ❌ LOST
```

The Vivo router has no route for 192.168.1.0/24, so return packets go out to the internet instead of back through the switch.

### ISSUE 4: Huawei Bridge Mode Side-Effect

| Detail | Value |
|--------|-------|
| **Status** | User manually set Huawei BE3 to Bridge/AP mode ✅ |
| **Effect** | 192.168.16.0/24 subnet no longer exists — WiFi clients get IPs from Vivo DHCP (192.168.15.x) |
| **Cleanup done** | Removed obsolete route and ip host from switch |

---

## 5. Current Switch Configuration (Post All Changes)

### Routing Table (Clean — 4 routes)

| Type | Network | Next Hop | Metric | Purpose |
|------|---------|----------|--------|---------|
| S* | 0.0.0.0/0 | 192.168.1.1 | 10 | Default → TIM (primary) |
| S | 0.0.0.0/0 | 192.168.15.1 | 20 | Default → Vivo (failover) |
| C | 192.168.1.0/24 | connected | 0 | TIM LAN |
| C | 192.168.15.0/24 | connected | 0 | Vivo LAN |

### Port Assignments

| Port | VLAN | Speed | Connected To |
|------|------|-------|-------------|
| P1 (1/0/1) | 15 | 1G SFP+ | R2 — Vivo |
| P2-P5, P7 | 1 | — | Empty (expansion) |
| P6 (1/0/6) | 15 | 10G DAC | AP1 — Huawei BE3 |
| P8 (1/0/8) | 1 | 10G DAC | R1 — TIM |

---

## 6. What Needs to Happen Next (Priority Order)

### Priority 1: Try SSH/Telnet to TIM Router

```
# Credentials to test (in order):
1. admin / admin
2. admin / L1vt1m4eng
3. support / support
4. root / root
5. user / user
```

If shell access is gained:
```bash
# BusyBox Linux — add static route:
ip route add 192.168.15.0/24 via 192.168.1.254
# Or if iptables/iproute2:
route add -net 192.168.15.0 netmask 255.255.255.0 gw 192.168.1.254
```

### Priority 2: Configure Vivo Router Static Route

Access `http://192.168.15.1` → Find static/advanced routing → Add:
- **Destination:** 192.168.1.0
- **Mask:** 255.255.255.0
- **Gateway:** 192.168.15.254

### Priority 3: Verify End-to-End

From lenovo-lab (192.168.1.9):
```cmd
ping 192.168.15.1      # Should reply (return path fixed)
tracert 192.168.15.1   # Should show: .1.254 → .15.1
```

### Priority 4: Test RDP Cross-VLAN

```cmd
mstsc /v:192.168.15.x:3389   # RDP to Vivo-side device
```

---

## 7. Source Documents Index

| Document | Location | Purpose |
|----------|----------|---------|
| **Switch backup (BEFORE changes)** | [`switch_backup_20260322_0850.txt`](file:///C:/VMs/Projects/Network_Tracker/switch_backup_20260322_0850.txt) | Original config snapshot before any modifications |
| **Network topology** | [`network_topology.md`](file:///C:/VMs/Projects/Network_Tracker/network_topology.md) | Physical/logical topology with all devices and subnets |
| **Network Design LLD** | [Brain artifact: `network_design_lld.md`](file:///C:/Users/mbenicios/.gemini/antigravity/brain/eb5610b0-5a23-44b0-a810-db8615562e80/network_design_lld.md) | CCIE-level LLD with MAC tables, ARP, packet flows, 3 simulation scenarios |
| **AS-IS vs TO-BE diagram**| [Brain artifact: `network_as_is_to_be.md`](file:///C:/Users/mbenicios/.gemini/antigravity/brain/eb5610b0-5a23-44b0-a810-db8615562e80/network_as_is_to_be.md) | Visual comparison of current vs target state |
| **Packet flow simulation** | [Brain artifact: `packet_flow_simulation.md`](file:///C:/Users/mbenicios/.gemini/antigravity/brain/eb5610b0-5a23-44b0-a810-db8615562e80/packet_flow_simulation.md) | 6 trace scenarios validating the routing plan |
| **Task tracker** | [Brain artifact: `task.md`](file:///C:/Users/mbenicios/.gemini/antigravity/brain/eb5610b0-5a23-44b0-a810-db8615562e80/task.md) | Phase-by-phase checklist |
| **Walkthrough** | [Brain artifact: `walkthrough.md`](file:///C:/Users/mbenicios/.gemini/antigravity/brain/eb5610b0-5a23-44b0-a810-db8615562e80/walkthrough.md) | Post-execution verification log with ping/tracert evidence |
| **Inter-VLAN route script** | [`scripts/Setup-InterVLAN-Routes.ps1`](file:///C:/VMs/Projects/Network_Tracker/scripts/Setup-InterVLAN-Routes.ps1) | PowerShell script for per-device static routes (workaround) |
| **ONTi switch manual pack** | [`manual/ONTi_ONT-S508CL-8S_manual_pack/`](file:///C:/VMs/Projects/Network_Tracker/manual/ONTi_ONT-S508CL-8S_manual_pack/) | 16 CLI guides, datasheet, web UI manual, quick manual |
| **GitHub repo** | https://github.com/cloud-labs-brazil/House_Network_LAB.git | All project files |

### Key Manual Files for Next PM

| Manual | Content |
|--------|---------|
| `01-Command For Basic Switch Configuration.pdf` | Hostname, system, passwords |
| `04-Commands for VLAN Configuration.pdf` | VLAN creation, port assignment |
| `07-Commands for Layer 3 Interface and ARP.pdf` | SVI config, ARP management |
| `16-Commands for Routing Protocol.pdf` | Static routes, RIP, OSPF |

---

## 8. Lessons Learned / What Went Wrong

| # | Issue | Impact | Root Cause | Lesson |
|---|-------|--------|------------|--------|
| 1 | Original switch config had 4 broken routes | Low — cleanup required | Previous admin left stale routes for devices no longer present | Always clean up routes when removing devices |
| 2 | TIM Kaon PG2447 web UI lacks static route support | **HIGH** — blocks project completion | ISP-provided CPE with restricted firmware | Research CPE capabilities BEFORE planning routes through it |
| 3 | Huawei double-NAT caused confusion | Medium — wasted investigation time | Cascaded router in default router mode | Always check if AP/bridge mode is available first |
| 4 | Switch VTY timeout disconnected sessions mid-work | Low — annoying but recoverable | Default 5-min timeout | Consider setting `exec-timeout` higher during maintenance windows |
| 5 | Browser session limits on ISP routers | Medium — blocked automated config | Kaon allows only 1 admin session at a time | Never open parallel browser sessions to same router |
| 6 | Commands tried without checking manual first | Low — some commands rejected | Firmware uses slightly different syntax | **Always check the manufacturer manual pack before executing commands** |

---

## 9. Project Completion Summary

| Metric | Value |
|--------|-------|
| **Overall completion** | **~80%** |
| **Switch config** | 100% complete ✅ |
| **Huawei bridge mode** | 100% complete ✅ |
| **ISP router routes** | 0% — blocked by firmware limitations |
| **Inter-VLAN forward path** | Works via per-device routes |
| **Inter-VLAN return path** | ❌ Broken — needs ISP router routes |
| **RDP cross-subnet** | ❌ Not yet functional |
| **Documentation** | 100% complete ✅ |

> [!IMPORTANT]
> The project is **80% complete**. The remaining 20% depends entirely on gaining CLI access to the TIM Kaon PG2447 router (SSH port 22 is open, credentials need testing) and configuring the Vivo Askey router's static route through its web UI.
