from __future__ import annotations

from typing import List, Sequence

from batch_reports.report_models import CoverPageData, DailyReport
from batch_reports.report_styles import (
    COLOR_BADGE_TEXT,
    COLOR_BORDER,
    COLOR_SURFACE,
    COLOR_TABLE_HEADER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_TITLE,
    COLOR_WHITE,
    MARGIN_BOTTOM,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    MARGIN_TOP,
    PDF_FONT_CANDIDATES,
    element_accent,
    element_palette,
    lighten_hex,
)

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas as pdf_canvas


PAGE_WIDTH, PAGE_HEIGHT = A4
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
DEFAULT_FONT_SIZE = 10.5
TEXT_TOP_ADJUST = -0.6


def resolve_pdf_font_name() -> str:
    for font_name in PDF_FONT_CANDIDATES:
        try:
            pdfmetrics.registerFont(UnicodeCIDFont(font_name))
            return font_name
        except Exception:
            continue
    return "Helvetica"


PDF_FONT_NAME = resolve_pdf_font_name()


def string_width(text: str, font_size: float) -> float:
    return pdfmetrics.stringWidth(text, PDF_FONT_NAME, font_size)


def top_to_bottom_y(top_y: float, height: float = 0.0) -> float:
    return PAGE_HEIGHT - top_y - height


def text_baseline(top_y: float, font_size: float) -> float:
    return PAGE_HEIGHT - top_y - font_size * 0.84


def centered_text_top(top_y: float, height: float, font_size: float) -> float:
    return top_y + max((height - font_size * 1.08) / 2.0 + TEXT_TOP_ADJUST, 0.0)


def draw_text(
    canvas: pdf_canvas.Canvas,
    text: str,
    x: float,
    top_y: float,
    font_size: float,
    *,
    color: str = COLOR_TEXT_PRIMARY,
    align: str = "left",
) -> None:
    if not text:
        return

    actual_x = x
    width = string_width(text, font_size)
    if align == "center":
        actual_x = x - width / 2.0
    elif align == "right":
        actual_x = x - width

    canvas.setFont(PDF_FONT_NAME, font_size)
    canvas.setFillColor(HexColor(color))
    canvas.drawString(actual_x, text_baseline(top_y, font_size), text)


def wrap_text(text: str, font_size: float, max_width: float) -> List[str]:
    if not text:
        return [""]

    lines: List[str] = []
    current = ""
    for character in text:
        test_text = current + character
        if current and string_width(test_text, font_size) > max_width:
            lines.append(current)
            current = character
        else:
            current = test_text

    if current or not lines:
        lines.append(current)
    return lines


def draw_text_lines(
    canvas: pdf_canvas.Canvas,
    lines: Sequence[str],
    x: float,
    top_y: float,
    font_size: float,
    *,
    color: str = COLOR_TEXT_PRIMARY,
    line_height: float = 16.0,
) -> float:
    current_top = top_y
    for line in lines:
        draw_text(canvas, line, x, current_top, font_size, color=color)
        current_top += line_height
    return current_top


def draw_cell_text(
    canvas: pdf_canvas.Canvas,
    text: str,
    x: float,
    top_y: float,
    width: float,
    height: float,
    font_size: float,
    *,
    color: str = COLOR_TEXT_PRIMARY,
    align: str = "center",
    padding_x: float = 0.0,
) -> None:
    text_top = centered_text_top(top_y, height, font_size)
    if align == "left":
        draw_text(canvas, text, x + padding_x, text_top, font_size, color=color)
    elif align == "right":
        draw_text(
            canvas,
            text,
            x + width - padding_x,
            text_top,
            font_size,
            color=color,
            align="right",
        )
    else:
        draw_text(
            canvas,
            text,
            x + width / 2.0,
            text_top,
            font_size,
            color=color,
            align="center",
        )


def draw_round_box(
    canvas: pdf_canvas.Canvas,
    x: float,
    top_y: float,
    width: float,
    height: float,
    *,
    fill_color: str = COLOR_SURFACE,
    stroke_color: str = COLOR_BORDER,
    radius: float = 12.0,
    line_width: float = 1.0,
) -> None:
    canvas.setLineWidth(line_width)
    canvas.setStrokeColor(HexColor(stroke_color))
    canvas.setFillColor(HexColor(fill_color))
    canvas.roundRect(
        x,
        top_to_bottom_y(top_y, height),
        width,
        height,
        radius,
        stroke=1,
        fill=1,
    )


