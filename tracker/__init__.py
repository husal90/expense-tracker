"""Personal expense tracker: storage, analysis and charts."""

CURRENCY_SYMBOL = "$"


def format_currency(amount: float) -> str:
    """Format an amount as currency, e.g. 1234.5 -> '$1,234.50'."""
    return f"{CURRENCY_SYMBOL}{amount:,.2f}"
