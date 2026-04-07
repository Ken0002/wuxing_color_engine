#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Union


HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

STEM_TO_ELEMENT = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

BRANCH_TO_ELEMENT = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}

HIDDEN_STEMS = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

# 節氣近似版，先用固定日期做月令切分
# 這組日期已依專案資料做過校正，主要修正少數交節邊界日
# 寅月=1, 卯月=2, ..., 丑月=12
SOLAR_MONTH_BOUNDARIES = [
    ((1, 5), 12),   # 小寒 -> 丑月
    ((2, 4), 1),    # 立春 -> 寅月
    ((3, 5), 2),    # 驚蟄 -> 卯月
    ((4, 5), 3),    # 清明 -> 辰月
    ((5, 5), 4),    # 立夏 -> 巳月
    ((6, 6), 5),    # 芒種 -> 午月
    ((7, 7), 6),    # 小暑 -> 未月
    ((8, 7), 7),    # 立秋 -> 申月
    ((9, 7), 8),    # 白露 -> 酉月
    ((10, 8), 9),   # 寒露 -> 戌月
    ((11, 7), 10),  # 立冬 -> 亥月
    ((12, 7), 11),  # 大雪 -> 子月
]

DAY_PILLAR_OFFSET = 2


@dataclass
class Pillar:
    stem: str
    branch: str

    @property
    def name(self) -> str:
        return f"{self.stem}{self.branch}"

    @property
    def stem_element(self) -> str:
        return STEM_TO_ELEMENT[self.stem]

    @property
    def branch_element(self) -> str:
        return BRANCH_TO_ELEMENT[self.branch]

    @property
    def hidden_stems(self) -> List[str]:
        return HIDDEN_STEMS[self.branch]

    def to_dict(self) -> Dict:
        return {
            "stem": self.stem,
            "branch": self.branch,
            "name": self.name,
            "stem_element": self.stem_element,
            "branch_element": self.branch_element,
            "hidden_stems": self.hidden_stems,
        }


@dataclass
class BaZiChart:
    birth_datetime: datetime
    year_pillar: Pillar
    month_pillar: Pillar
    day_pillar: Pillar
    hour_pillar: Pillar
    day_master: str

    def to_dict(self) -> Dict:
        return {
            "birth_datetime": self.birth_datetime.isoformat(sep=" "),
            "year_pillar": self.year_pillar.to_dict(),
            "month_pillar": self.month_pillar.to_dict(),
            "day_pillar": self.day_pillar.to_dict(),
            "hour_pillar": self.hour_pillar.to_dict(),
            "day_master": self.day_master,
            "day_master_element": STEM_TO_ELEMENT[self.day_master],
        }


def cyclical_index_to_ganzhi(index_60: int) -> Tuple[str, str]:
    stem = HEAVENLY_STEMS[index_60 % 10]
    branch = EARTHLY_BRANCHES[index_60 % 12]
    return stem, branch


def make_pillar(stem_idx: int, branch_idx: int) -> Pillar:
    return Pillar(
        stem=HEAVENLY_STEMS[stem_idx % 10],
        branch=EARTHLY_BRANCHES[branch_idx % 12],
    )


def approximate_li_chun(dt: Union[datetime, date]) -> date:
    y = dt.year if isinstance(dt, (datetime, date)) else dt.year
    return date(y, 2, 4)


def get_solar_month_order(dt: Union[datetime, date]) -> int:
    d = dt.date() if isinstance(dt, datetime) else dt
    md = (d.month, d.day)

    matched_order = None
    for (mday, order) in reversed(SOLAR_MONTH_BOUNDARIES):
        if md >= mday:
            matched_order = order
            break

    if matched_order is not None:
        return matched_order

    return 11


def get_year_pillar(dt: Union[datetime, date]) -> Pillar:
    d = dt.date() if isinstance(dt, datetime) else dt
    lichun = approximate_li_chun(d)

    year_for_ganzhi = d.year if d >= lichun else d.year - 1
    stem_idx = (year_for_ganzhi - 4) % 10
    branch_idx = (year_for_ganzhi - 4) % 12
    return make_pillar(stem_idx, branch_idx)


