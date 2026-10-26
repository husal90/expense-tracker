import pytest

from tracker import db


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    db.init_db(path)
    return path


def test_new_database_is_empty(db_path):
    assert db.get_expenses(db_path).empty
    assert db.get_budgets(db_path).empty


def test_init_db_is_idempotent(db_path):
    db.add_expense("2024-01-01", 5, "Food", db_path=db_path)
    db.init_db(db_path)
    assert len(db.get_expenses(db_path)) == 1


def test_add_and_get_expense(db_path):
    expense_id = db.add_expense("2024-03-05", 12.5, "Food", "  lunch ", db_path=db_path)
    df = db.get_expenses(db_path)
    assert df.to_dict("records") == [
        {"id": expense_id, "date": "2024-03-05", "amount": 12.5, "category": "Food", "note": "lunch"}
    ]


def test_blank_note_is_stored_as_null(db_path):
    db.add_expense("2024-03-05", 1, "Food", "   ", db_path=db_path)
    assert db.get_expenses(db_path)["note"].isna().all()


def test_expenses_are_newest_first(db_path):
    db.add_expense("2024-01-01", 1, "Food", db_path=db_path)
    db.add_expense("2024-02-01", 2, "Food", db_path=db_path)
    assert list(db.get_expenses(db_path)["date"]) == ["2024-02-01", "2024-01-01"]


@pytest.mark.parametrize("amount", [0, -5, float("nan")])
def test_rejects_non_positive_amount(db_path, amount):
    with pytest.raises(ValueError):
        db.add_expense("2024-01-01", amount, "Food", db_path=db_path)


@pytest.mark.parametrize("date", ["2024-13-01", "yesterday", ""])
def test_rejects_invalid_date(db_path, date):
    with pytest.raises(ValueError):
        db.add_expense(date, 10, "Food", db_path=db_path)


def test_rejects_blank_category(db_path):
    with pytest.raises(ValueError):
        db.add_expense("2024-01-01", 10, "  ", db_path=db_path)


def test_delete_expense(db_path):
    keep = db.add_expense("2024-01-01", 1, "Food", db_path=db_path)
    drop = db.add_expense("2024-01-02", 2, "Food", db_path=db_path)
    assert db.delete_expense(drop, db_path) is True
    assert db.delete_expense(drop, db_path) is False
    assert list(db.get_expenses(db_path)["id"]) == [keep]


def test_set_budget_inserts_then_updates(db_path):
    db.set_budget("Food", 300, db_path)
    db.set_budget("Food", 450, db_path)
    assert db.get_budgets(db_path).to_dict("records") == [{"category": "Food", "monthly_limit": 450.0}]


def test_set_budget_rejects_non_positive_limit(db_path):
    with pytest.raises(ValueError):
        db.set_budget("Food", 0, db_path)


def test_categories_include_defaults_then_custom(db_path):
    db.add_expense("2024-01-01", 1, "Pets", db_path=db_path)
    db.add_expense("2024-01-01", 1, "Food", db_path=db_path)
    db.set_budget("Gifts", 50, db_path)
    assert db.get_categories(db_path) == db.DEFAULT_CATEGORIES + ["Gifts", "Pets"]
