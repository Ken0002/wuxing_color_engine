#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

from bazi_calculator import get_bazi_chart
from core_scoring import calculate_core_scores
from core_scoring_v2 import calculate_core_scores_v2
from date_energy_calculator import FIVE_ELEMENTS, get_date_energy


DATASET_PATH = Path(__file__).resolve().parent / "data" / "dataset.csv"


@dataclass
class ModelStats:
    score_hits: int = 0
    rank_hits: int = 0
    total_rows: int = 0
    total_abs_error: int = 0

    @property
    def mean_abs_error(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return self.total_abs_error / (self.total_rows * len(FIVE_ELEMENTS))


def expected_scores(row: Dict[str, str]) -> Dict[str, int]:
    return {
        "木": int(row["score_wood"]),
        "火": int(row["score_fire"]),
        "土": int(row["score_earth"]),
        "金": int(row["score_metal"]),
        "水": int(row["score_water"]),
    }


def expected_ranking(row: Dict[str, str]) -> Tuple[str, ...]:
    return tuple(row[f"rank_{index}"] for index in range(1, 6))


def accumulate(
    stats: ModelStats,
    predicted_scores: Dict[str, int],
    predicted_ranking: Tuple[str, ...],
    row: Dict[str, str],
) -> None:
    target_scores = expected_scores(row)
    target_ranking = expected_ranking(row)

    stats.total_rows += 1
    stats.total_abs_error += sum(
        abs(predicted_scores[element] - target_scores[element])
        for element in FIVE_ELEMENTS
    )

    if predicted_scores == target_scores:
        stats.score_hits += 1
    if predicted_ranking == target_ranking:
        stats.rank_hits += 1


def format_stats(label: str, stats: ModelStats) -> str:
    return "\n".join(
        [
            f"[{label}]",
            f"score exact hits: {stats.score_hits}/{stats.total_rows}",
            f"rank exact hits: {stats.rank_hits}/{stats.total_rows}",
            f"mean abs error: {stats.mean_abs_error:.3f}",
        ]
    )


def main() -> None:
    rows = list(csv.DictReader(DATASET_PATH.open(encoding="utf-8-sig")))

    v1_stats = ModelStats()
    v2_stats = ModelStats()

    for row in rows:
        birth_dt = datetime.strptime(row["birth_datetime"], "%Y-%m-%d %H:%M")
        target_date = datetime.strptime(row["date"], "%Y-%m-%d").date()

        chart = get_bazi_chart(birth_dt)
        energy = get_date_energy(target_date)

        v1_result = calculate_core_scores(row["birth_datetime"], chart, energy)
        v2_result = calculate_core_scores_v2(row["birth_datetime"], chart, energy)

        accumulate(v1_stats, v1_result.scores, v1_result.ranking, row)
        accumulate(v2_stats, v2_result.scores, v2_result.ranking, row)

    print(format_stats("v1", v1_stats))
    print()
    print(format_stats("v2", v2_stats))


if __name__ == "__main__":
    main()
