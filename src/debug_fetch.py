"""
debug_fetch.py - Công cụ kiểm tra và debug việc lấy dữ liệu

Chạy: python src/debug_fetch.py

Script này sẽ:
1. Tải trang web minhngoc.net.vn
2. In ra cấu trúc HTML để kiểm tra
3. Thử parse và in kết quả tìm được
"""
from __future__ import annotations

import sys
from datetime import date

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def debug(region: str = "mien-nam", test_date: str | None = None) -> None:
    if test_date is None:
        test_date = date.today().strftime("%d-%m-%Y")

    url = f"https://www.minhngoc.net.vn/kqxs/{region}/{test_date}.html"
    print(f"\n{'='*60}")
    print(f"URL: {url}")
    print(f"{'='*60}\n")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        print(f"Status: {resp.status_code} OK")
        print(f"Content-Type: {resp.headers.get('Content-Type', 'unknown')}")
        print(f"Content length: {len(resp.text)} chars\n")
    except requests.RequestException as e:
        print(f"LỖI kết nối: {e}")
        return

    soup = BeautifulSoup(resp.text, "lxml")

    # --- Kiểm tra tất cả table ---
    all_tables = soup.find_all("table")
    print(f"Tổng số <table> tìm thấy: {len(all_tables)}")

    bkqxs_tables = soup.find_all("table", class_="bkqxs")
    print(f"Số <table class='bkqxs'> tìm thấy: {len(bkqxs_tables)}\n")

    if bkqxs_tables:
        tables_to_check = bkqxs_tables
    else:
        tables_to_check = all_tables[:5]  # Xem 5 table đầu tiên

    for i, table in enumerate(tables_to_check):
        print(f"{'─'*50}")
        print(f"TABLE #{i+1} | class={table.get('class', 'none')}")

        # In 5 dòng đầu của table
        rows = table.find_all("tr")
        print(f"  Số hàng (tr): {len(rows)}")

        for j, row in enumerate(rows[:8]):
            cells = row.find_all(["td", "th"])
            cell_texts = [c.get_text(strip=True)[:30] for c in cells]
            print(f"  Row {j+1}: {cell_texts}")

        # Tìm tên đài
        tinh = table.find(["td", "th"], class_="tinh")
        th = table.find("th")
        print(f"  td/th.tinh: {tinh.get_text(strip=True)[:40] if tinh else 'không tìm thấy'}")
        print(f"  th đầu tiên: {th.get_text(strip=True)[:40] if th else 'không tìm thấy'}")
        print()

    # --- Thử parse ---
    print(f"\n{'='*60}")
    print("KẾT QUẢ PARSE:")
    print(f"{'='*60}")

    try:
        if region == "mien-nam":
            import fetcher_xsmn as fetcher
        else:
            import fetcher_xsmt as fetcher

        day = date(int(test_date[6:10]), int(test_date[3:5]), int(test_date[0:2]))
        results = fetcher._parse_page(resp.text, day)

        if results:
            print(f"Tìm thấy {len(results)} đài:\n")
            for r in results:
                print(f"  Đài   : {r['station']}")
                print(f"  Đặc biệt: {r['special']}")
                print(f"  Nhất  : {r['first']}")
                print(f"  Nhì   : {r['second']}")
                print()
        else:
            print("KHÔNG tìm thấy dữ liệu nào!")
            print("\nĐây là 500 ký tự đầu của HTML trang web:")
            print(resp.text[:500])
    except Exception as e:
        print(f"Lỗi khi parse: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    region = sys.argv[1] if len(sys.argv) > 1 else "mien-nam"
    test_date = sys.argv[2] if len(sys.argv) > 2 else None

    # Chạy debug
    debug(region, test_date)

    print("\n" + "="*60)
    print("HƯỚNG DẪN DÙNG:")
    print("  python src/debug_fetch.py                      # XSMN hôm nay")
    print("  python src/debug_fetch.py mien-nam 04-04-2026  # XSMN ngày cụ thể")
    print("  python src/debug_fetch.py mien-trung           # XSMT hôm nay")
    print("="*60)
