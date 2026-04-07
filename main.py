#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from datetime import datetime, date

from bazi_calculator import get_bazi_chart, parse_birth_datetime
from core_scoring import calculate_core_scores, format_core_score_result
from date_energy_calculator import get_date_energy, parse_target_date, format_date_energy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Main entry for BaZi chart and date energy lookup."
    )
    parser.add_argument(
        "--birth-datetime",
        type=parse_birth_datetime,
        default=datetime(1990, 7, 15, 14, 30),
        help="Birth datetime in format 'YYYY-MM-DD HH:MM' (default: 1990-07-15 14:30)",
    )
    parser.add_argument(
        "--target-date",
        type=parse_target_date,
        default=date(2026, 4, 2),
        help="Target date in format YYYY-MM-DD (default: 2026-04-02)",
    )
    return parser


def format_chart_summary(birth_dt: datetime, chart) -> str:
    return "\n".join(
        [
            birth_dt.strftime("%Y-%m-%d %H:%M"),
            (
                f"{chart.year_pillar.name}年"
                f"{chart.month_pillar.name}月"
                f"{chart.day_pillar.name}日"
                f"{chart.hour_pillar.name}時"
            ),
        ]
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    birth_dt = args.birth_datetime
    target_date = args.target_date

    chart = get_bazi_chart(birth_dt)
    energy = get_date_energy(target_date)
    core_scores = calculate_core_scores(
        birth_dt.strftime("%Y-%m-%d %H:%M"),
        chart,
        energy,
    )

    print("=== 個人八字 ===")
    print(format_chart_summary(birth_dt, chart))

    print("\n=== 特定日期五行能量 ===")
    print(format_date_energy(energy))

    print("\n=== 核心算法 ===")
    print(format_core_score_result(core_scores))


if __name__ == "__main__":
    main()
