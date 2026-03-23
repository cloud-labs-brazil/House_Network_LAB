#!/usr/bin/env python3
"""
Kaon PG2447 / Broadcom BCM968560 Backup Config Decryptor
=========================================================
Brute-force decryption of OpenSSL-encrypted backupsettings.conf
using known ISP router encryption patterns.

Author: Network Security Engineer
Purpose: Extract L1vt1m4eng superadmin password from own router backup
"""

import base64
import hashlib
import os
import sys
import itertools
import string
from pathlib import Path

# Try to import cryptography library
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# Fallback to subprocess openssl
import subprocess

BACKUP_FILE = Path(__file__).parent / "backupsettings.conf"
OUTPUT_FILE = Path(__file__).parent / "backup_decrypted.xml"

# ============================================================
# KNOWN KEYS FOR BROADCOM/KAON/ISP ROUTERS
# Sources: GitHub repos, Adrenaline forums, router security research
# ============================================================
KNOWN_KEYS = [
    # Standard Broadcom keys
    "kaon", "Kaon", "KAON", "kaonbroadband", "KaonBroadband",
    "kaonmedia", "KaonMedia", "kaongroup", "KaonGroup",
    "broadcom", "Broadcom", "BROADCOM", "BCM", "bcm",
    # TIM/ISP specific
    "tim", "TIM", "timlive", "livtim", "timbrasil",
    "TimLive", "TIMLIVE", "L1vt1m4eng",
    # Common router backup keys
    "admin", "password", "1234", "default", "root",
    "support", "user", "guest", "tech", "technician",
    # Common ISP default keys (Brazil)
    "vivo", "claro", "oi", "net", "algar",
    # Device-specific patterns
    "PG2447", "pg2447", "AR4010", "ar4010",
    "BCM968560", "bcm968560",
    "ONT", "ont", "gpon", "GPON",
    # Sticker password and variants
    "prv7rnhb", "PRV7RNHB",
    # Common Broadcom CPE keys from firmware analysis
    "3bb", "true", "cat", "tot", "ais", "dtac",
    "somlabs", "sievert", "inteno", "iopsys",
    "telstra", "telecom", "BrCm", "brcm",
    # Known encryption keys from other Broadcom routers
    "01234567890ABCDEF", "0123456789abcdef",
    "abcdefghijklmnop", "ABCDEFGHIJKLMNOP",
    # Key patterns from firmware dumps
    "CfgMgr", "cfgmgr", "config", "backup",
    "settings", "backupsettings", "backupSettings",
    # SHA/MD5 derived keys
    hashlib.md5(b"kaon").hexdigest(),
    hashlib.md5(b"admin").hexdigest(),
    hashlib.md5(b"broadcom").hexdigest(),
    hashlib.md5(b"tim").hexdigest(),
    hashlib.sha256(b"kaon").hexdigest()[:32],
    hashlib.sha256(b"broadcom").hexdigest()[:32],
    # Empty/null
    "", " ",
]

# Ciphers to try
CIPHERS = [
    "aes-256-cbc", "aes-128-cbc", "aes-256-ecb", "aes-128-ecb",
    "des-ede3-cbc", "des-cbc", "aes-192-cbc",
    "aes-256-cfb", "aes-128-cfb", "aes-256-ofb",
    "bf-cbc",  # Blowfish
    "rc4",     # RC4 (some older routers)
    "camellia-256-cbc", "camellia-128-cbc",
]

# Digest algorithms for key derivation
DIGESTS = ["md5", "sha256", "sha1", "sha512"]


