import time
import json
import hmac
import hashlib
import requests

API_URL = "http://localhost:5000/api/v1"

def test_security():
    print("=== MITTI SECURITY & ANOMALY TEST SUITE (v1) ===")
    
    # Establish session to persist HttpOnly refresh cookies automatically
    session = requests.Session()
    
    # 1. Test Unauthorized Access (Should be blocked with 401)
    print("\n[Test 1] Accessing protected dashboard without credentials...")
    r = session.get(f"{API_URL}/")
    print(f"Status: {r.status_code} | Response: {r.json() if r.status_code == 401 else 'FAIL'}")
    assert r.status_code == 401, "Error: Unauthorized route was accessed!"
    
    # 2. Test Login Authentication against SQLite DB
    print("\n[Test 2] Logging in via SQLite DB credentials...")
    payload = {"phone": "1234567890", "password": "mitti_admin_secure_secret_password_2026"}
    r = session.post(f"{API_URL}/login", json=payload, headers={"X-Requested-With": "XMLHttpRequest"})
    if r.status_code == 200:
        res = r.json()
        print(f"Status: 200 | Logged in as: {res['user']['name']} ({res['user']['role']})")
        token = res["access_token"]
        # Backup refresh token cookie to simulate replay/reuse attacks
        old_refresh_cookie = session.cookies.get("refresh_token")
    else:
        print(f"FAIL: Login failed: {r.status_code} | {r.text}")
        return
        
    # 3. Test Authorized Dashboard Access with JWT
    print("\n[Test 3] Accessing dashboard with valid JWT Bearer header...")
    headers = {"Authorization": f"Bearer {token}", "X-Requested-With": "XMLHttpRequest"}
    r = session.get(f"{API_URL}/", headers=headers)
    print(f"Status: {r.status_code} | Response key counts: {len(r.json().get('data', {}))} sensor readings.")
    assert r.status_code == 200, "Error: Valid token dashboard access failed!"
    
    # 4. Test CSRF Protection (Missing X-Requested-With header)
    print("\n[Test 4] Accessing dashboard using cookies but WITHOUT X-Requested-With CSRF header...")
    cookie_session = requests.Session()
    cookie_session.cookies.set("access_token", token)
    r_csrf = cookie_session.get(f"{API_URL}/")
    print(f"Status: {r_csrf.status_code} | Response: {r_csrf.json() if r_csrf.status_code == 403 else 'FAIL'}")
    assert r_csrf.status_code == 403, "Error: Cookie-based request was not blocked for missing CSRF header!"

    # 5. Test Silent Token Refresh & Rotation (RTR)
    print("\n[Test 5] Requesting silent access token refresh (Rotates token)...")
    r_ref = session.post(f"{API_URL}/refresh", headers={"X-Requested-With": "XMLHttpRequest"})
    if r_ref.status_code == 200:
        res_ref = r_ref.json()
        print(f"Status: 200 | Wrote new token in-memory: {res_ref['access_token'][:25]}...")
    else:
        print(f"FAIL: Refresh failed: {r_ref.status_code} | {r_ref.text}")
        assert False, "Error: Silent refresh failed!"

    # 6. Test Refresh Token Rotation Reuse Attack Block
    print("\n[Test 6] Reusing the OLD refresh token to hijack session (RTR breach detection)...")
    hacker_session = requests.Session()
    hacker_session.cookies.set("refresh_token", old_refresh_cookie)
    r_hack = hacker_session.post(f"{API_URL}/refresh", headers={"X-Requested-With": "XMLHttpRequest"})
    print(f"Status: {r_hack.status_code} | Response: {r_hack.json() if r_hack.status_code == 401 else 'FAIL'}")
    assert r_hack.status_code == 401, "Error: Reused refresh token was not blocked!"
    assert "hijacked" in r_hack.json().get("error", ""), "Error: Expected 'hijacked' reuse breach explanation!"

    # 7. Test Device HMAC Authentication: Valid Registered Device
    print("\n[Test 7] Submitting telemetry from registered device 'esp8266_test_node_01' with valid HMAC...")
    hmac_secret = b"mitti_esp8266_signing_secret_key_99"
    nonce = str(int(time.time() * 1000))
    timestamp = str(time.time())
    
    sensor_data = {
        "n": 130, "p": 48, "k": 220,
        "moisture": 52, "ec": 0.9, "ph": 6.9,
        "temp": 30, "humidity": 62
    }
    sensor_json = json.dumps(sensor_data, separators=(',', ':'))
    message = f"{nonce}:{timestamp}:{sensor_json}".encode()
    signature = hmac.new(hmac_secret, message, hashlib.sha256).hexdigest()
    
    headers_device = {
        "X-Signature": signature,
        "X-Nonce": nonce,
        "X-Timestamp": timestamp,
        "X-Device-ID": "esp8266_test_node_01",
        "X-Firmware-Version": "1.0.5",
        "Content-Type": "application/json"
    }
    
    r_device = session.post(f"{API_URL}/sensors", data=sensor_json, headers=headers_device)
    print(f"Status: {r_device.status_code} | Response: {r_device.json()}")
    assert r_device.status_code == 200, "Error: Valid registered device telemetry rejected!"
    
    # 8. Test Device HMAC Authentication: Unauthorized / Fake Device ID
    print("\n[Test 8] Submitting telemetry from unregistered device ID 'fake_esp8266_node_99'...")
    headers_fake = headers_device.copy()
    headers_fake["X-Device-ID"] = "fake_esp8266_node_99"
    r_fake = session.post(f"{API_URL}/sensors", data=sensor_json, headers=headers_fake)
    print(f"Status: {r_fake.status_code} | Response: {r_fake.json() if r_fake.status_code == 403 else 'FAIL'}")
    assert r_fake.status_code == 403, "Error: Unregistered device was not blocked!"

    # 9. Test Sensor Anomaly Reject: High Humidity/Temp Anomaly
    print("\n[Test 9] Submitting impossible physical anomaly (Humidity=99%, Temp=48C, Raining=False)...")
    nonce3 = str(int(time.time() * 1000) + 5)
    timestamp3 = str(time.time())
    
    anomaly_payload = {
        "n": 130, "p": 48, "k": 220,
        "moisture": 52, "ec": 0.9, "ph": 6.9,
        "temp": 48, "humidity": 99, "raining": False
    }
    anomaly_json = json.dumps(anomaly_payload, separators=(',', ':'))
    message = f"{nonce3}:{timestamp3}:{anomaly_json}".encode()
    signature = hmac.new(hmac_secret, message, hashlib.sha256).hexdigest()
    
    headers_anomaly = {
        "X-Signature": signature,
        "X-Nonce": nonce3,
        "X-Timestamp": timestamp3,
        "X-Device-ID": "esp8266_test_node_01",
        "Content-Type": "application/json"
    }
    
    r_anomaly = session.post(f"{API_URL}/sensors", data=anomaly_json, headers=headers_anomaly)
    print(f"Status: {r_anomaly.status_code} | Response: {r_anomaly.json() if r_anomaly.status_code == 400 else 'FAIL'}")
    assert r_anomaly.status_code == 400, "Error: Physical anomaly was not rejected!"
    assert "Anomaly" in r_anomaly.json().get("error", ""), "Error: Expected Anomaly error description!"
    
    # 10. Test User Registration via /api/v1/register
    print("\n[Test 10] Testing User Registration endpoint...")
    reg_phone = f"999{int(time.time()) % 10000000}" # Generate dynamic phone number
    reg_payload = {
        "phone": reg_phone,
        "name": "New Farmer Test",
        "password": "secure_farmer_password_2026",
        "state": "Maharashtra",
        "city": "Pune"
    }
    r_reg = session.post(f"{API_URL}/register", json=reg_payload, headers={"X-Requested-With": "XMLHttpRequest"})
    print(f"Status: {r_reg.status_code} | Response: {r_reg.json()}")
    assert r_reg.status_code == 201, "Error: User registration endpoint failed!"
    
    print("\n=== ALL SECURITY & RTR VERIFICATION TESTS PASSED ===\n")

if __name__ == "__main__":
    test_security()
