"""
debug_vietlott.py - Kiểm tra API Vietlott
Cài trước: python -m pip install cloudscraper requests
Chạy: python src/debug_vietlott.py
"""
import json
import cloudscraper

scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows"})

GAMES = [
    ("Mega 6/45",  "2"),
    ("Power 6/55", "3"),
    ("Keno",       "4"),
    ("Max 3D",     "5"),
    ("Loto 5/35",  "6"),
    ("Max 3D Pro", "8"),
]

BASE = "https://api.vietlott.vn/api/prize-service/prize/get-prize"

for name, pid in GAMES:
    url = f"{BASE}?productId={pid}&pageIndex=0&pageSize=3"
    print(f"\n=== {name} (productId={pid}) ===")
    try:
        r = scraper.get(url, timeout=20)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            print(f"Preview: {json.dumps(data, ensure_ascii=False)[:600]}")
        else:
            print(f"Body: {r.text[:300]}")
    except Exception as e:
        print(f"Loi: {e}")

print("\n=== Xong ===")
