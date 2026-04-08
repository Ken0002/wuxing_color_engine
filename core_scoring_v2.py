#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from bazi_calculator import BRANCH_TO_ELEMENT, BaZiChart, HIDDEN_STEMS, STEM_TO_ELEMENT
from core_scoring import (
    PreferenceProfile,
    apply_profile_adjustment,
    build_date_base_scores,
    extract_transform_target,
    format_profile_label,
    infer_preference_profile,
    make_date_signature,
    rank_elements,
)
from date_energy_calculator import DateEnergy, FIVE_ELEMENTS, GENERATES, LIUHE_RESULT


CONTROLS = {
    "木": "土",
    "火": "金",
    "土": "水",
    "金": "木",
    "水": "火",
}

GENERATED_BY = {child: parent for parent, child in GENERATES.items()}

BRANCH_TO_SEASONAL_ELEMENT = {
    "寅": "木",
    "卯": "木",
    "辰": "木",
    "巳": "火",
    "午": "火",
    "未": "火",
    "申": "金",
    "酉": "金",
    "戌": "金",
    "亥": "水",
    "子": "水",
    "丑": "水",
}

CLASHES = {
    frozenset(("子", "午")),
    frozenset(("丑", "未")),
    frozenset(("寅", "申")),
    frozenset(("卯", "酉")),
    frozenset(("辰", "戌")),
    frozenset(("巳", "亥")),
}

ELEMENT_INDEX = {element: index for index, element in enumerate(FIVE_ELEMENTS)}


@dataclass(frozen=True)
class V2CoreScoreResult:
    scores: Dict[str, int]
    ranking: Tuple[str, ...]
    profile: PreferenceProfile
    date_signature: Tuple[str, str, Optional[str]]
    scoring_mode: str
    baseline_scores: Dict[str, int]
    structural_adjustments: Dict[str, float]


def relation(target_element: str, source_element: str) -> str:
    if target_element == source_element:
        return "same"
    if GENERATED_BY[target_element] == source_element:
        return "parent"
    if GENERATES[target_element] == source_element:
        return "child"
    if CONTROLS[target_element] == source_element:
        return "control_out"
    return "control_in"


def hidden_weights(branch: str) -> Tuple[float, ...]:
    hidden = HIDDEN_STEMS[branch]
    if len(hidden) == 1:
        return (1.0,)
    if len(hidden) == 2:
        return (0.7, 0.3)
    return (0.7, 0.2, 0.1)


def season_multiplier(target_element: str, seasonal_element: str) -> float:
    return {
        "same": 1.06,
        "child": 1.02,
        "parent": 0.995,
        "control_out": 0.98,
        "control_in": 0.95,
    }[relation(target_element, seasonal_element)]


