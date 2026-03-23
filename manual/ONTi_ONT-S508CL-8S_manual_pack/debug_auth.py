#!/usr/bin/env python3
"""Debug the exact auth flow of the Kaon PG2447 router API."""
import requests
import re
import json

session = requests.Session()
base = 'http://192.168.1.1'

print("=" * 60)
print("  Kaon PG2447 API Auth Flow Debug")
print("=" * 60)

# Test 1: POST empty to /api/auth/token
print("\n=== Test 1: POST empty body to /api/auth/token ===")
try:
    r = session.post(f'{base}/api/auth/token', timeout=5,
                     headers={'Content-Type': 'application/json'}, data='{}')
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: POST with username
print("\n=== Test 2: POST username to /api/auth/token ===")
try:
    r = session.post(f'{base}/api/auth/token', timeout=5,
                     headers={'Content-Type': 'application/json'},
                     json={"auth": {"username": "admin"}})
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: GET the main page and find JS files
print("\n=== Test 3: Fetching main page and extracting JS files ===")
try:
    r = session.get(f'{base}/', timeout=5)
    scripts = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', r.text)
    print(f"Script files: {scripts}")
    
    # Find auth-related references
    auth_refs = re.findall(r'(?:auth|token|challenge|login|md5|hash|password)[^\n]{0,80}',
                           r.text, re.IGNORECASE)
    for ref in auth_refs[:15]:
        print(f"  Auth ref: {ref.strip()}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Fetch JS files to find auth logic
print("\n=== Test 4: Downloading JS files ===")
if scripts:
    for script in scripts[:5]:
        # Handle relative paths
        if script.startswith('/'):
            url = f'{base}{script}'
        elif script.startswith('http'):
            url = script
        else:
            url = f'{base}/{script}'
        
        print(f"\n--- Fetching: {url} ---")
        try:
            r = session.get(url, timeout=5)
            if r.status_code == 200:
                content = r.text
                print(f"  Size: {len(content)} bytes")
                
                # Search for auth patterns
                auth_patterns = re.findall(
                    r'(?:auth|token|challenge|login|md5|hash|password|api/auth)[^\n]{0,120}',
                    content, re.IGNORECASE
                )
                if auth_patterns:
                    print(f"  Found {len(auth_patterns)} auth references:")
                    for p in auth_patterns[:20]:
                        print(f"    {p.strip()}")
                
                # Search for API endpoint definitions
                api_refs = re.findall(r'["\']api/[^"\']+["\']', content)
                if api_refs:
                    print(f"  API endpoints found:")
                    for a in set(api_refs):
                        print(f"    {a}")
            else:
                print(f"  Status: {r.status_code}")
        except Exception as e:
            print(f"  Error: {e}")

# Test 5: Try more API paths
print("\n=== Test 5: Testing additional API endpoints ===")
test_paths = [
    '/api/auth/token',
    '/api/auth/challenge', 
    '/api/auth/login',
    '/api/session',
    '/api/user',
    '/api/system',
    '/api/device',
    '/api/config',
]
for path in test_paths:
    try:
        r = session.get(f'{base}{path}', timeout=5)
        marker = "***" if r.status_code not in [401, 404] else ""
        print(f"  GET  {path:30s} -> {r.status_code} {marker}")
    except:
        print(f"  GET  {path:30s} -> TIMEOUT")
    
    try:
        r = session.post(f'{base}{path}', timeout=5, 
                        headers={'Content-Type': 'application/json'}, data='{}')
        marker = "***" if r.status_code not in [401, 404] else ""
        print(f"  POST {path:30s} -> {r.status_code} {r.text[:100] if r.status_code != 401 else ''} {marker}")
    except:
        print(f"  POST {path:30s} -> TIMEOUT")

print("\n=== Debug complete ===")
