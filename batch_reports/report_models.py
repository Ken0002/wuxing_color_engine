from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Sequence


@dataclass(frozen=True)
class BatchConfig:
    name: str
    birth_datetime: datetime
    start_date: date
    end_date: date
    output_pdf: Path
    report_title: str
    report_subtitle: str

    @property
    def total_days(self) -> int:
        return (self.end_date - self.start_date).days + 1


@dataclass(frozen=True)
class RankingRow:
    rank: int
    element: str
    score: int
    level: str
    palette: str


@dataclass(frozen=True)
class OutfitStrategy:
    conservative: str
    safe_combo: str
    accessory: str


@dataclass(frozen=True)
class CoverPageData:
    title: str
    subtitle: str
    name: str
    birth_text: str
    bazi_text: str
    fav_text: str
    unfav_text: str
    date_range_text: str
    total_days_text: str
    notes: Sequence[str]


@dataclass(frozen=True)
class DailyReport:
    target_date: date
    weekday: str
    pillars_text: str
    wuxing_summary: str
    ranking_rows: Sequence[RankingRow]
    primary_element: str
    support_elements: Sequence[str]
    avoid_element: str
    accessory_element: Optional[str]
    outfit_strategy: OutfitStrategy
    daily_insight: Optional[str]
    console_text: str