def draw_line(
    canvas: pdf_canvas.Canvas,
    x1: float,
    top_y1: float,
    x2: float,
    top_y2: float,
    *,
    color: str = COLOR_BORDER,
    line_width: float = 1.0,
) -> None:
    canvas.setStrokeColor(HexColor(color))
    canvas.setLineWidth(line_width)
    canvas.line(x1, PAGE_HEIGHT - top_y1, x2, PAGE_HEIGHT - top_y2)


def draw_section_heading(canvas: pdf_canvas.Canvas, title: str, top_y: float) -> float:
    draw_text(canvas, title, MARGIN_LEFT, top_y, 14, color=COLOR_TITLE)
    line_y = top_y + 18
    draw_line(
        canvas,
        MARGIN_LEFT,
        line_y,
        PAGE_WIDTH - MARGIN_RIGHT,
        line_y,
        color=COLOR_BORDER,
        line_width=0.8,
    )
    return line_y + 10


def draw_badge(
    canvas: pdf_canvas.Canvas,
    text: str,
    right_x: float,
    top_y: float,
    fill_color: str,
) -> None:
    font_size = 10
    padding_x = 9
    padding_y = 5
    badge_width = string_width(text, font_size) + padding_x * 2
    badge_height = font_size + padding_y * 2 + 1
    left_x = right_x - badge_width
    draw_round_box(
        canvas,
        left_x,
        top_y,
        badge_width,
        badge_height,
        fill_color=fill_color,
        stroke_color=fill_color,
        radius=9,
        line_width=0.5,
    )
    draw_text(
        canvas,
        text,
        left_x + padding_x,
        top_y + padding_y - 1,
        font_size,
        color=COLOR_BADGE_TEXT,
    )


def draw_card_top_strip(
    canvas: pdf_canvas.Canvas,
    x: float,
    top_y: float,
    width: float,
    color: str,
) -> None:
    inset_x = 12.0
    inset_y = 2.0
    strip_height = 4.8
    canvas.setFillColor(HexColor(color))
    canvas.setStrokeColor(HexColor(color))
    canvas.roundRect(
        x + inset_x,
        top_to_bottom_y(top_y + inset_y, strip_height),
        width - inset_x * 2,
        strip_height,
        3,
        stroke=0,
        fill=1,
    )


def draw_info_item(
    canvas: pdf_canvas.Canvas,
    label: str,
    value: str,
    x: float,
    top_y: float,
    width: float,
) -> None:
    draw_text(canvas, label, x, top_y, 10, color=COLOR_TEXT_SECONDARY)
    lines = wrap_text(value, 11, width)
    draw_text_lines(
        canvas,
        lines[:2],
        x,
        top_y + 14,
        11,
        line_height=15,
    )


