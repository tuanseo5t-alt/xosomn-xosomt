"""
main.py - Thu thập dữ liệu Vietlott
Dùng:
  python src/main.py                        # Tất cả game, 100 kỳ gần nhất
  python src/main.py --game mega645        # Chỉ Mega 6/45
  python src/main.py --all                 # Toàn bộ lịch sử
  python src/main.py --page-size 50        # Số kỳ mỗi trang
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import fetcher
import storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Thu thập dữ liệu Vietlott")
    parser.add_argument("--game", choices=list(fetcher.GAMES.keys()),
                        help="Chỉ chạy một loại game (mặc định: tất cả)")
    parser.add_argument("--all", action="store_true",
                        help="Lấy toàn bộ lịch sử")
    parser.add_argument("--page-size", type=int, default=100,
                        help="Số kỳ quay mỗi trang (mặc định: 100)")
    parser.add_argument("--delay", type=float, default=1.5,
                        help="Thời gian chờ giữa các lần tải (giây)")
    return parser.parse_args()


def run_game(game_key: str, args) -> None:
    cfg = fetcher.GAMES[game_key]
    logger.info("=== %s ===", cfg["name"])

    if args.all:
        results = fetcher.fetch_game_all(game_key, delay=args.delay)
    else:
        results = fetcher.fetch_game(game_key, page=0, page_size=args.page_size)

    if results:
        logger.info("%s: Tìm thấy %d kỳ quay", cfg["name"], len(results))
        storage.save(results, game_key)
    else:
        logger.warning("%s: Không lấy được dữ liệu", cfg["name"])


def main():
    args = parse_args()
    games_to_run = [args.game] if args.game else list(fetcher.GAMES.keys())

    logger.info("Bắt đầu thu thập Vietlott - %d game", len(games_to_run))

    for game_key in games_to_run:
        try:
            run_game(game_key, args)
        except Exception as exc:
            logger.error("Lỗi khi chạy %s: %s", game_key, exc)

    logger.info("Hoàn tất!")


if __name__ == "__main__":
    main()