def build_structural_adjustments(
    chart: BaZiChart,
    energy: DateEnergy,
) -> Dict[str, float]:
    counts = {element: 0.0 for element in FIVE_ELEMENTS}

    specs = [
        (energy.year_pillar, 0.25, 0.35, 0.10),
        (energy.month_pillar, 0.40, 0.60, 0.16),
        (energy.day_pillar, 0.35, 0.50, 0.14),
    ]

    for pillar, stem_weight, branch_weight, hidden_weight in specs:
        counts[pillar.stem_element] += stem_weight
        counts[pillar.branch_element] += branch_weight

        for hidden_stem, fraction in zip(
            pillar.hidden_stems,
            hidden_weights(pillar.branch),
        ):
            counts[STEM_TO_ELEMENT[hidden_stem]] += hidden_weight * fraction

    seasonal_element = BRANCH_TO_SEASONAL_ELEMENT[energy.month_pillar.branch]
    for element in FIVE_ELEMENTS:
        counts[element] *= season_multiplier(element, seasonal_element)

    transform_target = extract_transform_target(energy.month_element_note)
    if transform_target in counts:
        counts[transform_target] += 0.20

    natal_branches = [
        chart.year_pillar.branch,
        chart.month_pillar.branch,
        chart.day_pillar.branch,
        chart.hour_pillar.branch,
    ]
    date_branches = [
        energy.year_pillar.branch,
        energy.month_pillar.branch,
        energy.day_pillar.branch,
    ]

    for natal_branch in natal_branches:
        for date_branch in date_branches:
            pair = frozenset((natal_branch, date_branch))
            if pair in LIUHE_RESULT:
                counts[LIUHE_RESULT[pair]] += 0.03
            if pair in CLASHES:
                counts[BRANCH_TO_ELEMENT[date_branch]] -= 0.02

    average = sum(counts.values()) / len(FIVE_ELEMENTS)
    adjustments = {}

    for element in FIVE_ELEMENTS:
        deficiency = average - counts[element]
        control_bonus = max(counts[CONTROLS[element]] - average, 0.0)
        feed_penalty = max(counts[GENERATES[element]] - average, 0.0)

        adjustments[element] = (
            deficiency * 0.10
            + control_bonus * 0.04
            - feed_penalty * 0.03
        )

    mean_adjustment = sum(adjustments.values()) / len(FIVE_ELEMENTS)
    for element in FIVE_ELEMENTS:
        centered = adjustments[element] - mean_adjustment
        adjustments[element] = max(-0.12, min(0.12, centered))

    return adjustments


def calculate_core_scores_v2(
    birth_dt_text: str,
    chart: BaZiChart,
    energy: DateEnergy,
) -> V2CoreScoreResult:
    del birth_dt_text

    profile = infer_preference_profile(chart)
    date_signature = make_date_signature(energy)

    baseline_base_scores = build_date_base_scores(energy)
    structural_adjustments = build_structural_adjustments(chart, energy)
    v2_base_scores = {
        element: baseline_base_scores[element] + structural_adjustments[element]
        for element in FIVE_ELEMENTS
    }

    baseline_scores = apply_profile_adjustment(baseline_base_scores, profile)
    scores = apply_profile_adjustment(v2_base_scores, profile)

    return V2CoreScoreResult(
        scores=scores,
        ranking=rank_elements(scores),
        profile=profile,
        date_signature=date_signature,
        scoring_mode="birth_and_date_with_structural_overlay",
        baseline_scores=baseline_scores,
        structural_adjustments=structural_adjustments,
    )


def describe_scoring_mode(result: V2CoreScoreResult) -> str:
    del result
    return "純輸入推導 + 結構修正"


def format_core_score_result_v2(result: V2CoreScoreResult) -> str:
    transform_target = result.date_signature[2] or "無"
    score_line = " / ".join(
        f"{element} {result.scores[element]}" for element in FIVE_ELEMENTS
    )
    ranking_line = " > ".join(result.ranking)
    profile_label = format_profile_label(result.profile.key)
    structural_line = " / ".join(
        f"{element} {result.structural_adjustments[element]:+.2f}"
        for element in FIVE_ELEMENTS
    )
    baseline_line = " / ".join(
        f"{element} {result.baseline_scores[element]}"
        for element in FIVE_ELEMENTS
    )

    return "\n".join(
        [
            (
                f"命主判定: {result.profile.strength_label} "
                f"(support={result.profile.support_score:.2f}, "
                f"balance={result.profile.balancing_score:.2f})"
            ),
            f"命主喜忌: {profile_label}",
            f"命主來源: {result.profile.source}",
            (
                f"日期 signature: 月={result.date_signature[0]} / "
                f"日={result.date_signature[1]} / 轉化={transform_target}"
            ),
            f"計分模式: {describe_scoring_mode(result)}",
            f"v1 基底分數: {baseline_line}",
            f"結構修正: {structural_line}",
            f"v2 五行分數: {score_line}",
            f"v2 排名: {ranking_line}",
        ]
    )