def render_cover_page(
    canvas: pdf_canvas.Canvas,
    cover: CoverPageData,
    page_number: int,
    total_pages: int,
) -> None:
    top_y = MARGIN_TOP
    draw_text(canvas, cover.title, MARGIN_LEFT, top_y, 24, color=COLOR_TITLE)
    draw_text(
        canvas,
        cover.subtitle,
        MARGIN_LEFT,
        top_y + 28,
        14,
        color=COLOR_TEXT_SECONDARY,
    )

    accent_top = top_y + 56
    canvas.setFillColor(HexColor(COLOR_TITLE))
    canvas.roundRect(
        MARGIN_LEFT,
        top_to_bottom_y(accent_top, 5),
        64,
        5,
        3,
        stroke=0,
        fill=1,
    )

    top_y = draw_section_heading(canvas, "使用者資訊", accent_top + 24)
    info_height = 216
    draw_round_box(canvas, MARGIN_LEFT, top_y, CONTENT_WIDTH, info_height, fill_color=COLOR_WHITE)

    inner_x = MARGIN_LEFT + 16
    inner_y = top_y + 16
    gap = 18
    column_width = (CONTENT_WIDTH - 32 - gap) / 2.0
    draw_info_item(canvas, "姓名", cover.name, inner_x, inner_y, column_width)
    draw_info_item(canvas, "出生日期", cover.birth_text, inner_x + column_width + gap, inner_y, column_width)
    draw_info_item(canvas, "八字", cover.bazi_text, inner_x, inner_y + 54, CONTENT_WIDTH - 32)
    draw_info_item(canvas, "命主喜用五行", cover.fav_text, inner_x, inner_y + 112, column_width)
    draw_info_item(canvas, "命主忌用五行", cover.unfav_text, inner_x + column_width + gap, inner_y + 112, column_width)
    draw_info_item(canvas, "報表日期範圍", cover.date_range_text, inner_x, inner_y + 164, CONTENT_WIDTH - 32)

    top_y = draw_section_heading(canvas, "顏色對應表", top_y + info_height + 20)
    table_header_height = 26
    left_col_width = 72
    row_height = 28
    table_height = table_header_height + row_height * 5
    draw_round_box(canvas, MARGIN_LEFT, top_y, CONTENT_WIDTH, table_height, fill_color=COLOR_WHITE)
    draw_round_box(
        canvas,
        MARGIN_LEFT,
        top_y,
        CONTENT_WIDTH,
        table_header_height,
        fill_color=COLOR_TABLE_HEADER,
        stroke_color=COLOR_TABLE_HEADER,
        radius=12,
        line_width=0.5,
    )
    draw_line(canvas, MARGIN_LEFT + left_col_width, top_y, MARGIN_LEFT + left_col_width, top_y + table_height, line_width=0.8)
    draw_cell_text(canvas, "五行", MARGIN_LEFT, top_y, left_col_width, table_header_height, 10, color=COLOR_TITLE)
    draw_cell_text(
        canvas,
        "對應色系",
        MARGIN_LEFT + left_col_width,
        top_y,
        CONTENT_WIDTH - left_col_width,
        table_header_height,
        10,
        color=COLOR_TITLE,
        align="left",
        padding_x=12,
    )

    for row_index in range(6):
        row_y = top_y + table_header_height + row_index * row_height
        draw_line(canvas, MARGIN_LEFT, row_y, MARGIN_LEFT + CONTENT_WIDTH, row_y, line_width=0.8)

    for index, element in enumerate(("金", "木", "水", "火", "土")):
        row_top = top_y + table_header_height + index * row_height
        swatch_size = 10
        swatch_x = MARGIN_LEFT + 18
        swatch_top = row_top + (row_height - swatch_size) / 2.0
        canvas.setFillColor(HexColor(element_accent(element)))
        canvas.roundRect(
            swatch_x,
            top_to_bottom_y(swatch_top, swatch_size),
            swatch_size,
            swatch_size,
            2,
            stroke=0,
            fill=1,
        )
        draw_cell_text(
            canvas,
            element,
            swatch_x + 12,
            row_top,
            left_col_width - 24,
            row_height,
            DEFAULT_FONT_SIZE,
            align="left",
        )
        draw_cell_text(
            canvas,
            element_palette(element),
            MARGIN_LEFT + left_col_width,
            row_top,
            CONTENT_WIDTH - left_col_width,
            row_height,
            DEFAULT_FONT_SIZE,
            align="left",
            padding_x=12,
        )

    top_y = draw_section_heading(canvas, "閱讀說明", top_y + table_height + 20)
    note_height = 100
    draw_round_box(canvas, MARGIN_LEFT, top_y, CONTENT_WIDTH, note_height, fill_color=COLOR_WHITE)
    for index, note in enumerate(cover.notes, start=1):
        base_top = top_y + 14 + (index - 1) * 24
        draw_text(canvas, "%s." % index, MARGIN_LEFT + 14, base_top, 11, color=COLOR_TITLE)
        wrapped = wrap_text(note, 11, CONTENT_WIDTH - 60)
        draw_text_lines(canvas, wrapped, MARGIN_LEFT + 30, base_top, 11, line_height=14)

    draw_footer(canvas, page_number, total_pages, left_text="%s｜%s" % (cover.name, cover.total_days_text))


def render_daily_header(canvas: pdf_canvas.Canvas, report: DailyReport) -> float:
    accent = element_accent(report.primary_element)
    top_y = MARGIN_TOP
    draw_text(canvas, report.target_date.isoformat(), MARGIN_LEFT, top_y, 18, color=COLOR_TITLE)
    draw_badge(
        canvas,
        report.weekday,
        PAGE_WIDTH - MARGIN_RIGHT,
        top_y + 1,
        lighten_hex(accent, 0.78),
    )
    accent_top = top_y + 26
    canvas.setFillColor(HexColor(accent))
    canvas.roundRect(
        MARGIN_LEFT,
        top_to_bottom_y(accent_top, 4),
        58,
        4,
        2,
        stroke=0,
        fill=1,
    )
    draw_text(canvas, report.pillars_text, MARGIN_LEFT, top_y + 40, 11)
    draw_text(canvas, report.wuxing_summary, MARGIN_LEFT, top_y + 56, 11, color=COLOR_TEXT_SECONDARY)
    return top_y + 84


