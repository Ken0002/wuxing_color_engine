from __future__ import annotations

from pathlib import Path
from typing import Optional


BATCH_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BATCH_DIR.parent
OUTPUT_DIR = BATCH_DIR / "output"


def mm_to_pt(value: float) -> float:
    return value * 72.0 / 25.4


MARGIN_TOP = mm_to_pt(18)
MARGIN_BOTTOM = mm_to_pt(18)
MARGIN_LEFT = mm_to_pt(16)
MARGIN_RIGHT = mm_to_pt(16)

COLOR_WHITE = "#FFFFFF"
COLOR_TEXT_PRIMARY = "#222222"
COLOR_TEXT_SECONDARY = "#666666"
COLOR_BORDER = "#DDDDDD"
COLOR_TITLE = "#2F3A4A"
COLOR_SURFACE = "#FAFBFC"
COLOR_TABLE_HEADER = "#EEF2F5"
COLOR_BADGE_TEXT = "#3A4553"

CONTENT_TEMPLATE_PATH = BATCH_DIR / "templates" / "explanation_templates.json"

ELEMENT_STYLES = {
    "金": {"accent": "#FFD700", "palette": "白、銀、金", "label": "金色系"},
    "木": {"accent": "#7FB77E", "palette": "淺綠、深綠", "label": "木色系"},
    "水": {"accent": "#4A90E2", "palette": "淺藍、深藍、黑", "label": "水色系"},
    "火": {"accent": "#D95C5C", "palette": "紅、紫、粉", "label": "火色系"},
    "土": {"accent": "#B58B57", "palette": "黃、灰、咖啡", "label": "土色系"},
}

WEEKDAY_LABELS = [
    "星期一",
    "星期二",
    "星期三",
    "星期四",
    "星期五",
    "星期六",
    "星期日",
]

PDF_FONT_CANDIDATES = [
    "MHei-Medium",
    "HeiseiKakuGo-W5",
    "HYGothic-Medium",
]


def lighten_hex(color_hex: str, ratio: float) -> str:
    text = color_hex.lstrip("#")
    red = int(text[0:2], 16)
    green = int(text[2:4], 16)
    blue = int(text[4:6], 16)
    new_red = int(red * (1.0 - ratio) + 255 * ratio)
    new_green = int(green * (1.0 - ratio) + 255 * ratio)
    new_blue = int(blue * (1.0 - ratio) + 255 * ratio)
    return "#%02X%02X%02X" % (new_red, new_green, new_blue)


def element_label(element: str) -> str:
    return ELEMENT_STYLES[element]["label"]


def optional_element_label(element: Optional[str]) -> str:
    return element_label(element) if element else "無"


def element_palette(element: str) -> str:
    return ELEMENT_STYLES[element]["palette"]


def element_accent(element: str) -> str:
    return ELEMENT_STYLES[element]["accent"]


def element_color_family(element: str) -> str:
    return "%s色系" % element


def element_color_short(element: str) -> str:
    return "%s色" % element
