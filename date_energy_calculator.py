#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, List

from bazi_calculator import (
    Pillar,
    STEM_TO_ELEMENT,
    get_year_pillar,
    get_month_pillar,
    get_day_pillar,
)


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

FIVE_ELEMENTS = ["木", "火", "土", "金", "水"]

GENERATES = {
    "木": "火",
    "火": "土",
    "土": "金",
    "金": "水",
    "水": "木",
}

LIUHE_RESULT = {
    frozenset(("子", "丑")): "土",
    frozenset(("寅", "亥")): "木",
    frozenset(("卯", "戌")): "火",
    frozenset(("辰", "酉")): "金",
    frozenset(("巳", "申")): "水",
    frozenset(("午", "未")): "火",
}

SANHE_GROUPS = [
    ({"申", "子", "辰"}, "水"),
    ({"亥", "卯", "未"}, "木"),
    ({"寅", "午", "戌"}, "火"),
    ({"巳", "酉", "丑"}, "金"),
]


@dataclass
class DateEnergy:
    target_date: date
    year_pillar: Pillar
    month_pillar: Pillar
    day_pillar: Pillar
    year_element: str
    month_element: str
    month_element_note: str
    day_element: str
    element_counts_simple: Dict[str, float]
    element_counts_hidden: Dict[str, float]

    def to_dict(self) -> Dict:
        return {
            "target_date": self.target_date.isoformat(),
            "year_pillar": self.year_pillar.to_dict(),
            "month_pillar": self.month_pillar.to_dict(),
            "day_pillar": self.day_pillar.to_dict(),
            "year_pillar_text": self.year_pillar.name,
            "month_pillar_text": self.month_pillar.name,
            "day_pillar_text": self.day_pillar.name,
            "year_element": self.year_element,
            "month_element": self.month_element,
            "month_element_note": self.month_element_note,
            "day_element": self.day_element,
            "element_counts_simple": self.element_counts_simple,
            "element_counts_hidden": self.element_counts_hidden,
        }


def init_element_counter() -> Dict[str, float]:
    return {e: 0.0 for e in FIVE_ELEMENTS}


def count_elements_simple_from_pillars(pillars: List[Pillar]) -> Dict[str, float]:
    counter = init_element_counter()

    for pillar in pillars:
        counter[pillar.stem_element] += 1.0
        counter[pillar.branch_element] += 1.0

    return counter


def count_elements_with_hidden_stems(
    pillars: List[Pillar],
    hidden_weight_mode: str = "equal",
) -> Dict[str, float]:
    counter = init_element_counter()

    for pillar in pillars:
        counter[pillar.stem_element] += 1.0
        counter[pillar.branch_element] += 1.0

        hidden = HIDDEN_STEMS[pillar.branch]
        if hidden_weight_mode == "equal":
            weight = 1.0 / len(hidden)
            for hidden_stem in hidden:
                counter[STEM_TO_ELEMENT[hidden_stem]] += weight
        else:
            raise ValueError(f"Unsupported hidden_weight_mode: {hidden_weight_mode}")

    return counter


def infer_month_element_note(year_pillar: Pillar, month_pillar: Pillar) -> str:
    year_element = year_pillar.branch_element
    month_element = month_pillar.branch_element

    if GENERATES.get(month_element) == year_element:
        return f"(月生年以{year_element}算)"

    liuhe_result = LIUHE_RESULT.get(frozenset((year_pillar.branch, month_pillar.branch)))
    if liuhe_result == year_element:
        return f"(六合局以{liuhe_result}算)"

    for branches, result_element in SANHE_GROUPS:
        if (
            year_pillar.branch in branches
            and month_pillar.branch in branches
            and year_pillar.branch != month_pillar.branch
            and result_element == year_element
        ):
            return f"(三合局以{result_element}算)"

    return "無"


def get_date_energy(target_date: date) -> DateEnergy:
    noon_dt = datetime(target_date.year, target_date.month, target_date.day, 12, 0, 0)

    year_pillar = get_year_pillar(noon_dt)
    month_pillar = get_month_pillar(noon_dt)
    day_pillar = get_day_pillar(noon_dt, day_rollover_hour=23)

    pillars = [year_pillar, month_pillar, day_pillar]

    simple_counts = count_elements_simple_from_pillars(pillars)
    hidden_counts = count_elements_with_hidden_stems(pillars)

    return DateEnergy(
        target_date=target_date,
        year_pillar=year_pillar,
        month_pillar=month_pillar,
        day_pillar=day_pillar,
        year_element=year_pillar.branch_element,
        month_element=month_pillar.branch_element,
        month_element_note=infer_month_element_note(year_pillar, month_pillar),
        day_element=day_pillar.branch_element,
        element_counts_simple=simple_counts,
        element_counts_hidden=hidden_counts,
    )


def parse_target_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError("target date format must be YYYY-MM-DD") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate five-element energy for a target date."
    )
    parser.add_argument(
        "--target-date",
        type=parse_target_date,
        default=date(2026, 4, 2),
        help="Target date in format YYYY-MM-DD (default: 2026-04-02)",
    )
    return parser


def format_date_energy(energy: DateEnergy) -> str:
    note = "" if energy.month_element_note == "無" else energy.month_element_note
    return "\n".join(
        [
            energy.target_date.isoformat(),
            f"{energy.year_pillar.name}年{energy.month_pillar.name}月{energy.day_pillar.name}日",
            f"{energy.year_element}年{energy.month_element}月{note}{energy.day_element}日",
        ]
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    energy = get_date_energy(args.target_date)
    print(format_date_energy(energy))


if __name__ == "__main__":
    main()