def draw_table_header(
    canvas: pdf_canvas.Canvas,
    table_x: float,
    table_top: float,
    table_width: float,
    header_height: float,
    column_widths: Sequence[float],
) -> None:
    draw_round_box(
        canvas,
        table_x,
        table_top,
        table_width,
        header_height,
        fill_color=COLOR_TABLE_HEADER,
        stroke_color=COLOR_TABLE_HEADER,
        radius=12,
        line_width=0.5,
    )
    headers = ("排名", "五行", "分數", "建議等級", "色系")
    cursor_x = table_x
    for width, header in zip(column_widths, headers):
        draw_cell_text(
            canvas,
            header,
            cursor_x,
            table_top,
            width,
            header_height,
            10,
            color=COLOR_TITLE,
            align="left" if header == "色系" else "center",
            padding_x=12,
        )
        cursor_x += width


def render_ranking_table(canvas: pdf_canvas.Canvas, report: DailyReport, top_y: float) -> float:
    section_top = draw_section_heading(canvas, "五行排行與分數", top_y)
    table_x = MARGIN_LEFT
    table_width = CONTENT_WIDTH
    header_height = 26
    row_height = 28
    table_height = header_height + row_height * len(report.ranking_rows)
    draw_round_box(canvas, table_x, section_top, table_width, table_height, fill_color=COLOR_WHITE)

    column_widths = (42.0, 42.0, 48.0, 80.0, table_width - 212.0)
    draw_table_header(canvas, table_x, section_top, table_width, header_height, column_widths)

    cursor_x = table_x
    for width in column_widths[:-1]:
        cursor_x += width
        draw_line(canvas, cursor_x, section_top, cursor_x, section_top + table_height, line_width=0.8)

    for row_index, row in enumerate(report.ranking_rows):
        row_top = section_top + header_height + row_index * row_height
        draw_line(canvas, table_x, row_top, table_x + table_width, row_top, line_width=0.8)

        palette_x = table_x + sum(column_widths[:4]) + 12

        draw_cell_text(canvas, str(row.rank), table_x, row_top, column_widths[0], row_height, 10)
        draw_cell_text(
            canvas,
            row.element,
            table_x + column_widths[0],
            row_top,
            column_widths[1],
            row_height,
            10.5,
        )
        draw_cell_text(
            canvas,
            str(row.score),
            table_x + column_widths[0] + column_widths[1],
            row_top,
            column_widths[2],
            row_height,
            10,
        )
        draw_cell_text(
            canvas,
            row.level,
            table_x + column_widths[0] + column_widths[1] + column_widths[2],
            row_top,
            column_widths[3],
            row_height,
            10,
        )

        swatch_size = 10
        swatch_top = row_top + (row_height - swatch_size) / 2.0
        canvas.setFillColor(HexColor(element_accent(row.element)))
        canvas.roundRect(
            palette_x,
            top_to_bottom_y(swatch_top, swatch_size),
            swatch_size,
            swatch_size,
            2,
            stroke=0,
            fill=1,
        )
        draw_cell_text(
            canvas,
            row.palette,
            table_x + sum(column_widths[:4]),
            row_top,
            column_widths[4],
            row_height,
            10,
            align="left",
            padding_x=26,
        )

    return section_top + table_height


def draw_advice_card(
    canvas: pdf_canvas.Canvas,
    x: float,
    top_y: float,
    width: float,
    height: float,
    label: str,
    value: str,
    accent_color: str,
) -> None:
    draw_round_box(canvas, x, top_y, width, height, fill_color=COLOR_WHITE)
    draw_card_top_strip(canvas, x, top_y, width, accent_color)
    draw_text(canvas, label, x + 14, top_y + 16, 10, color=COLOR_TEXT_SECONDARY)
    lines = wrap_text(value, 11, width - 24)
    draw_text_lines(canvas, lines[:2], x + 14, top_y + 34, 11, line_height=15)


def render_advice_section(canvas: pdf_canvas.Canvas, report: DailyReport, top_y: float) -> float:
    section_top = draw_section_heading(canvas, "當日建議", top_y)
    gap = 10
    card_width = (CONTENT_WIDTH - gap * 2) / 3.0
    card_height = 74
    x1 = MARGIN_LEFT
    x2 = x1 + card_width + gap
    x3 = x2 + card_width + gap

    draw_advice_card(canvas, x1, section_top, card_width, card_height, "主色建議", "%s色系" % report.primary_element, element_accent(report.primary_element))
    draw_advice_card(canvas, x2, section_top, card_width, card_height, "輔助色建議", "、".join("%s色系" % item for item in report.support_elements), lighten_hex(element_accent(report.support_elements[0]), 0.16))
    draw_advice_card(canvas, x3, section_top, card_width, card_height, "配件色", ("%s色系" % report.accessory_element) if report.accessory_element else "無", element_accent(report.accessory_element) if report.accessory_element else COLOR_BORDER)

    return section_top + card_height


