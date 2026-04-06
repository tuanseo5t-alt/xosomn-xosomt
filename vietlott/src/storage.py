"""
storage.py - Lưu dữ liệu Vietlott vào CSV và JSON
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


def save(records: list[dict], game_key: str) -> None:
    """Lưu kết quả vào CSV và JSON, tránh trùng lặp."""
    if not records:
        logger.info("Không có dữ liệu để lưu cho %s", game_key)
        return

    out_dir = DATA_DIR / game_key
    out_dir.mkdir(parents=True, exist_ok=True)

    new_df = pd.DataFrame(records)

    # Đảm bảo cột date đúng định dạng
    if "date" in new_df.columns:
        new_df["date"] = pd.to_datetime(new_df["date"]).dt.strftime("%Y-%m-%d")

    key_cols = ["date", "draw_id"] if "draw_id" in new_df.columns else ["date"]

    csv_path = out_dir / f"{game_key}.csv"
    json_path = out_dir / f"{game_key}.json"

    # Gộp với dữ liệu cũ
    if csv_path.exists():
        existing = pd.read_csv(csv_path, dtype=str).fillna("")
        combined = pd.concat([existing, new_df.astype(str)], ignore_index=True)
        combined = combined.drop_duplicates(subset=key_cols, keep="last")
    else:
        combined = new_df.astype(str)

    # Sắp xếp theo ngày giảm dần (mới nhất trước)
    if "date" in combined.columns:
        combined = combined.sort_values("date", ascending=False).reset_index(drop=True)

    # Lưu CSV
    combined.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info("Saved CSV: %s (%d dòng)", csv_path, len(combined))

    # Lưu JSON
    records_out = combined.to_dict(orient="records")
    json_path.write_text(
        json.dumps(records_out, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    logger.info("Saved JSON: %s", json_path)
