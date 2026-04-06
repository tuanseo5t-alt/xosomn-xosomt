"""
fetcher.py - Thu thập dữ liệu Vietlott từ api.vietlott.vn
Hỗ trợ: Mega 6/45, Power 6/55, Loto 5/35, Max 3D, Max 3D Pro, Keno, Bingo 18
"""
from __future__ import annotations

import logging
import time
from datetime import date, datetime, timedelta

import cloudscraper

logger = logging.getLogger(__name__)

API_BASE = "https://api.vietlott.vn/api/prize-service/prize/get-prize"

# Cấu hình từng loại vé
GAMES = {
    "mega645": {
        "name": "Mega 6/45",
        "product_id": 2,
        "number_count": 6,
        "draw_days": [2, 4, 6],  # Thứ 3, 5, 7
    },
    "power655": {
        "name": "Power 6/55",
        "product_id": 3,
        "number_count": 6,
        "extra_count": 1,  # Số Power
        "draw_days": [2, 4, 6],  # Thứ 3, 5, 7
    },
    "loto535": {
        "name": "Loto 5/35",
        "product_id": 6,
        "number_count": 5,
        "draw_days": [1, 3, 5],  # Thứ 2, 4, 6
    },
    "max3d": {
        "name": "Max 3D",
        "product_id": 5,
        "number_count": 3,
        "draw_days": [0, 2, 4],  # Thứ 2, 4, 6
    },
    "max3dpro": {
        "name": "Max 3D Pro",
        "product_id": 8,
        "number_count": 6,
        "draw_days": [0, 2, 4],
    },
    "keno": {
        "name": "Keno",
        "product_id": 4,
        "number_count": 20,
        "draw_days": list(range(7)),  # Mỗi ngày
    },
    "bingo18": {
        "name": "Bingo 18",
        "product_id": 9,
        "number_count": 18,
        "draw_days": list(range(7)),
    },
}


def _make_scraper():
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )


def fetch_game(game_key: str, page: int = 0, page_size: int = 100) -> list[dict]:
    """
    Tải kết quả một loại vé Vietlott.
    Trả về danh sách kết quả, mỗi phần tử là một kỳ quay.
    """
    if game_key not in GAMES:
        raise ValueError(f"Game không hợp lệ: {game_key}. Chọn trong: {list(GAMES.keys())}")

    cfg = GAMES[game_key]
    url = f"{API_BASE}?productId={cfg['product_id']}&pageIndex={page}&pageSize={page_size}"
    logger.debug("Fetching %s page=%d", cfg["name"], page)

    scraper = _make_scraper()
    try:
        r = scraper.get(url, timeout=30)
        r.raise_for_status()
    except Exception as exc:
        logger.warning("Lỗi fetch %s: %s", cfg["name"], exc)
        return []

    try:
        data = r.json()
    except Exception:
        logger.warning("Không parse được JSON từ %s", url)
        return []

    return _parse_results(data, game_key, cfg)


def fetch_game_all(game_key: str, delay: float = 1.0) -> list[dict]:
    """Tải toàn bộ lịch sử của một loại vé."""
    all_results = []
    page = 0
    page_size = 100

    while True:
        results = fetch_game(game_key, page=page, page_size=page_size)
        if not results:
            break
        all_results.extend(results)
        logger.info("%s: Trang %d - %d kết quả", GAMES[game_key]["name"], page, len(results))
        if len(results) < page_size:
            break
        page += 1
        time.sleep(delay)

    return all_results


def fetch_game_date_range(game_key: str, from_date: date, to_date: date, delay: float = 1.0) -> list[dict]:
    """Tải kết quả trong khoảng ngày."""
    all_results = fetch_game_all(game_key, delay=delay)
    filtered = [
        r for r in all_results
        if from_date <= datetime.strptime(r["date"], "%Y-%m-%d").date() <= to_date
    ]
    return filtered


def _parse_results(data: dict | list, game_key: str, cfg: dict) -> list[dict]:
    """Phân tích dữ liệu JSON trả về từ API."""
    results = []

    # API trả về dạng {"data": [...]} hoặc trực tiếp [...]
    if isinstance(data, dict):
        items = data.get("data", data.get("result", data.get("items", [])))
    elif isinstance(data, list):
        items = data
    else:
        logger.warning("Cấu trúc JSON không nhận ra: %s", type(data))
        return []

    for item in items:
        record = _parse_item(item, game_key, cfg)
        if record:
            results.append(record)

    return results


def _parse_item(item: dict, game_key: str, cfg: dict) -> dict | None:
    """Phân tích một kỳ quay."""
    try:
        # Lấy ngày
        draw_date = _extract_date(item)
        if not draw_date:
            return None

        # Lấy số kỳ
        draw_id = str(item.get("id", item.get("drawId", item.get("ticketId", ""))))

        # Lấy dãy số trúng
        numbers = _extract_numbers(item)

        # Jackpot (nếu có)
        jackpot = _extract_jackpot(item)

        record = {
            "date": draw_date,
            "draw_id": draw_id,
            "game": game_key,
            "game_name": cfg["name"],
            "numbers": " ".join(str(n).zfill(2) for n in numbers),
            "jackpot": jackpot,
        }

        # Số đặc biệt (Power number cho Power 6/55)
        if "extra_count" in cfg:
            extra = _extract_extra(item)
            record["power_number"] = str(extra) if extra else ""

        return record

    except Exception as exc:
        logger.debug("Lỗi parse item: %s - %s", exc, item)
        return None


def _extract_date(item: dict) -> str:
    """Lấy ngày quay từ item."""
    for key in ["drawDate", "date", "drawTime", "issueDate", "time"]:
        val = item.get(key)
        if val:
            for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%SZ"]:
                try:
                    return datetime.strptime(str(val)[:19], fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
    return ""


def _extract_numbers(item: dict) -> list:
    """Lấy dãy số trúng từ item."""
    for key in ["winningNumbers", "numbers", "drawResult", "result", "ballOrder", "balls"]:
        val = item.get(key)
        if val:
            if isinstance(val, list):
                return [int(n) for n in val if str(n).isdigit()]
            if isinstance(val, str):
                return [int(n) for n in val.split() if n.isdigit()]
    return []


def _extract_extra(item: dict) -> int | None:
    """Lấy số Power/Extra."""
    for key in ["powerNumber", "bonusNumber", "extraNumber", "bonusBall"]:
        val = item.get(key)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                pass
    return None


def _extract_jackpot(item: dict) -> str:
    """Lấy giá trị jackpot."""
    for key in ["jackpot", "jackpot1", "prizeValue", "prize"]:
        val = item.get(key)
        if val is not None and val != 0:
            return str(val)
    return ""
