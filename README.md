# Expense Tracker

A small personal expense tracker. Log what you spend, sort it into categories, set monthly budgets per category, and see where the money goes on a dashboard with monthly totals, charts and budget alerts.

Built with Python, SQLite, Pandas, Matplotlib and Streamlit. Everything is stored locally in `expenses.db`, which is created the first time you run the app.

## Setup

Requires Python 3.11 or newer.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

The sidebar switches between four pages:

- **Add expense**: date, amount, category (or a new one) and an optional note.
- **Expenses**: every expense, filterable by month and category. Select rows to delete them.
- **Dashboard**: the month's total, a breakdown by category, a donut chart, the last 12 months and daily spending. Budget status is shown at the bottom, with a banner at the top if any category is over budget.
- **Budgets**: set a monthly limit per category. Categories at 80% of their limit or more show a warning, and those over 100% show an error.

### Sample data

To try the dashboard with some data:

```bash
python seed.py
```

This adds six months of sample expenses and a few budgets. It does nothing if the database already has expenses. Delete `expenses.db` to start over.

## Tests

```bash
python -m pytest
```

## Project layout

```
app.py             Streamlit UI
seed.py            sample data
tracker/db.py      SQLite schema and queries
tracker/analysis.py  monthly totals, category grouping, budget status
tracker/charts.py  Matplotlib figures
tests/             pytest tests
```

The currency symbol is set by `CURRENCY_SYMBOL` in `tracker/__init__.py`.
