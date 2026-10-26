import pandas as pd
import pytest

from tracker import analysis

COLUMNS = ["id", "date", "amount", "category", "note"]


def expenses(*rows):
    """Build an expenses frame from (date, amount, category) tuples."""
    return pd.DataFrame(
        [(i, d, a, c, None) for i, (d, a, c) in enumerate(rows, 1)], columns=COLUMNS
    )


EMPTY = pd.DataFrame(columns=COLUMNS)
SAMPLE = expenses(
    ("2024-01-05", 10.0, "Food"),
    ("2024-01-20", 30.0, "Food"),
    ("2024-01-20", 60.0, "Housing"),
    ("2024-02-01", 5.0, "Food"),
)


def budgets(**limits):
    return pd.DataFrame(list(limits.items()), columns=["category", "monthly_limit"])


def test_available_months_newest_first():
    assert analysis.available_months(SAMPLE) == ["2024-02", "2024-01"]
    assert analysis.available_months(EMPTY) == []


def test_filter_month():
    assert list(analysis.filter_month(SAMPLE, "2024-01")["id"]) == [1, 2, 3]
    assert analysis.filter_month(EMPTY, "2024-01").empty


def test_category_totals():
    out = analysis.category_totals(analysis.filter_month(SAMPLE, "2024-01"))
    assert out.to_dict("records") == [
        {"category": "Housing", "total": 60.0, "share": 0.6},
        {"category": "Food", "total": 40.0, "share": 0.4},
    ]


def test_category_totals_empty():
    out = analysis.category_totals(EMPTY)
    assert out.empty
    assert list(out.columns) == ["category", "total", "share"]


def test_monthly_totals_zero_fills_and_crosses_year():
    out = analysis.monthly_totals(SAMPLE, "2024-02", months=3)
    assert out.to_dict("records") == [
        {"month": "2023-12", "total": 0.0},
        {"month": "2024-01", "total": 100.0},
        {"month": "2024-02", "total": 5.0},
    ]


def test_monthly_totals_defaults_to_twelve_months():
    assert len(analysis.monthly_totals(SAMPLE, "2024-02")) == 12


def test_monthly_totals_empty():
    out = analysis.monthly_totals(EMPTY, "2024-02")
    assert len(out) == 12
    assert (out["total"] == 0).all()


def test_daily_totals_covers_every_day():
    out = analysis.daily_totals(SAMPLE, "2024-01")
    assert len(out) == 31
    assert out.loc[out["date"] == "2024-01-20", "total"].item() == 90.0
    assert out["total"].sum() == 100.0


def test_daily_totals_leap_february_and_empty():
    out = analysis.daily_totals(EMPTY, "2024-02")
    assert len(out) == 29
    assert (out["total"] == 0).all()


@pytest.mark.parametrize(
    ("spent", "expected"),
    [
        (0.0, "ok"),
        (79.99, "ok"),
        (80.0, "warning"),
        (99.99, "warning"),
        (100.0, "warning"),
        (100.01, "over"),
        (250.0, "over"),
    ],
)
def test_budget_status_thresholds(spent, expected):
    df = expenses(("2024-01-01", spent, "Food")) if spent else EMPTY
    out = analysis.budget_status(df, budgets(Food=100.0))
    assert out["status"].item() == expected


def test_budget_status_float_noise_does_not_drop_below_threshold():
    # 0.1 + 0.7 sums to 0.7999999999999999 in floating point.
    df = expenses(("2024-01-01", 0.1, "Food"), ("2024-01-02", 0.7, "Food"))
    assert analysis.budget_status(df, budgets(Food=1.0))["status"].item() == "warning"


def test_budget_status_only_budgeted_categories_sorted_by_usage():
    out = analysis.budget_status(analysis.filter_month(SAMPLE, "2024-01"), budgets(Food=50.0, Bills=20.0))
    assert out.to_dict("records") == [
        {"category": "Food", "spent": 40.0, "limit": 50.0, "pct": 0.8, "status": "warning"},
        {"category": "Bills", "spent": 0.0, "limit": 20.0, "pct": 0.0, "status": "ok"},
    ]


def test_budget_status_no_budgets():
    out = analysis.budget_status(SAMPLE, budgets())
    assert out.empty
    assert list(out.columns) == ["category", "spent", "limit", "pct", "status"]
