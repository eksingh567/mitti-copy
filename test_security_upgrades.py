import time
import json
import hmac
import hashlib
import requests

API_URL = "http://localhost:5000"

def test_security():
    print("=== MITTI SECURITY TEST SUITE ===")
    
    # 1. Test Unauthorized Access (Should be blocked with 401)
    print("\n[Test 1] Accessing protected dashboard without JWT...")
    r = requests.get(f"{API_URL}/")
    print(f"Status: {r.status_code} | Response: {r.json() if r.status_code == 401 else 'FAIL'}")
    assert r.status_code == 401, "Error: Unauthorized route was accessed!"
    
    # 2. Test Login Authentication
    print("\n[Test 2] Logging in with user '1234567890' and default password 'MittiPass123!'...")
    payload = {"phone": "1234567890", "password": "mitti_admin_secure_secret_password_2026"}
    r = requests.post(f"{API_URL}/api/login", json=payload)
    if r.status_code == 200:
        res = r.json()
        print(f"Status: 200 | Logged in as: {res['user']['name']} ({res['user']['role']})")
        token = res["access_token"]
    else:
        print(f"FAIL: Login failed: {r.status_code} | {r.text}")
        return
        
    # 3. Test Authorized Dashboard Access
    print("\n[Test 3] Accessing dashboard with valid JWT bearer token...")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{API_URL}/", headers=headers)
    print(f"Status Code: {r.status_code}")
    print(f"Raw Response: {r.text.encode('ascii', errors='replace').decode('ascii')[:300]}")
    print(f"Status: {r.status_code} | Response key counts: {len(r.json().get('data', {}))} sensor readings.")
    assert r.status_code == 200, "Error: Valid token dashboard access failed!"
    
    # 4. Test Malicious Image Upload Prevention
    print("\n[Test 4] Uploading an invalid/dangerous text file to /api/scan-image...")
    files = {'image': ('exploit.sh', b'#!/bin/bash\nrm -rf /', 'text/x-shellscript')}
    r = requests.post(f"{API_URL}/api/scan-image", files=files, headers=headers)
    print(f"Status: {r.status_code} | Response: {r.json() if r.status_code == 400 else 'FAIL'}")
    assert r.status_code == 400, "Error: Malicious upload was not blocked!"
    
    # 5. Test ESP8266 HMAC Signature validation
    print("\n[Test 5] Simulating ESP8266 payload with valid HMAC signature...")
    hmac_secret = b"mitti_esp8266_signing_secret_key_99"
    nonce = str(int(time.time() * 1000))
    timestamp = str(time.time())
    
    sensor_data = {
        "n": 130, "p": 48, "k": 220,
        "moisture": 52, "ec": 0.9, "ph": 6.9,
        "temp": 30, "humidity": 62
    }
    sensor_json = json.dumps(sensor_data, separators=(',', ':'))
    
    # Calculate HMAC signature
    message = f"{nonce}:{timestamp}:{sensor_json}".encode()
    signature = hmac.new(hmac_secret, message, hashlib.sha256).hexdigest()
    
    iot_headers = {
        "X-Signature": signature,
        "X-Nonce": nonce,
        "X-Timestamp": timestamp,
        "Content-Type": "application/json"
    }
    
    r = requests.post(f"{API_URL}/api/sensors", data=sensor_json, headers=iot_headers)
    print(f"Status: {r.status_code} | Response: {r.json()}")
    assert r.status_code == 200, "Error: Valid ESP8266 signature rejected!"
    
    # 6. Test Replay Attack Protection (Sending same nonce again)
    print("\n[Test 6] Sending the exact same ESP8266 signature & nonce again (Replay attack simulation)...")
    r_replay = requests.post(f"{API_URL}/api/sensors", data=sensor_json, headers=iot_headers)
    print(f"Status: {r_replay.status_code} | Response: {r_replay.json() if r_replay.status_code == 400 else 'FAIL'}")
    assert r_replay.status_code == 400, "Error: Replay attack was not blocked!"
    
    print("\n=== ALL SECURITY VERIFICATION TESTS PASSED ===\n")

if __name__ == "__main__":
    test_security()
