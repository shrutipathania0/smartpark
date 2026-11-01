import time
import subprocess
import urllib.request
import json
import sys

def run_smoke_test():
    print("=== STARTING SMARTPARK AI LOCAL SMOKE TEST ===")
    py_exe = "smartpark-env\\Scripts\\python.exe"
    proc = subprocess.Popen([py_exe, "app.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(4)

    endpoints = [
        ("Portal Home", "http://127.0.0.1:8000/"),
        ("Entry Machine", "http://127.0.0.1:8000/entry"),
        ("Parking Grid", "http://127.0.0.1:8000/parking"),
        ("Guard Login", "http://127.0.0.1:8000/guard/login"),
        ("Exit Machine", "http://127.0.0.1:8000/exit"),
        ("Slots API", "http://127.0.0.1:8000/api/parking/slots"),
    ]

    all_ok = True
    try:
        for name, url in endpoints:
            try:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    status = resp.status
                    body = resp.read().decode('utf-8')
                    if name == "Slots API":
                        data = json.loads(body)
                        slots_count = len(data.get("slots", []))
                        print(f"[{name}] HTTP {status} OK | Loaded {slots_count} slots")
                        assert slots_count == 15
                    else:
                        print(f"[{name}] HTTP {status} OK ({len(body)} bytes)")
            except Exception as e:
                print(f"[{name}] FAILED: {e}")
                all_ok = False
    finally:
        proc.terminate()
        proc.kill()

    if all_ok:
        print("\nAll 6 local endpoints probed successfully with HTTP 200!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_smoke_test()

