#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path


BATCH_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BATCH_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from batch_reports.report_content import (
    ConfigError,
    build_cover_page_data,
    build_daily_report,
    get_bazi_chart,
    iter_dates,
    load_config,
)
from batch_reports.report_layout import write_reports_pdf
from batch_reports.report_styles import CONTENT_TEMPLATE_PATH

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate date-range WuXing reports from a JSON config file."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=BATCH_DIR / "config" / "config.example.json",
        help="Path to a JSON config file (default: batch_reports/config/config.example.json).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        parser.error(str(exc))

    chart = get_bazi_chart(config.birth_datetime)
    cover_page = build_cover_page_data(config, chart)
    reports = [
        build_daily_report(config.birth_datetime, chart, target_date)
        for target_date in iter_dates(config.start_date, config.end_date)
    ]

    print("=== 報表摘要 ===")
    print("姓名: %s" % config.name)
    print("日期範圍: %s" % cover_page.date_range_text)
    print("命主喜用: %s" % cover_page.fav_text)
    print("命主忌用: %s" % cover_page.unfav_text)
    print("模板檔: %s" % CONTENT_TEMPLATE_PATH)

    for report in reports:
        print()
        print(report.console_text)

    write_reports_pdf(cover_page, reports, config.output_pdf)

    print()
    print("總共生成 %s 天資料。" % len(reports))
    print("PDF 已輸出到: %s" % config.output_pdf)


if __name__ == "__main__":
    main()