def find_openssl():
    """Find openssl binary on the system."""
    paths = [
        r"C:\Program Files\Git\usr\bin\openssl.exe",
        r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe",
        r"C:\Windows\System32\openssl.exe",
        "openssl",  # PATH
    ]
    for p in paths:
        if os.path.exists(p) or p == "openssl":
            try:
                result = subprocess.run([p, "version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"[+] Found OpenSSL: {result.stdout.strip()}")
                    return p
            except Exception:
                continue
    return None


def try_openssl_decrypt(openssl_path, cipher, digest, key, input_file, output_file):
    """Try to decrypt using openssl CLI."""
    cmd = [
        openssl_path, "enc", f"-{cipher}", "-d", "-a",
        "-pass", f"pass:{key}",
        "-in", str(input_file),
        "-out", str(output_file),
        "-md", digest,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and os.path.exists(output_file):
            size = os.path.getsize(output_file)
            if size > 100:
                with open(output_file, 'r', errors='ignore') as f:
                    head = f.read(500)
                # Check if decrypted content looks like config XML/text
                config_markers = [
                    '<?xml', '<config', '<Inter', '<Device', 
                    'password', 'admin', 'wan', 'lan',
                    'dhcp', 'route', 'interface', 'ppp',
                    'ssid', 'wifi', 'dns', 'firewall',
                    'http', 'telnet', 'ssh', 'snmp',
                    'L1vt1m4eng', 'username', 'passwd',
                ]
                for marker in config_markers:
                    if marker.lower() in head.lower():
                        return True, head
    except Exception:
        pass
    return False, None


def try_raw_decrypt(data_bytes, key_bytes, iv_bytes, cipher_mode="aes-256-cbc"):
    """Try direct decryption with raw key/IV (no key derivation)."""
    if not HAS_CRYPTO:
        return False, None
    try:
        if "aes-256" in cipher_mode:
            key = key_bytes[:32].ljust(32, b'\x00')
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv_bytes[:16]), backend=default_backend())
        elif "aes-128" in cipher_mode:
            key = key_bytes[:16].ljust(16, b'\x00')
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv_bytes[:16]), backend=default_backend())
        else:
            return False, None

        decryptor = cipher.decryptor()
        plaintext = decryptor.update(data_bytes) + decryptor.finalize()

        # Remove PKCS7 padding
        pad_len = plaintext[-1]
        if 0 < pad_len <= 16:
            plaintext = plaintext[:-pad_len]

        text = plaintext.decode('utf-8', errors='ignore')
        if any(m in text.lower() for m in ['xml', 'config', 'password', 'admin', 'interface']):
            return True, text[:500]
    except Exception:
        pass
    return False, None


def extract_salt_and_data(filepath):
    """Extract salt and encrypted data from OpenSSL Salted__ format."""
    with open(filepath, 'r') as f:
        b64_data = f.read().replace('\n', '').replace('\r', '')
    
    raw = base64.b64decode(b64_data)
    
    # OpenSSL format: "Salted__" (8 bytes) + salt (8 bytes) + encrypted data
    if raw[:8] == b'Salted__':
        salt = raw[8:16]
        enc_data = raw[16:]
        print(f"[+] Salt extracted: {salt.hex()}")
        print(f"[+] Encrypted data size: {len(enc_data)} bytes")
        return salt, enc_data
    else:
        print(f"[!] Header: {raw[:16].hex()} - may not be standard OpenSSL format")
        return None, raw


def openssl_evp_bytes_to_key(password, salt, key_len, iv_len, digest='md5'):
    """Replicate OpenSSL's EVP_BytesToKey key derivation."""
    if isinstance(password, str):
        password = password.encode('utf-8')
    
    if digest == 'md5':
        hash_func = hashlib.md5
    elif digest == 'sha256':
        hash_func = hashlib.sha256
    elif digest == 'sha1':
        hash_func = hashlib.sha1
    elif digest == 'sha512':
        hash_func = hashlib.sha512
    else:
        hash_func = hashlib.md5
    
    d = b''
    d_i = b''
    while len(d) < key_len + iv_len:
        d_i = hash_func(d_i + password + salt).digest()
        d += d_i
    
    return d[:key_len], d[key_len:key_len + iv_len]


def decrypt_with_evp(salt, enc_data, password, key_len=32, iv_len=16, digest='md5'):
    """Decrypt using EVP_BytesToKey derivation (pure Python)."""
    if not HAS_CRYPTO:
        return False, None
    
    key, iv = openssl_evp_bytes_to_key(password, salt, key_len, iv_len, digest)
    
    try:
        if key_len == 32:
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        elif key_len == 16:
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        elif key_len == 24:
            from cryptography.hazmat.primitives.ciphers import algorithms as alg
            cipher = Cipher(alg.TripleDES(key), modes.CBC(iv), backend=default_backend())
        else:
            return False, None
        
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(enc_data) + decryptor.finalize()
        
        # Remove PKCS7 padding
        pad_len = plaintext[-1]
        if 0 < pad_len <= 16 and all(b == pad_len for b in plaintext[-pad_len:]):
            plaintext = plaintext[:-pad_len]
        
        text = plaintext.decode('utf-8', errors='ignore')
        markers = ['xml', 'config', 'password', 'admin', 'interface', 
                   'l1vt1m4eng', 'username', 'dhcp', 'wan', 'lan',
                   'ssid', 'ppp', 'dns', 'route']
        if any(m in text.lower() for m in markers):
            return True, text[:1000]
    except Exception:
        pass
    return False, None


