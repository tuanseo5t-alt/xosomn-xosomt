"""
fetcher_xsmn.py - Thu thập dữ liệu Xổ Số Miền Nam từ minhngoc.net.vn

Cấu trúc HTML thực tế:
  - table.bkqtinhmiennam  → mỗi đài
  - span.loaive           → mã đài chính xác (ví dụ: XSTG, XSKG)
  - div.ngay              → ngày quay
  - table.box_kqxs_content → bảng giải thưởng
"""
from __future__ import annotations

import logging
import re
import time
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.minhngoc.net.vn/kqxs/mien-nam/{date}.html"
START_DATE = date(2008, 1, 1)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

PRIZE_MAP = [
    (["đặc biệt", "giải đb", "giải ĐB", "đb"], "special"),
    (["giải nhất", "nhất"], "first"),
    (["giải nhì", "nhì"], "second"),
    (["giải ba"], "third"),
    (["giải tư"], "fourth"),
    (["giải năm"], "fifth"),
    (["giải sáu"], "sixth"),
    (["giải bảy"], "seventh"),
    (["giải 8", "giải tám"], "eighth"),
]

# Mã đài chính xác từ span.loaive → tên đài
# Lấy từ HTML thực tế tại minhngoc.net.vn
STATION_CODE_MAP = {
    # Thứ 2: TP.HCM, Đồng Tháp, Cà Mau
    "XSHCM": "Hồ Chí Minh",
    "XSDT":  "Đồng Tháp",
    "XSCM":  "Cà Mau",
    # Thứ 3: Bến Tre, Vũng Tàu, Bạc Liêu
    "XSBTR": "Bến Tre",
    "XSVT":  "Vũng Tàu",
    "XSBL":  "Bạc Liêu",
    # Thứ 4: Đồng Nai, Cần Thơ, Sóc Trăng
    "XSDN":  "Đồng Nai",
    "XSCT":  "Cần Thơ",
    "XSST":  "Sóc Trăng",
    # Thứ 5: Tây Ninh, An Giang, Bình Thuận
    "XSTN":  "Tây Ninh",
    "XSAG":  "An Giang",
    "XSBTH": "Bình Thuận",
    # Thứ 6: Vĩnh Long, Bình Dương, Trà Vinh
    "XSVL":  "Vĩnh Long",
    "XSBD":  "Bình Dương",
    "XSTV":  "Trà Vinh",
    # Thứ 7: TP.HCM, Long An, Bình Phước, Hậu Giang
    "XSLA":  "Long An",
    "XSBP":  "Bình Phước",
    "XSHG":  "Hậu Giang",
    # Chủ nhật: Tiền Giang, Kiên Giang, Đà Lạt
    "XSTG":  "Tiền Giang",
    "XSKG":  "Kiên Giang",
    "XSDL":  "Đà Lạt",
    # Thêm mã dự phòng
    "XSDNO": "Đắk Nông",
}


def fetch_day(target_date: date, delay: float = 1.0) -> list[dict]:
    """Tải kết quả XSMN cho một ngày. Trả về danh sách dict mỗi đài."""
    date_str = target_date.strftime("%d-%m-%Y")
    url = BASE_URL.format(date=date_str)
    logger.debug("Fetching XSMN %s", date_str)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return []

    time.sleep(delay)
    return _parse_page(resp.text, target_date)


def _parse_page(html: str, target_date: date) -> list[dict]:
    """Phân tích HTML và trả về danh sách kết quả đúng ngày target_date."""
    soup = BeautifulSoup(html, "lxml")
    results = []

    for station_table in soup.find_all("table", class_="bkqtinhmiennam"):
        record = _parse_station_table(station_table, target_date)
        if record:
            results.append(record)

    if not results:
        logger.warning("Không tìm thấy dữ liệu cho ngày %s", target_date)

    return results


def _extract_header_date(station_table) -> date | None:
    """Lấy ngày từ div.ngay hoặc text chứa DD/MM/YYYY."""
    ngay_div = station_table.find("div", class_="ngay")
    if ngay_div:
        m = re.search(r"(\d{2}/\d{2}/\d{4})", ngay_div.get_text())
        if m:
            try:
                d, mo, y = m.group(1).split("/")
                return date(int(y), int(mo), int(d))
            except (ValueError, TypeError):
                pass
    first_row = station_table.find("tr")
    if first_row:
        m = re.search(r"(\d{2}/\d{2}/\d{4})", first_row.get_text())
        if m:
            try:
                d, mo, y = m.group(1).split("/")
                return date(int(y), int(mo), int(d))
            except (ValueError, TypeError):
                pass
    return None


def _extract_station_name(station_table) -> str:
    """Lấy tên đài từ span.loaive → tra STATION_CODE_MAP."""
    loaive = station_table.find("span", class_="loaive")
    if loaive:
        raw = loaive.get_text(strip=True)
        # Lấy phần mã trước dấu " - " (vd: "XSTG - Loại vé: ..." → "XSTG")
        code = raw.split(" - ")[0].split()[0].strip()
        if code in STATION_CODE_MAP:
            return STATION_CODE_MAP[code]
        logger.warning("Mã đài chưa có trong map: '%s' (raw: '%s')", code, raw)
        return code

    # Fallback: lấy tên từ thẻ <a>
    first_row = station_table.find("tr")
    if first_row:
        day_names = {"thứ hai", "thứ ba", "thứ tư", "thứ năm",
                     "thứ sáu", "thứ bảy", "chủ nhật"}
        for a_tag in first_row.find_all("a"):
            name = a_tag.get_text(strip=True)
            if (name and len(name) > 3
                    and name.lower() not in day_names
                    and not re.match(r"\d{2}/\d{2}/\d{4}", name)):
                return name
    return ""


def _parse_station_table(station_table, target_date: date) -> dict | None:
    """Phân tích một bảng đài. Bỏ qua nếu ngày không khớp target_date."""
    header_date = _extract_header_date(station_table)
    if header_date and header_date != target_date:
        return None

    station_name = _extract_station_name(station_table)
    if not station_name:
        return None

    prize_table = station_table.find("table", class_="box_kqxs_content") or station_table

    record: dict = {
        "date": target_date.strftime("%Y-%m-%d"),
        "station": station_name,
        "special": "", "first": "", "second": "", "third": "",
        "fourth": "", "fifth": "", "sixth": "", "seventh": "", "eighth": "",
    }

    for row in prize_table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        key = _match_prize(cells[0].get_text(strip=True).lower())
        if not key:
            continue
        numbers = re.findall(r"\d+", cells[1].get_text(" ", strip=True))
        if numbers:
            record[key] = ", ".join(numbers)

    has_data = any(record[k] for k in [
        "special", "first", "second", "third",
        "fourth", "fifth", "sixth", "seventh", "eighth"
    ])
    return record if has_data else None


def _match_prize(label: str) -> str | None:
    label = label.lower().strip()
    for keywords, prize_key in PRIZE_MAP:
        if any(kw in label for kw in keywords):
            return prize_key
    return None


def date_range(from_date: date, to_date: date) -> list[date]:
    days, cur = [], from_date
    while cur <= to_date:
        days.append(cur)
        cur += timedelta(days=1)
    return days
