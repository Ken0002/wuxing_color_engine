from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence

from batch_reports.report_models import (
    BatchConfig,
    CoverPageData,
    DailyReport,
    OutfitStrategy,
    RankingRow,
)
from batch_reports.report_styles import (
    CONTENT_TEMPLATE_PATH,
    OUTPUT_DIR,
    PROJECT_ROOT,
    WEEKDAY_LABELS,
    element_color_family,
    element_color_short,
    element_label,
    element_palette,
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bazi_calculator import BaZiChart, get_bazi_chart, parse_birth_datetime
from core_scoring import CoreScoreResult, calculate_core_scores, infer_preference_profile
from date_energy_calculator import get_date_energy, parse_target_date


DEFAULT_CONTENT_TEMPLATES = {
    "outfit_strategy": {
        "conservative": "保守穿法：{main_color}單穿",
        "safe_combo": "安全搭配：{combo}",
        "accessory": "配件方向：{accessory_color}作小面積點綴",
        "accessory_none": "配件方向：配件可延續主色",
    },
    "daily_insight": {
        "close_top2": "今日主色選擇彈性高，{top1}、{top2}皆可優先搭配。",
        "dominant_top1": "今日主色集中，建議整體穿搭以單一主色為主。",
        "very_low_last": "低分色不建議大面積使用，請避免作為主色。",
        "balanced": "今日各色差距不大，搭配自由度較高。",
        "accessory_differs": "今日配件可另選色系，不必和主色綁在一起。",
    },
}


class ConfigError(ValueError):
    """Raised when the batch config is missing required fields or has bad values."""


def require_string(raw_config: Dict, field_name: str) -> str:
    value = raw_config.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("config field '%s' must be a non-empty string" % field_name)
    return value.strip()


def get_string(raw_config: Dict, field_name: str, default: str) -> str:
    value = raw_config.get(field_name, default)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("config field '%s' must be a non-empty string" % field_name)
    return value.strip()


def load_config(config_path) -> BatchConfig:
    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigError("config file not found: %s" % config_path) from exc

    try:
        raw_config = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ConfigError("config file is not valid JSON: %s" % exc) from exc

    if not isinstance(raw_config, dict):
        raise ConfigError("config root must be a JSON object")

    try:
        birth_datetime = parse_birth_datetime(
            require_string(raw_config, "birth_datetime")
        )
        start_date = parse_target_date(require_string(raw_config, "start_date"))
        end_date = parse_target_date(require_string(raw_config, "end_date"))
    except argparse.ArgumentTypeError as exc:
        raise ConfigError(str(exc)) from exc

    if start_date > end_date:
        raise ConfigError("start_date cannot be later than end_date")

    output_name = get_string(
        raw_config,
        "output_pdf",
        "wuxing_date_range_report.pdf",
    )
    if any(char in output_name for char in ('/', '\\', ':', '\x00')) or output_name in ('.', '..'):
        raise ConfigError("config field 'output_pdf' must be a filename, not a path")
    if not output_name.lower().endswith('.pdf'):
        raise ConfigError("config field 'output_pdf' must end with .pdf")
    resolved_output = OUTPUT_DIR / output_name

    return BatchConfig(
        name=get_string(raw_config, "name", "使用者"),
        birth_datetime=birth_datetime,
        start_date=start_date,
        end_date=end_date,
        output_pdf=resolved_output,
        report_title=get_string(raw_config, "report_title", "每日五行能量建議書"),
        report_subtitle=get_string(raw_config, "report_subtitle", "個人化日期範圍報表"),
    )


def iter_dates(start_date: date, end_date: date) -> Iterable[date]:
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def format_birth_text(birth_datetime: datetime) -> str:
    return birth_datetime.strftime("%Y-%m-%d %H:%M")


def format_bazi_text(chart: BaZiChart) -> str:
    return (
        "%s年 %s月 %s日 %s時"
        % (
            chart.year_pillar.name,
            chart.month_pillar.name,
            chart.day_pillar.name,
            chart.hour_pillar.name,
        )
    )


def format_element_list(elements: Sequence[str]) -> str:
    return "、".join(elements) if elements else "無"


def format_date_range_text(config: BatchConfig) -> str:
    return "%s 至 %s（共 %s 天）" % (
        config.start_date.isoformat(),
        config.end_date.isoformat(),
        config.total_days,
    )


def get_weekday_label(target_date: date) -> str:
    return WEEKDAY_LABELS[target_date.weekday()]


def get_level_label(score: int) -> str:
    if score >= 85:
        return "強推"
    if score >= 70:
        return "可用"
    if score >= 50:
        return "普通"
    if score >= 30:
        return "偏弱"
    return "避免"


@lru_cache(maxsize=1)
def load_content_templates() -> Dict:
    try:
        raw = json.loads(CONTENT_TEMPLATE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return dict(DEFAULT_CONTENT_TEMPLATES)
    except json.JSONDecodeError:
        return dict(DEFAULT_CONTENT_TEMPLATES)

    if not isinstance(raw, dict):
        return dict(DEFAULT_CONTENT_TEMPLATES)

    templates = json.loads(json.dumps(DEFAULT_CONTENT_TEMPLATES))
    for section_name in ("outfit_strategy", "daily_insight"):
        section_value = raw.get(section_name)
        if not isinstance(section_value, dict):
            continue
        for key, default_value in templates[section_name].items():
            candidate = section_value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                templates[section_name][key] = candidate.strip()
            else:
                templates[section_name][key] = default_value
    return templates


def build_cover_page_data(config: BatchConfig, chart: BaZiChart) -> CoverPageData:
    profile = infer_preference_profile(chart)
    return CoverPageData(
        title=config.report_title,
        subtitle=config.report_subtitle,
        name=config.name,
        birth_text=format_birth_text(config.birth_datetime),
        bazi_text=format_bazi_text(chart),
        fav_text=format_element_list(profile.fav_elements),
        unfav_text=format_element_list(profile.unfav_elements),
        date_range_text=format_date_range_text(config),
        total_days_text="%s 天" % config.total_days,
        notes=(
            "後續每一頁代表一天。",
            "每頁會顯示五行排行、分數與顏色建議。",
            "分數越高，越適合作為當日主色或優先選擇。",
        ),
    )


def build_ranking_rows(core_scores: CoreScoreResult) -> List[RankingRow]:
    rows = []
    for rank, element in enumerate(core_scores.ranking, start=1):
        rows.append(
            RankingRow(
                rank=rank,
                element=element,
                score=core_scores.scores[element],
                level=get_level_label(core_scores.scores[element]),
                palette=element_palette(element),
            )
        )
    return rows


def choose_accessory_element(ranking_rows: Sequence[RankingRow]) -> Optional[str]:
    candidate = ranking_rows[3]
    if candidate.score >= 50:
        return candidate.element
    return None


def build_outfit_strategy(
    primary_element: str,
    support_elements: Sequence[str],
    accessory_element: Optional[str],
    templates: Dict,
) -> OutfitStrategy:
    strategy_template = templates["outfit_strategy"]
    conservative = strategy_template["conservative"].format(
        main_color=element_color_family(primary_element)
    )
    safe_combo = strategy_template["safe_combo"].format(
        combo="%s搭%s"
        % (
            element_color_short(primary_element),
            element_color_short(support_elements[0]),
        )
    )
    if accessory_element:
        accessory = strategy_template["accessory"].format(
            accessory_color=element_color_short(accessory_element)
        )
    else:
        accessory = strategy_template["accessory_none"]
    return OutfitStrategy(
        conservative=conservative,
        safe_combo=safe_combo,
        accessory=accessory,
    )


def build_daily_insight(
    ranking_rows: Sequence[RankingRow],
    primary_element: str,
    accessory_element: Optional[str],
    templates: Dict,
) -> Optional[str]:
    insight_template = templates["daily_insight"]
    top1 = ranking_rows[0]
    top2 = ranking_rows[1]
    last = ranking_rows[-1]
    top_gap = top1.score - top2.score
    total_gap = top1.score - last.score

    if top_gap <= 5:
        return insight_template["close_top2"].format(top1=top1.element, top2=top2.element)
    if top_gap >= 15:
        return insight_template["dominant_top1"]
    if last.score <= 20:
        return insight_template["very_low_last"]
    if total_gap <= 20:
        return insight_template["balanced"]
    if accessory_element and accessory_element != primary_element:
        return insight_template["accessory_differs"]
    return None


def build_console_text(
    target_date: date,
    weekday: str,
    pillars_text: str,
    wuxing_summary: str,
    ranking_rows: Sequence[RankingRow],
    primary_element: str,
    support_elements: Sequence[str],
    avoid_element: str,
    accessory_element: Optional[str],
    daily_insight: Optional[str],
) -> str:
    ranking_text = " / ".join(
        "%s.%s%s(%s)" % (row.rank, row.element, row.score, row.level)
        for row in ranking_rows
    )
    lines = [
        "=== %s %s ===" % (target_date.isoformat(), weekday),
        pillars_text,
        wuxing_summary,
        (
            "主色: %s | 輔助: %s | 避免: %s | 配件: %s"
            % (
                element_label(primary_element),
                ", ".join(element_label(item) for item in support_elements),
                element_label(avoid_element),
                element_label(accessory_element) if accessory_element else "無",
            )
        ),
        "排行: %s" % ranking_text,
    ]
    if daily_insight:
        lines.append("重點: %s" % daily_insight)
    return "\n".join(lines)


def build_daily_report(
    birth_datetime: datetime,
    chart: BaZiChart,
    target_date: date,
) -> DailyReport:
    templates = load_content_templates()
    energy = get_date_energy(target_date)
    core_scores = calculate_core_scores(
        birth_datetime.strftime("%Y-%m-%d %H:%M"),
        chart,
        energy,
    )

    ranking_rows = build_ranking_rows(core_scores)
    primary_element = ranking_rows[0].element
    support_elements = (ranking_rows[1].element, ranking_rows[2].element)
    avoid_element = ranking_rows[-1].element
    accessory_element = choose_accessory_element(ranking_rows)

    weekday = get_weekday_label(target_date)
    pillars_text = "%s年 %s月 %s日" % (
        energy.year_pillar.name,
        energy.month_pillar.name,
        energy.day_pillar.name,
    )
    wuxing_summary = "%s年 / %s月 / %s日" % (
        energy.year_element,
        energy.month_element,
        energy.day_element,
    )

    outfit_strategy = build_outfit_strategy(
        primary_element,
        support_elements,
        accessory_element,
        templates,
    )
    daily_insight = build_daily_insight(
        ranking_rows,
        primary_element,
        accessory_element,
        templates,
    )

    return DailyReport(
        target_date=target_date,
        weekday=weekday,
        pillars_text=pillars_text,
        wuxing_summary=wuxing_summary,
        ranking_rows=ranking_rows,
        primary_element=primary_element,
        support_elements=support_elements,
        avoid_element=avoid_element,
        accessory_element=accessory_element,
        outfit_strategy=outfit_strategy,
        daily_insight=daily_insight,
        console_text=build_console_text(
            target_date,
            weekday,
            pillars_text,
            wuxing_summary,
            ranking_rows,
            primary_element,
            support_elements,
            avoid_element,
            accessory_element,
            daily_insight,
        ),
    )


__all__ = [
    "BatchConfig",
    "ConfigError",
    "build_cover_page_data",
    "build_daily_report",
    "get_bazi_chart",
    "iter_dates",
    "load_config",
]