def render_outfit_strategy_section(canvas: pdf_canvas.Canvas, report: DailyReport, top_y: float) -> float:
    section_top = draw_section_heading(canvas, "穿搭策略", top_y)
    box_height = 102
    draw_round_box(canvas, MARGIN_LEFT, section_top, CONTENT_WIDTH, box_height, fill_color=COLOR_WHITE)

    inner_x = MARGIN_LEFT + 16
    inner_right = PAGE_WIDTH - MARGIN_RIGHT - 16
    row_height = 28
    row_start = section_top + 14
    label_width = 88
    rows = (
        report.outfit_strategy.conservative,
        report.outfit_strategy.safe_combo,
        report.outfit_strategy.accessory,
    )
    for index, row_text in enumerate(rows):
        row_top = row_start + index * row_height
        if index:
            divider_top = row_top - 7
            draw_line(canvas, inner_x, divider_top, inner_right, divider_top, line_width=0.5)

        label, value = row_text.split("：", 1)
        draw_cell_text(
            canvas,
            "%s：" % label,
            inner_x,
            row_top,
            label_width,
            18,
            10.5,
            color=COLOR_TITLE,
            align="left",
        )
        draw_cell_text(
            canvas,
            value,
            inner_x + label_width,
            row_top,
            CONTENT_WIDTH - 32 - label_width,
            18,
            10.5,
            align="left",
        )

    return section_top + box_height


def render_daily_insight_section(canvas: pdf_canvas.Canvas, report: DailyReport, top_y: float) -> float:
    if not report.daily_insight:
        return top_y

    section_top = draw_section_heading(canvas, "今日重點", top_y)
    lines = wrap_text(report.daily_insight, 10.5, CONTENT_WIDTH - 52)
    box_height = 48 + max(0, len(lines) - 1) * 14
    draw_round_box(canvas, MARGIN_LEFT, section_top, CONTENT_WIDTH, box_height, fill_color=COLOR_WHITE)
    accent = element_accent(report.primary_element)
    canvas.setFillColor(HexColor(accent))
    canvas.roundRect(
        MARGIN_LEFT + 2.0,
        top_to_bottom_y(section_top + 2.0, box_height - 4.0),
        5,
        box_height - 4.0,
        3,
        stroke=0,
        fill=1,
    )
    draw_text_lines(canvas, lines[:2], MARGIN_LEFT + 20, section_top + 15, 10.5, line_height=15)
    return section_top + box_height


def draw_footer(
    canvas: pdf_canvas.Canvas,
    page_number: int,
    total_pages: int,
    *,
    left_text: str,
) -> None:
    line_top = PAGE_HEIGHT - MARGIN_BOTTOM + 6
    draw_line(canvas, MARGIN_LEFT, line_top, PAGE_WIDTH - MARGIN_RIGHT, line_top, line_width=0.8)
    draw_text(canvas, left_text, MARGIN_LEFT, line_top + 6, 8.5, color=COLOR_TEXT_SECONDARY)
    draw_text(
        canvas,
        "第 %s / %s 頁" % (page_number, total_pages),
        PAGE_WIDTH - MARGIN_RIGHT,
        line_top + 6,
        8.5,
        color=COLOR_TEXT_SECONDARY,
        align="right",
    )


def render_daily_page(
    canvas: pdf_canvas.Canvas,
    report: DailyReport,
    page_number: int,
    total_pages: int,
) -> None:
    top_y = render_daily_header(canvas, report)
    top_y = render_ranking_table(canvas, report, top_y) + 18
    top_y = render_advice_section(canvas, report, top_y) + 18
    top_y = render_outfit_strategy_section(canvas, report, top_y) + 18
    render_daily_insight_section(canvas, report, top_y)
    draw_footer(canvas, page_number, total_pages, left_text=report.target_date.isoformat())


def write_reports_pdf(
    cover_page: CoverPageData,
    reports: Sequence[DailyReport],
    output_pdf,
) -> None:
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    canvas = pdf_canvas.Canvas(str(output_pdf), pagesize=A4, pageCompression=1)
    canvas.setTitle("%s - %s" % (cover_page.title, cover_page.name))
    canvas.setSubject(cover_page.subtitle)
    canvas.setAuthor(cover_page.name)
    canvas.setCreator("WuXing Color Engine")
    total_pages = len(reports) + 1

    render_cover_page(canvas, cover_page, 1, total_pages)
    canvas.showPage()

    for index, report in enumerate(reports, start=2):
        render_daily_page(canvas, report, index, total_pages)
        canvas.showPage()

    canvas.save()
