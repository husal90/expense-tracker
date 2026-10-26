"""Matplotlib figures for the dashboard.

Figures are built with matplotlib.figure.Figure rather than pyplot, so they never
enter pyplot's global registry and are freed once the caller drops them.
"""

from __future__ import annotations

import matplotlib.dates as mdates
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from tracker import format_currency

ACCENT = "#3b6ea5"
PALETTE = ["#3b6ea5", "#e07a5f", "#81b29a", "#f2cc8f", "#6d597a", "#9a8c98", "#5fa8d3", "#b56576"]
_CURRENCY_TICKS = FuncFormatter(lambda value, _pos: format_currency(value))


def _new_figure() -> tuple[Figure, Axes]:
    fig = Figure(figsize=(7, 4), layout="constrained")
    ax = fig.subplots()
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    return fig, ax


def category_donut(totals: pd.DataFrame) -> Figure:
    """Donut chart of spending by category, from analysis.category_totals."""
    fig, ax = _new_figure()
    ax.pie(
        totals["total"],
        labels=totals["category"],
        colors=[PALETTE[i % len(PALETTE)] for i in range(len(totals))],
        autopct="%1.0f%%",
        pctdistance=0.8,
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.4, "edgecolor": "white"},
    )
    ax.text(0, 0, format_currency(totals["total"].sum()), ha="center", va="center", fontsize=13)
    ax.set_title("Spending by category")
    ax.set_aspect("equal")
    return fig


def monthly_bar(monthly: pd.DataFrame) -> Figure:
    """Bar chart of monthly totals, from analysis.monthly_totals."""
    fig, ax = _new_figure()
    ax.bar(monthly["month"], monthly["total"], color=ACCENT)
    ax.set_title("Monthly totals")
    ax.set_xlabel("Month")
    ax.set_ylabel("Spent")
    ax.yaxis.set_major_formatter(_CURRENCY_TICKS)
    ax.tick_params(axis="x", labelrotation=45)
    return fig


def daily_line(daily: pd.DataFrame) -> Figure:
    """Line chart of spending per day, from analysis.daily_totals."""
    fig, ax = _new_figure()
    ax.plot(daily["date"], daily["total"], color=ACCENT, marker="o", markersize=3)
    ax.set_title("Daily spending")
    ax.set_xlabel("Day of month")
    ax.set_ylabel("Spent")
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(_CURRENCY_TICKS)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d"))
    return fig
