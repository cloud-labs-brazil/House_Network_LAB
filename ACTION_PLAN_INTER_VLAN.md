# Action Plan — Cross-Subnet Connectivity Fix

> **Date:** 2026-03-23  
> **Priority:** CRITICAL  
> **Goal:** All devices on Huawei WiFi ↔ all devices on TIM ↔ all devices on Vivo must communicate (RDP, ping, etc.)

---

## Current Architecture Understanding

```
Huawei WiFi BE3 (BRIDGE MODE)
  └── WiFi devices get IP from Vivo DHCP → 192.168.15.x
      └── Gateway: 192.168.15.1 (Vivo router)
      └── Connected to switch P6 (VLAN 15)

Vivo Askey RTF8225VW
  └── LAN: 192.168.15.1/24
  └── Has static route: 192.168.1.0/24 via 192.168.1.254 (confirmed by user)
  └── Connected to switch P1 (VLAN 15)

ONTi-L3 Switch (CORE)
  └── SVI VLAN 1:  192.168.1.254/24
  └── SVI VLAN 15: 192.168.15.254/24
  └── Routes between VLANs ✅

TIM Kaon PG2447
  └── LAN: 192.168.1.1/24
  └── NO static route capability (web UI limitation)
  └── Connected to switch P8 (VLAN 1)
  └── TIM devices: lenovo-lab (.1.9), msi-laptop (.1.7), iPhone (.1.15)
```

---

## Traffic Flow Analysis

### Test 1: Huawei WiFi device (.15.50) → lenovo-lab (.1.9)

| Hop | Device | Action | Result |
|-----|--------|--------|--------|
| 1 | WiFi device .15.50 | dst .1.9 not local → send to gw .15.1 | → Vivo |
| 2 | Vivo .15.1 | Route lookup: .1.0/24 via .1.254... | ⚠️ **PROBLEM** |

> [!CAUTION]
> **The Vivo route `192.168.1.0/24 via 192.168.1.254` is WRONG.**
> 
> The IP 192.168.1.254 is on VLAN 1 (TIM subnet). The Vivo router is on VLAN 15 (192.168.15.0/24).
> The Vivo router **cannot reach** 192.168.1.254 directly — it's on a different subnet.
> 
> **The correct next-hop should be `192.168.15.254`** (the switch's SVI on VLAN 15, which IS directly reachable from the Vivo router).

### Test 2: lenovo-lab (.1.9) → Huawei WiFi device (.15.50)

| Hop | Device | Action | Result |
|-----|--------|--------|--------|
| 1 | lenovo-lab .1.9 | Has per-device route: .15.0/24 via .1.254 | → Switch |
| 2 | Switch .1.254 | Route: .15.0/24 connected on VLAN 15 | → VLAN 15 |
| 3 | WiFi device .15.50 | Receives packet | ✅ |
| 4 | WiFi device responds | dst .1.9 → gw .15.1 (Vivo) | → Vivo |
| 5 | Vivo .15.1 | Route to .1.0/24 via .1.254 (WRONG next-hop) | ❌ FAILS |

---

## Root Cause Summary

| Problem | Detail |
|---------|--------|
| **Vivo static route has WRONG next-hop** | Points to 192.168.1.254 (unreachable from Vivo). Must be 192.168.15.254 |
| **TIM router has NO route to .15.0/24** | Cannot be fixed via router (ISP-locked). Workaround: per-device routes on every TIM endpoint |

---

## Fix Plan

### FIX 1: Correct Vivo Router Static Route (user does manually)

**Current (WRONG):**
```
Destination: 192.168.1.0/24
Gateway:     192.168.1.254     ← WRONG — not reachable from Vivo subnet
```

**Correct:**
```
Destination: 192.168.1.0
Subnet Mask: 255.255.255.0
Gateway:     192.168.15.254    ← Switch SVI on VLAN 15 — directly reachable from Vivo
```

**Steps for user:**
1. Open browser → `http://192.168.15.1`
2. Login with Vivo credentials
3. Navigate to: Advanced → Routing → Static Routes (or similar)
4. Delete the existing wrong route (192.168.1.0/24 via 192.168.1.254)
5. Add new route:
   - Destination: `192.168.1.0`
   - Mask: `255.255.255.0`
   - Gateway: `192.168.15.254`
6. Save/Apply

### FIX 2: Per-Device Routes on ALL TIM Devices

Since TIM router can't add static routes, every TIM device that needs cross-VLAN access needs:

**Windows devices (cmd as Administrator):**
```cmd
route -p add 192.168.15.0 mask 255.255.255.0 192.168.1.254
```

**Mac/Linux devices:**
```bash
# Linux (persistent via /etc/network/interfaces or netplan)
sudo ip route add 192.168.15.0/24 via 192.168.1.254

# macOS (not persistent — re-add after reboot)
sudo route -n add 192.168.15.0/24 192.168.1.254
```

**iPhone/Android:**
Cannot add static routes on mobile devices.
These devices will NOT have cross-VLAN access unless connected via Huawei WiFi (which is on VLAN 15).

**Devices that need this route:**

| Device | IP | How to Apply |
|--------|-----|-------------|
| lenovo-lab | 192.168.1.9 | ✅ Already done |
| msi-laptop | 192.168.1.7 | Run `route -p add` command above |
| Any other TIM-side PC | 192.168.1.x | Run `route -p add` command above |
| iPhone on TIM WiFi | 192.168.1.15 | ❌ Cannot add routes on iOS |

### FIX 3: Verify Huawei Bridge Mode (user confirms)

Confirm: WiFi devices connected to Huawei are getting IPs in 192.168.15.x range (not 192.168.16.x).
If still getting .16.x → Huawei is NOT fully in bridge mode.

```cmd
# From any Huawei WiFi device, check IP:
ipconfig    (Windows)
ifconfig    (Mac/Linux)
```

---

## Expected Result After Fixes

```
Huawei WiFi device (.15.50) → lenovo-lab (.1.9):
  .15.50 → .15.1 (Vivo) → .15.254 (Switch) → VLAN 1 → .1.9 → responds via .1.254 (Switch) → VLAN 15 → .15.50
  ✅ FULL ROUND-TRIP

lenovo-lab (.1.9) → Huawei WiFi device (.15.50):
  .1.9 → .1.254 (Switch, per-device route) → VLAN 15 → .15.50 → responds via .15.1 (Vivo) → .15.254 (Switch) → VLAN 1 → .1.9
  ✅ FULL ROUND-TRIP

Internet from any device:
  .1.x → .1.1 (TIM) → WAN    ✅ NO CHANGE
  .15.x → .15.1 (Vivo) → WAN  ✅ NO CHANGE
```

---

## Verification Steps (after fixes applied)

From lenovo-lab (192.168.1.9):
```cmd
ping 192.168.15.254    # Switch SVI V15 → should reply
ping 192.168.15.1      # Vivo router → should reply (if Vivo route fixed)
ping 192.168.15.50     # Huawei WiFi device → should reply
```

From Huawei WiFi device (192.168.15.x):
```cmd
ping 192.168.1.254     # Switch SVI V1 → should reply
ping 192.168.1.9       # lenovo-lab → should reply
```

RDP test:
```cmd
mstsc /v:192.168.15.x   # From TIM device to Huawei device
mstsc /v:192.168.1.9     # From Huawei device to lenovo-lab
```
