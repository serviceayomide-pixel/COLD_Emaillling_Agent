import urllib.request, json

import os

BASE = os.getenv("SUPABASE_URL", "https://rojuifpeywxpflaimvks.supabase.co")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

def test_api(name, url, key):
    try:
        headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        if isinstance(data, list):
            print(f"  {name}: OK ({len(data)} rows)")
        elif isinstance(data, dict):
            print(f"  {name}: OK -> {json.dumps(data)[:200]}")
        else:
            print(f"  {name}: OK -> {str(data)[:200]}")
    except Exception as e:
        print(f"  {name}: FAILED -> {e}")

print("=" * 60)
print("SUPABASE API GATEWAY TEST")
print("=" * 60)

# 1. Test REST API (PostgREST) - Tables
print("\n--- REST API (Tables) ---")
tables = ["cqc_leads", "campaign_logs", "campaign_months", "meetings", "outlook_messages"]
for t in tables:
    test_api(t, f"{BASE}/rest/v1/{t}?select=*&limit=3", ANON_KEY)

# 2. Test RPC Functions
print("\n--- RPC Functions ---")
rpcs = [
    "get_global_dashboard_metrics",
    "get_analytics_metrics",
    "get_inbox_metrics",
    "get_outbox_metrics",
    "get_meetings_metrics",
]
for rpc in rpcs:
    try:
        headers = {
            "apikey": ANON_KEY,
            "Authorization": f"Bearer {ANON_KEY}",
            "Content-Type": "application/json"
        }
        req = urllib.request.Request(f"{BASE}/rest/v1/rpc/{rpc}", data=b"{}", headers=headers, method="POST")
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        print(f"  {rpc}: OK -> {json.dumps(data)[:200]}")
    except Exception as e:
        print(f"  {rpc}: FAILED -> {e}")

# Test campaign month RPC with parameter
try:
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {ANON_KEY}",
        "Content-Type": "application/json"
    }
    body = json.dumps({"target_month": 1}).encode()
    req = urllib.request.Request(f"{BASE}/rest/v1/rpc/get_campaign_month_metrics", data=body, headers=headers, method="POST")
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    print(f"  get_campaign_month_metrics(1): OK -> {json.dumps(data)[:200]}")
except Exception as e:
    print(f"  get_campaign_month_metrics(1): FAILED -> {e}")

# 3. Test Auth endpoint
print("\n--- Auth API ---")
try:
    headers = {"apikey": ANON_KEY}
    req = urllib.request.Request(f"{BASE}/auth/v1/settings", headers=headers)
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    providers = [k for k, v in data.get("external", {}).items() if v]
    print(f"  Auth Settings: OK (enabled providers: {providers})")
except Exception as e:
    print(f"  Auth Settings: FAILED -> {e}")

# 4. Test Realtime endpoint
print("\n--- Realtime API ---")
try:
    headers = {"apikey": ANON_KEY}
    req = urllib.request.Request(f"{BASE}/realtime/v1/api/channels", headers=headers)
    resp = urllib.request.urlopen(req)
    print(f"  Realtime: OK (status {resp.status})")
except Exception as e:
    err_str = str(e)
    if "101" in err_str or "426" in err_str or "200" in err_str:
        print(f"  Realtime: OK (WebSocket upgrade expected)")
    else:
        print(f"  Realtime: FAILED -> {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