def main():
    print("=" * 70)
    print("  KAON PG2447 Backup Config Decryptor")
    print("  Target: Broadcom BCM968560 (TIM Ultra Fibra)")
    print("=" * 70)
    
    if not BACKUP_FILE.exists():
        print(f"[!] Backup file not found: {BACKUP_FILE}")
        sys.exit(1)
    
    print(f"\n[*] Backup file: {BACKUP_FILE}")
    print(f"[*] File size: {BACKUP_FILE.stat().st_size} bytes")
    
    # Extract salt and encrypted data
    salt, enc_data = extract_salt_and_data(BACKUP_FILE)
    
    if salt is None:
        print("[!] Could not extract salt - trying raw approaches")
    
    total_attempts = 0
    
    # ============================
    # METHOD 1: OpenSSL CLI brute-force
    # ============================
    openssl = find_openssl()
    if openssl:
        print(f"\n{'='*70}")
        print("  METHOD 1: OpenSSL CLI Brute-Force")
        total = len(CIPHERS) * len(DIGESTS) * len(KNOWN_KEYS)
        print(f"  Combinations: {total}")
        print(f"{'='*70}")
        
        for cipher in CIPHERS:
            for digest in DIGESTS:
                for key in KNOWN_KEYS:
                    total_attempts += 1
                    if total_attempts % 100 == 0:
                        print(f"  [{total_attempts}/{total}] Testing {cipher}/{digest}...", end='\r')
                    
                    success, content = try_openssl_decrypt(
                        openssl, cipher, digest, key, BACKUP_FILE, OUTPUT_FILE
                    )
                    if success:
                        print(f"\n\n{'*'*70}")
                        print(f"  *** SUCCESS! ***")
                        print(f"  Cipher: {cipher}")
                        print(f"  Digest: {digest}")
                        print(f"  Key:    {key}")
                        print(f"  Output: {OUTPUT_FILE}")
                        print(f"{'*'*70}")
                        print(f"\nFirst 500 chars:\n{content}")
                        
                        # Search for password
                        search_for_password(str(OUTPUT_FILE))
                        return
        
        print(f"\n  OpenSSL CLI: {total_attempts} attempts failed")
    
    # ============================
    # METHOD 2: Pure Python EVP_BytesToKey
    # ============================
    if HAS_CRYPTO and salt is not None:
        print(f"\n{'='*70}")
        print("  METHOD 2: Python EVP_BytesToKey Decryption")
        print(f"{'='*70}")
        
        configs = [
            (32, 16, 'md5'),     # AES-256-CBC, MD5 (OpenSSL default)
            (16, 16, 'md5'),     # AES-128-CBC, MD5
            (32, 16, 'sha256'),  # AES-256-CBC, SHA256
            (16, 16, 'sha256'),  # AES-128-CBC, SHA256
            (32, 16, 'sha1'),    # AES-256-CBC, SHA1
            (16, 16, 'sha1'),    # AES-128-CBC, SHA1
            (24, 8, 'md5'),      # 3DES-CBC, MD5
        ]
        
        for key_len, iv_len, digest in configs:
            for key in KNOWN_KEYS:
                total_attempts += 1
                success, content = decrypt_with_evp(salt, enc_data, key, key_len, iv_len, digest)
                if success:
                    print(f"\n{'*'*70}")
                    print(f"  *** SUCCESS (Python)! ***")
                    print(f"  Key Length: {key_len}")
                    print(f"  Digest: {digest}")
                    print(f"  Password: {key}")
                    print(f"{'*'*70}")
                    print(f"\nFirst 1000 chars:\n{content}")
                    
                    with open(OUTPUT_FILE, 'w') as f:
                        f.write(content)
                    search_for_password(str(OUTPUT_FILE))
                    return
        
        print(f"  Python EVP: all attempts failed")
    
    # ============================
    # METHOD 3: Common firmware hardcoded keys (hex)
    # ============================
    if HAS_CRYPTO and salt is not None:
        print(f"\n{'='*70}")
        print("  METHOD 3: Hardcoded Firmware Keys (raw hex)")
        print(f"{'='*70}")
        
        # Known hardcoded keys from Broadcom router firmware
        hex_keys = [
            # Common Broadcom CPE backup encryption keys
            "00112233445566778899aabbccddeeff",
            "0123456789abcdef0123456789abcdef",
            "deadbeefdeadbeefdeadbeefdeadbeef",
            "ffffffffffffffffffffffffffffffff",
            "00000000000000000000000000000000",
            "6b616f6e62726f616462616e64000000",  # "kaonbroadband\0\0\0"
            "6b616f6e00000000000000000000000000000000000000000000000000000000",  # "kaon" padded
            "61646d696e000000000000000000000000000000000000000000000000000000",  # "admin" padded
            "3362620000000000000000000000000000000000000000000000000000000000",  # "3bb" padded
            hashlib.md5(b"Broadcom").hexdigest() + "0" * 32,
            hashlib.md5(b"kaon").hexdigest() + "0" * 32,
            hashlib.md5(b"admin").hexdigest() + "0" * 32,
        ]
        
        for hk in hex_keys:
            total_attempts += 1
            try:
                key_bytes = bytes.fromhex(hk[:64])
                for iv_hex in ["00000000000000000000000000000000", salt.hex() + "0" * (32 - len(salt.hex() * 2))]:
                    iv_bytes = bytes.fromhex(iv_hex[:32])
                    success, content = try_raw_decrypt(enc_data, key_bytes, iv_bytes, "aes-256-cbc")
                    if success:
                        print(f"\n*** SUCCESS with raw key: {hk[:32]}... ***")
                        print(content)
                        return
                    success, content = try_raw_decrypt(enc_data, key_bytes[:16], iv_bytes, "aes-128-cbc")
                    if success:
                        print(f"\n*** SUCCESS with raw key (128-bit): {hk[:32]}... ***")
                        print(content)
                        return
            except Exception:
                continue
        
        print(f"  Hardcoded keys: all attempts failed")
    
    # ============================
    # SUMMARY
    # ============================
    print(f"\n{'='*70}")
    print(f"  TOTAL ATTEMPTS: {total_attempts}")
    print(f"  STATUS: Decryption key not found in known database")
    print(f"{'='*70}")
    print(f"\n[!] The backup uses a proprietary encryption key")
    print(f"[!] Options remaining:")
    print(f"    1. Extract key from firmware (need .bin firmware file)")
    print(f"    2. Try router's serial number as key")
    print(f"    3. Try MAC address as key")
    print(f"    4. Use John the Ripper or hashcat for dictionary attack")


