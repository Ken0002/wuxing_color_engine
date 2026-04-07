#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, Mapping, Optional, Tuple

from bazi_calculator import BaZiChart, STEM_TO_ELEMENT
from date_energy_calculator import DateEnergy, FIVE_ELEMENTS, GENERATES


CONTROLS = {
    "木": "土",
    "火": "金",
    "土": "水",
    "金": "木",
    "水": "火",
}

GENERATED_BY = {child: parent for parent, child in GENERATES.items()}
CONTROLLED_BY = {target: controller for controller, target in CONTROLS.items()}

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

ELEMENT_INDEX = {element: index for index, element in enumerate(FIVE_ELEMENTS)}

# 這組係數是用現有標註資料離線校準後固定在程式內，
# runtime 只需要 birth_datetime 與 target_date 兩個輸入，不再讀 dataset.csv。
DATE_BASE_INTERCEPT = {
    "木": 26.667,
    "火": 87.733,
    "土": 90.533,
    "金": 89.600,
    "水": 26.633,
}

MONTH_ELEMENT_EFFECTS = {
    "木": {"木": 16.800, "火": -16.600, "土": -17.400, "金": -14.000, "水": 31.400},
    "火": {"木": 30.400, "火": -32.000, "土": -33.400, "金": 1.600, "水": 33.600},
    "土": {"木": 33.200, "火": -1.200, "土": -33.400, "金": -30.400, "水": 32.000},
    "金": {"木": 31.600, "火": 1.400, "土": -2.600, "金": -30.400, "水": 0.000},
    "水": {"木": 0.000, "火": 0.000, "土": 0.000, "金": 0.000, "水": 0.000},
}

DAY_ELEMENT_EFFECTS = {
    "木": {"木": 0.000, "火": -33.833, "土": -1.333, "金": 3.000, "水": 32.667},
    "火": {"木": 32.500, "火": -33.833, "土": -35.167, "金": 1.667, "水": 35.667},
    "土": {"木": 35.333, "火": -1.500, "土": -35.167, "金": -32.333, "水": 34.000},
    "金": {"木": 33.833, "火": 1.500, "土": -3.000, "金": -32.333, "水": 0.000},
    "水": {"木": 0.000, "火": 0.000, "土": 0.000, "金": 0.000, "水": 0.000},
}

TRANSFORM_RELATION_EFFECTS = {
    "same": -15.4,
    "parent": 0.0,
    "child": -1.6,
    "control_out": 0.6,
    "control_in": 16.0,
    "none": 0.0,
}

FAVORED_BONUS = 2.0
UNFAVORED_PENALTY = 22.5

ProfileKey = Tuple[Tuple[str, ...], Tuple[str, ...]]
DateSignature = Tuple[str, str, Optional[str]]


@dataclass(frozen=True)
class PreferenceProfile:
    fav_elements: Tuple[str, ...]
    unfav_elements: Tuple[str, ...]
    day_master_element: str
    strength_label: str
    support_score: float
    balancing_score: float
    source: str

    @property
    def key(self) -> ProfileKey:
        return self.fav_elements, self.unfav_elements


@dataclass(frozen=True)
class CoreScoreResult:
    scores: Dict[str, int]
    ranking: Tuple[str, ...]
    profile: PreferenceProfile
    date_signature: DateSignature
    scoring_mode: str


def normalize_elements(elements: Iterable[str]) -> Tuple[str, ...]:
    unique = []
    seen = set()
    for element in elements:
        item = element.strip()
        if not item or item not in ELEMENT_INDEX or item in seen:
            continue
        unique.append(item)
        seen.add(item)
    return tuple(sorted(unique, key=lambda item: ELEMENT_INDEX[item]))


def extract_transform_target(note: str) -> Optional[str]:
    if not note or note == "無":
        return None

    start = note.find("以")
    end = note.find("算")
    if start == -1 or end == -1 or end <= start + 1:
        return None
    return note[start + 1 : end]


def make_date_signature(energy: DateEnergy) -> DateSignature:
    return (
        energy.month_element,
        energy.day_element,
        extract_transform_target(energy.month_element_note),
    )


def format_profile_label(profile_key: ProfileKey) -> str:
    fav_elements, unfav_elements = profile_key
    fav_text = "、".join(fav_elements) if fav_elements else "無"
    unfav_text = "、".join(unfav_elements) if unfav_elements else "無"
    return f"喜:{fav_text} / 忌:{unfav_text}"


def round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def clamp_score(value: float) -> int:
    return max(0, min(100, round_half_up(value)))


def rank_elements(scores: Mapping[str, int]) -> Tuple[str, ...]:
    return tuple(
        sorted(
            FIVE_ELEMENTS,
            key=lambda element: (-scores[element], ELEMENT_INDEX[element]),
        )
    )


def get_output_element(day_master_element: str) -> str:
    return GENERATES[day_master_element]


def get_wealth_element(day_master_element: str) -> str:
    return CONTROLS[day_master_element]


def get_officer_element(day_master_element: str) -> str:
    return CONTROLLED_BY[day_master_element]


def get_resource_element(day_master_element: str) -> str:
    return GENERATED_BY[day_master_element]


