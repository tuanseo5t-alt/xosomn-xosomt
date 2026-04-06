import requests
from bs4 import BeautifulSoup
from datetime import date

url = "https://www.minhngoc.net.vn/kqxs/mien-nam/" + date.today().strftime("%d-%m-%Y") + ".html"
print("URL:", url)

r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
print("Status:", r.status_code)

soup = BeautifulSoup(r.text, "lxml")
tables = soup.find_all("table")
print("Tong so table:", len(tables))

for i, t in enumerate(tables):
    txt = t.get_text()
    if "Đặc Biệt" in txt or "Giải" in txt:
        print("\n=== TABLE", i, "class=", t.get("class"), "===")
        print(str(t)[:3000])
        break
