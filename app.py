"""Streamlit UI for the expense tracker. Run with: streamlit run app.py"""

import datetime as dt

import pandas as pd
import streamlit as st

from tracker import analysis, charts, db, format_currency

st.set_page_config(page_title="Expense Tracker", layout="wide")
db.init_db()


def show_figure(fig) -> None:
    """Render a Matplotlib figure and release it."""
    st.pyplot(fig, clear_figure=True)


def add_expense_page() -> None:
    st.header("Add expense")
    with st.form("add_expense", clear_on_submit=True):
        date = st.date_input("Date", value=dt.date.today())
        amount = st.number_input("Amount", min_value=0.0, step=1.0, format="%.2f")
        category = st.selectbox("Category", db.get_categories())
        custom = st.text_input("Or add a new category", placeholder="e.g. Pets")
        note = st.text_input("Note (optional)")
        submitted = st.form_submit_button("Save")

    if submitted:
        if amount <= 0:
            st.error("Amount must be greater than zero.")
            return
        try:
            db.add_expense(date.isoformat(), amount, custom.strip() or category, note)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.success(f"Saved {format_currency(amount)} in {custom.strip() or category}.")


def expenses_page() -> None:
    st.header("Expenses")
    df = db.get_expenses()
    if df.empty:
        st.info("No expenses yet. Add one on the Add expense page.")
        return

    left, right = st.columns(2)
    month = left.selectbox("Month", ["All", *analysis.available_months(df)])
    categories = right.multiselect("Category", sorted(df["category"].unique()))

    view = df if month == "All" else analysis.filter_month(df, month)
    if categories:
        view = view[view["category"].isin(categories)]
    view = view.reset_index(drop=True)
    if view.empty:
        st.info("No expenses match these filters.")
        return

    st.caption(f"{len(view)} expenses, {format_currency(view['amount'].sum())} total. "
               "Select rows to delete them.")
    event = st.dataframe(
        view.style.format({"amount": format_currency}, na_rep=""),
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
    )
    selected = view.iloc[event.selection.rows]
    if not selected.empty and st.button(f"Delete {len(selected)} selected", type="primary"):
        for expense_id in selected["id"]:
            db.delete_expense(int(expense_id))
        st.rerun()


def show_budget_status(status: pd.DataFrame) -> None:
    st.subheader("Budgets")
    if status.empty:
        st.info("No budgets set. Add some on the Budgets page.")
        return
    for row in status.itertuples():
        text = (f"**{row.category}**: {format_currency(row.spent)} of "
                f"{format_currency(row.limit)} ({row.pct:.0%})")
        if row.status == "over":
            st.error(text)
        elif row.status == "warning":
            st.warning(text)
        else:
            st.success(text)


def dashboard_page() -> None:
    st.header("Dashboard")
    banner = st.container()  # filled once we know the month, but rendered above everything
    df = db.get_expenses()
    if df.empty:
        st.info("No expenses yet. Add some to see the dashboard.")
        return

    month = st.selectbox("Month", analysis.available_months(df))
    month_df = analysis.filter_month(df, month)
    status = analysis.budget_status(month_df, db.get_budgets())
    over = status[status["status"] == "over"]
    if not over.empty:
        banner.error(f"Over budget this month: {', '.join(over['category'])}")

    st.metric("Total spent", format_currency(month_df["amount"].sum()))

    totals = analysis.category_totals(month_df)
    left, right = st.columns(2)
    with left:
        st.subheader("By category")
        st.dataframe(
            totals.style.format({"total": format_currency, "share": "{:.0%}"}),
            hide_index=True,
        )
    with right:
        show_figure(charts.category_donut(totals))

    left, right = st.columns(2)
    with left:
        show_figure(charts.monthly_bar(analysis.monthly_totals(df, month)))
    with right:
        show_figure(charts.daily_line(analysis.daily_totals(df, month)))

    show_budget_status(status)


def budgets_page() -> None:
    st.header("Budgets")
    with st.form("set_budget"):
        category = st.selectbox("Category", db.get_categories())
        limit = st.number_input("Monthly limit", min_value=0.0, step=10.0, format="%.2f")
        submitted = st.form_submit_button("Save")
    if submitted:
        try:
            db.set_budget(category, limit)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.success(f"{category} budget set to {format_currency(limit)} per month.")

    budgets = db.get_budgets()
    if budgets.empty:
        st.info("No budgets yet.")
    else:
        st.dataframe(budgets.style.format({"monthly_limit": format_currency}), hide_index=True)


PAGES = {
    "Add expense": add_expense_page,
    "Expenses": expenses_page,
    "Dashboard": dashboard_page,
    "Budgets": budgets_page,
}

page = st.sidebar.radio("Page", list(PAGES))
PAGES[page]()