def search_for_password(filepath):
    """Search decrypted config for L1vt1m4eng password."""
    print(f"\n[*] Searching for L1vt1m4eng password in decrypted config...")
    
    with open(filepath, 'r', errors='ignore') as f:
        content = f.read()
    
    # Search patterns
    patterns = [
        'L1vt1m4eng', 'l1vt1m4eng',
        'password', 'passwd', 'pass',
        'AdminPasswd', 'adminPassword',
        'userPassword', 'UserPassword',
        'httpPwd', 'httpPassword',
        'sshPassword', 'telnetPassword',
    ]
    
    for pattern in patterns:
        idx = content.lower().find(pattern.lower())
        if idx >= 0:
            # Get context around the match
            start = max(0, idx - 100)
            end = min(len(content), idx + 200)
            context = content[start:end]
            print(f"\n[+] Found '{pattern}' at position {idx}:")
            print(f"    Context: ...{context}...")
            
            # Try to extract Base64 encoded password nearby
            import re
            b64_pattern = re.compile(r'[A-Za-z0-9+/]{4,}={0,2}')
            for match in b64_pattern.finditer(context):
                try:
                    decoded = base64.b64decode(match.group()).decode('utf-8', errors='ignore')
                    if decoded and len(decoded) > 2 and decoded.isprintable():
                        print(f"    Possible decoded password: {decoded}")
                except Exception:
                    pass


if __name__ == "__main__":
    main()
