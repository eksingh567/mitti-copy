import time
import json
import hmac
import hashlib
import requests

API_URL = "http://localhost:5000"

def test_security():
    print("=== MITTI SECURITY & ANOMALY TEST SUITE ===")
    
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
    r = session.post(f"{API_URL}/api/login", json=payload, headers={"X-Requested-With": "XMLHttpRequest"})
    if r.status_code == 200:
        res = r.json()
        print(f"Status: 200 | Logged in as: {res['user']['name']} ({res['user']['role']})")
        token = res["access_token"]
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
    # Copy access token into cookie to trigger cookie-based code path
    cookie_session.cookies.set("access_token", token)
    r_csrf = cookie_session.get(f"{API_URL}/")
    print(f"Status: {r_csrf.status_code} | Response: {r_csrf.json() if r_csrf.status_code == 403 else 'FAIL'}")
    assert r_csrf.status_code == 403, "Error: Cookie-based request was not blocked for missing CSRF header!"

    # 5. Test Silent Token Refresh
    print("\n[Test 5] Requesting silent access token refresh via cookie...")
    # Clear access token to ensure we are testing refresh cookie path
    r_ref = session.post(f"{API_URL}/api/refresh", headers={"X-Requested-With": "XMLHttpRequest"})
    if r_ref.status_code == 200:
        res_ref = r_ref.json()
        print(f"Status: 200 | Wrote new token in-memory: {res_ref['access_token'][:25]}...")
    else:
        print(f"FAIL: Refresh failed: {r_ref.status_code} | {r_ref.text}")
        assert False, "Error: Silent refresh failed!"

    # 6. Test Sensor Anomaly Reject: High Humidity/Temp Anomaly
    print("\n[Test 6] Submitting impossible physical anomaly (Humidity=99%, Temp=48C, Raining=False)...")
    hmac_secret = b"mitti_esp8266_signing_secret_key_99"
    nonce = str(int(time.time() * 1000))
    timestamp = str(time.time())
    
    anomaly_payload = {
        "n": 130, "p": 48, "k": 220,
        "moisture": 52, "ec": 0.9, "ph": 6.9,
        "temp": 48, "humidity": 99, "raining": False
    }
    anomaly_json = json.dumps(anomaly_payload, separators=(',', ':'))
    message = f"{nonce}:{timestamp}:{anomaly_json}".encode()
    signature = hmac.new(hmac_secret, message, hashlib.sha256).hexdigest()
    
    headers_anomaly = {
        "X-Signature": signature,
        "X-Nonce": nonce,
        "X-Timestamp": timestamp,
        "Content-Type": "application/json"
    }
    
    r_anomaly = session.post(f"{API_URL}/api/sensors", data=anomaly_json, headers=headers_anomaly)
    print(f"Status: {r_anomaly.status_code} | Response: {r_anomaly.json() if r_anomaly.status_code == 400 else 'FAIL'}")
    assert r_anomaly.status_code == 400, "Error: Physical anomaly was not rejected!"
    assert "Anomaly" in r_anomaly.json().get("error", ""), "Error: Expected Anomaly error description!"
    
    # 7. Test Sensor Anomaly Reject: Saturated zero EC Anomaly
    print("\n[Test 7] Submitting impossible physical anomaly (Moisture=100%, EC=0)...")
    nonce2 = str(int(time.time() * 1000) + 1)
    timestamp2 = str(time.time())
    
    anomaly_payload2 = {
        "n": 130, "p": 48, "k": 220,
        "moisture": 100, "ec": 0.0, "ph": 6.9,
        "temp": 30, "humidity": 60, "raining": False
    }
    anomaly_json2 = json.dumps(anomaly_payload2, separators=(',', ':'))
    message2 = f"{nonce2}:{timestamp2}:{anomaly_json2}".encode()
    signature2 = hmac.new(hmac_secret, message2, hashlib.sha256).hexdigest()
    
    headers_anomaly2 = {
        "X-Signature": signature2,
        "X-Nonce": nonce2,
        "X-Timestamp": timestamp2,
        "Content-Type": "application/json"
    }
    
    r_anomaly2 = session.post(f"{API_URL}/api/sensors", data=anomaly_json2, headers=headers_anomaly2)
    print(f"Status: {r_anomaly2.status_code} | Response: {r_anomaly2.json() if r_anomaly2.status_code == 400 else 'FAIL'}")
    assert r_anomaly2.status_code == 400, "Error: Physical zero EC anomaly was not rejected!"
    assert "Anomaly" in r_anomaly2.json().get("error", ""), "Error: Expected Anomaly error description!"
    
    print("\n=== ALL SECURITY & ANOMALY VERIFICATION TESTS PASSED ===\n")

if __name__ == "__main__":
    test_security()