def get_month_pillar(dt: Union[datetime, date]) -> Pillar:
    d = dt.date() if isinstance(dt, datetime) else dt
    year_pillar = get_year_pillar(d)
    year_stem_idx = HEAVENLY_STEMS.index(year_pillar.stem)

    month_order = get_solar_month_order(d)

    # 寅月對應 branch idx = 2
    branch_idx = (month_order + 1) % 12

    # 甲己年丙作首, 乙庚年戊作首, 丙辛年庚作首, 丁壬年壬作首, 戊癸年甲作首
    first_month_stem_idx = ((year_stem_idx % 5) * 2 + 2) % 10
    stem_idx = (first_month_stem_idx + (month_order - 1)) % 10

    return make_pillar(stem_idx, branch_idx)


def get_day_pillar(dt: datetime, day_rollover_hour: int = 23) -> Pillar:
    effective_dt = dt
    if day_rollover_hour == 23 and dt.hour >= 23:
        effective_dt = dt + timedelta(days=1)

    effective_date = effective_dt.date()

    # 工程基準點原本會整體慢 2 天，這裡補上固定偏移量校正
    ref_date = date(1984, 2, 2)
    diff_days = (effective_date - ref_date).days + DAY_PILLAR_OFFSET
    cyc_idx = diff_days % 60

    stem, branch = cyclical_index_to_ganzhi(cyc_idx)
    return Pillar(stem=stem, branch=branch)


def get_hour_pillar(dt: datetime, day_stem: str) -> Pillar:
    hour = dt.hour

    # 子時 23:00-00:59
    branch_idx = ((hour + 1) // 2) % 12

    # 甲己日甲子時, 乙庚日丙子時, 丙辛日戊子時, 丁壬日庚子時, 戊癸日壬子時
    day_stem_idx = HEAVENLY_STEMS.index(day_stem)
    zi_hour_stem_idx = (day_stem_idx % 5) * 2
    stem_idx = (zi_hour_stem_idx + branch_idx) % 10

    return make_pillar(stem_idx, branch_idx)


def get_bazi_chart(birth_dt: datetime, day_rollover_hour: int = 23) -> BaZiChart:
    year_pillar = get_year_pillar(birth_dt)
    month_pillar = get_month_pillar(birth_dt)
    day_pillar = get_day_pillar(birth_dt, day_rollover_hour=day_rollover_hour)
    hour_pillar = get_hour_pillar(birth_dt, day_stem=day_pillar.stem)

    return BaZiChart(
        birth_datetime=birth_dt,
        year_pillar=year_pillar,
        month_pillar=month_pillar,
        day_pillar=day_pillar,
        hour_pillar=hour_pillar,
        day_master=day_pillar.stem,
    )


def parse_birth_datetime(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError:
        raise argparse.ArgumentTypeError(
            "birth datetime format must be YYYY-MM-DD HH:MM"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate a BaZi chart from a birth datetime."
    )
    parser.add_argument(
        "--birth-datetime",
        type=parse_birth_datetime,
        default=datetime(1996, 4, 27, 17, 30),
        help="Birth datetime in format 'YYYY-MM-DD HH:MM' (default: 1996-04-27 17:30)",
    )
    parser.add_argument(
        "--day-rollover-hour",
        type=int,
        default=23,
        help="Hour used as day rollover for day pillar calculation (default: 23).",
    )
    return parser


def format_pillar(label: str, pillar: Pillar) -> str:
    hidden = "、".join(pillar.hidden_stems)
    return (
        f"{label}\n"
        f"  柱: {pillar.name}\n"
        f"  天干: {pillar.stem} ({pillar.stem_element})\n"
        f"  地支: {pillar.branch} ({pillar.branch_element})\n"
        f"  藏干: {hidden}"
    )


def format_bazi_chart(chart: BaZiChart, day_rollover_hour: int) -> str:
    sections = [
        "=== BaZi Chart ===",
        f"出生時間: {chart.birth_datetime.strftime('%Y-%m-%d %H:%M')}",
        f"換日設定: {day_rollover_hour}:00",
        f"日主: {chart.day_master} ({STEM_TO_ELEMENT[chart.day_master]})",
        "",
        format_pillar("年柱", chart.year_pillar),
        "",
        format_pillar("月柱", chart.month_pillar),
        "",
        format_pillar("日柱", chart.day_pillar),
        "",
        format_pillar("時柱", chart.hour_pillar),
    ]
    return "\n".join(sections)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    chart = get_bazi_chart(
        args.birth_datetime,
        day_rollover_hour=args.day_rollover_hour,
    )
    print(format_bazi_chart(chart, args.day_rollover_hour))


if __name__ == "__main__":
    main()
