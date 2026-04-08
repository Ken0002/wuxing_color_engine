#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Tuple

from flask import Flask, jsonify, render_template, request

from bazi_calculator import get_bazi_chart
from core_scoring import calculate_core_scores
from date_energy_calculator import FIVE_ELEMENTS, get_date_energy


app = Flask(__name__)


def build_birth_datetime(payload: Dict) -> datetime:
    return datetime(
        int(payload["year"]),
        int(payload["month"]),
        int(payload["day"]),
        int(payload["hour"]),
        int(payload["minute"]),
    )


def build_target_date(payload: Dict) -> date:
    return date(
        int(payload["year"]),
        int(payload["month"]),
        int(payload["day"]),
    )


def format_date_pillars(energy) -> str:
    return (
        f"{energy.year_pillar.name}年"
        f"{energy.month_pillar.name}月"
        f"{energy.day_pillar.name}日"
    )


def format_date_elements(energy) -> str:
    return f"{energy.year_element}年{energy.month_element}月{energy.day_element}日"


def build_ranking_payload(scores: Dict[str, int], ranking: Tuple[str, ...]):
    return [
        {
            "element": element,
            "score": scores[element],
            "label": f"{index}. {element} {scores[element]}分",
        }
        for index, element in enumerate(ranking, start=1)
    ]


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/score")
def api_score():
    payload = request.get_json(silent=True) or {}

    try:
        birth_dt = build_birth_datetime(payload["birth"])
        target_date = build_target_date(payload["target_date"])
    except (KeyError, TypeError, ValueError) as exc:
        return jsonify({"error": "日期或時間格式不正確"}), 400

    chart = get_bazi_chart(birth_dt)
    energy = get_date_energy(target_date)
    result = calculate_core_scores(
        birth_dt.strftime("%Y-%m-%d %H:%M"),
        chart,
        energy,
    )

    return jsonify(
        {
            "birth_datetime": birth_dt.strftime("%Y-%m-%d %H:%M"),
            "target_date": target_date.isoformat(),
            "fav_summary": (
                f"命主喜忌: 喜:{'、'.join(result.profile.fav_elements)} / "
                f"忌:{'、'.join(result.profile.unfav_elements) if result.profile.unfav_elements else '無'}"
            ),
            "date_pillars": format_date_pillars(energy),
            "date_elements": format_date_elements(energy),
            "ranking": build_ranking_payload(result.scores, result.ranking),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7788, debug=False)
