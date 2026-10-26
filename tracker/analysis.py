"""Aggregations over the expenses DataFrame returned by db.get_expenses.

Dates are ISO strings (YYYY-MM-DD), so a month is the first seven characters.
"""

from __future__ import annotations

import pandas as pd

WARNING_THRESHOLD = 0.8


def available_months(df: pd.DataFrame) -> list[str]:
    """Return the months (YYYY-MM) that have expenses, newest first."""
    return sorted(df["date"].str[:7].unique(), reverse=True)


def filter_month(df: pd.DataFrame, month: str) -> pd.DataFrame:
    """Return the expenses that fall in the given month (YYYY-MM)."""
    return df[df["date"].str.startswith(month)]


def category_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Total and share of spending per category, largest first."""
    out = df.groupby("category", as_index=False)["amount"].sum()
    out = out.rename(columns={"amount": "total"}).astype({"total": float})
    out["share"] = out["total"] / out["total"].sum()
    return out.sort_values("total", ascending=False, ignore_index=True)


def monthly_totals(df: pd.DataFrame, end_month: str, months: int = 12) -> pd.DataFrame:
    """Total spending for each of the `months` months ending at end_month, zero-filled."""
    end = pd.Period(end_month, freq="M")
    index = pd.period_range(end - (months - 1), end, freq="M").strftime("%Y-%m")
    totals = df.groupby(df["date"].str[:7])["amount"].sum()
    out = totals.reindex(index, fill_value=0.0).astype(float)
    return out.rename_axis("month").reset_index(name="total")


def daily_totals(df: pd.DataFrame, month: str) -> pd.DataFrame:
    """Total spending for every day of the month (YYYY-MM), zero-filled."""
    period = pd.Period(month, freq="M")
    days = pd.date_range(period.start_time, period.end_time.normalize(), freq="D")
    in_month = filter_month(df, month)
    totals = in_month.groupby(pd.to_datetime(in_month["date"]))["amount"].sum()
    out = totals.reindex(days, fill_value=0.0).astype(float)
    return out.rename_axis("date").reset_index(name="total")


def budget_status(df: pd.DataFrame, budgets: pd.DataFrame) -> pd.DataFrame:
    """Spending against each budget, most used first.

    `df` should already be filtered to one month. Status is 'over' above 100% of
    the limit, 'warning' from 80% up to and including 100%, otherwise 'ok'.
    """
    spent = df.groupby("category")["amount"].sum()
    out = budgets.rename(columns={"monthly_limit": "limit"}).astype({"limit": float})
    out["spent"] = out["category"].map(spent).fillna(0.0).astype(float)
    # Rounding stops float noise (e.g. 0.7999999) from flipping a threshold.
    out["pct"] = (out["spent"] / out["limit"]).round(9)
    out["status"] = "ok"
    out.loc[out["pct"] >= WARNING_THRESHOLD, "status"] = "warning"
    out.loc[out["pct"] > 1, "status"] = "over"
    out = out[["category", "spent", "limit", "pct", "status"]]
    return out.sort_values("pct", ascending=False, ignore_index=True)
