"""Fill the database with six months of sample expenses and a few budgets.

Usage: python seed.py
"""

import datetime as dt
import random

from tracker import db

# (category, typical amount, entries per month)
PATTERNS = [
    ("Food", 25, 18),
    ("Transport", 15, 10),
    ("Entertainment", 30, 4),
    ("Shopping", 60, 3),
    ("Health", 40, 1),
    ("Bills", 90, 2),
]
BUDGETS = {"Food": 450, "Transport": 150, "Entertainment": 100, "Shopping": 150}


def main() -> None:
    db.init_db()
    if not db.get_expenses().empty:
        print("Database already has expenses, nothing seeded.")
        return

    rng = random.Random(42)
    today = dt.date.today()
    count = 0
    for months_back in range(6):
        year, month = divmod(today.year * 12 + today.month - 1 - months_back, 12)
        first = dt.date(year, month + 1, 1)
        last_day = today.day if months_back == 0 else 28
        db.add_expense(first.isoformat(), 1200, "Housing", "Rent")
        count += 1
        for category, typical, per_month in PATTERNS:
            for _ in range(per_month):
                day = first.replace(day=rng.randint(1, last_day))
                amount = round(typical * rng.uniform(0.4, 1.8), 2)
                db.add_expense(day.isoformat(), amount, category)
                count += 1

    for category, limit in BUDGETS.items():
        db.set_budget(category, limit)
    print(f"Seeded {count} expenses and {len(BUDGETS)} budgets into {db.DB_PATH}.")


if __name__ == "__main__":
    main()