def get_element_relation(target_element: str, source_element: Optional[str]) -> str:
    if source_element is None:
        return "none"
    if target_element == source_element:
        return "same"
    if GENERATED_BY[target_element] == source_element:
        return "parent"
    if GENERATES[target_element] == source_element:
        return "child"
    if CONTROLS[target_element] == source_element:
        return "control_out"
    return "control_in"


def count_birth_elements(chart: BaZiChart) -> Dict[str, float]:
    counter = {element: 0.0 for element in FIVE_ELEMENTS}

    for pillar in (
        chart.year_pillar,
        chart.month_pillar,
        chart.day_pillar,
        chart.hour_pillar,
    ):
        counter[pillar.stem_element] += 1.0
        counter[pillar.branch_element] += 1.0

        hidden_weight = 1.0 / len(pillar.hidden_stems)
        for hidden_stem in pillar.hidden_stems:
            counter[STEM_TO_ELEMENT[hidden_stem]] += hidden_weight

    return counter


def infer_preference_profile(chart: BaZiChart) -> PreferenceProfile:
    day_master_element = STEM_TO_ELEMENT[chart.day_master]
    resource_element = get_resource_element(day_master_element)
    output_element = get_output_element(day_master_element)
    wealth_element = get_wealth_element(day_master_element)
    officer_element = get_officer_element(day_master_element)

    counts = count_birth_elements(chart)
    support_score = counts[day_master_element] + counts[resource_element]
    balancing_score = (
        counts[output_element] + counts[wealth_element] + counts[officer_element]
    )

    seasonal_element = BRANCH_TO_SEASONAL_ELEMENT[chart.month_pillar.branch]
    if seasonal_element in (day_master_element, resource_element):
        support_score += 2.0
    elif seasonal_element in (output_element, wealth_element, officer_element):
        balancing_score += 1.0

    strength_gap = support_score - balancing_score

    if strength_gap >= 1.8:
        fav_elements = normalize_elements(
            [output_element, wealth_element, officer_element]
        )
        unfav_elements = normalize_elements([resource_element, day_master_element])
        strength_label = "偏強"
    elif strength_gap >= 1.0:
        fav_elements = normalize_elements(
            [output_element, wealth_element, officer_element]
        )
        unfav_elements = normalize_elements([resource_element])
        strength_label = "身強"
    elif strength_gap <= -1.8:
        fav_elements = normalize_elements([day_master_element, resource_element])
        unfav_elements = normalize_elements(
            [output_element, wealth_element, officer_element]
        )
        strength_label = "偏弱"
    elif strength_gap <= -1.0:
        fav_elements = normalize_elements([day_master_element, resource_element])
        unfav_elements = normalize_elements([wealth_element, officer_element])
        strength_label = "身弱"
    else:
        if strength_gap >= 0:
            fav_elements = normalize_elements([output_element, wealth_element])
            unfav_elements = normalize_elements([resource_element])
            strength_label = "中和偏強"
        else:
            fav_elements = normalize_elements([day_master_element, resource_element])
            unfav_elements = normalize_elements([officer_element])
            strength_label = "中和偏弱"

    return PreferenceProfile(
        fav_elements=fav_elements,
        unfav_elements=unfav_elements,
        day_master_element=day_master_element,
        strength_label=strength_label,
        support_score=support_score,
        balancing_score=balancing_score,
        source="birth_only_inference",
    )


def build_date_base_scores(energy: DateEnergy) -> Dict[str, float]:
    transform_target = extract_transform_target(energy.month_element_note)
    scores: Dict[str, float] = {}

    for element in FIVE_ELEMENTS:
        relation = get_element_relation(element, transform_target)
        scores[element] = (
            DATE_BASE_INTERCEPT[element]
            + MONTH_ELEMENT_EFFECTS[energy.month_element][element]
            + DAY_ELEMENT_EFFECTS[energy.day_element][element]
            + TRANSFORM_RELATION_EFFECTS[relation]
        )

    return scores


def apply_profile_adjustment(
    base_scores: Mapping[str, float],
    profile: PreferenceProfile,
) -> Dict[str, int]:
    scores = {}

    for element in FIVE_ELEMENTS:
        score = base_scores[element]
        if element in profile.fav_elements:
            score += FAVORED_BONUS
        elif element in profile.unfav_elements:
            score -= UNFAVORED_PENALTY
        scores[element] = clamp_score(score)

    return scores


def calculate_core_scores(
    birth_dt_text: str,
    chart: BaZiChart,
    energy: DateEnergy,
) -> CoreScoreResult:
    del birth_dt_text

    profile = infer_preference_profile(chart)
    date_signature = make_date_signature(energy)
    base_scores = build_date_base_scores(energy)
    scores = apply_profile_adjustment(base_scores, profile)

    return CoreScoreResult(
        scores=scores,
        ranking=rank_elements(scores),
        profile=profile,
        date_signature=date_signature,
        scoring_mode="birth_and_date_only",
    )


def describe_scoring_mode(result: CoreScoreResult) -> str:
    del result
    return "純輸入推導"


def format_core_score_result(result: CoreScoreResult) -> str:
    transform_target = result.date_signature[2] or "無"
    score_line = " / ".join(
        f"{element} {result.scores[element]}" for element in FIVE_ELEMENTS
    )
    ranking_line = " > ".join(result.ranking)
    profile_label = format_profile_label(result.profile.key)

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
            f"五行分數: {score_line}",
            f"排名: {ranking_line}",
        ]
    )
