from backend.analytics import (
    get_spending_by_category,
    get_top_categories,
    get_top_merchants,
    get_transaction_categories,
    list_transactions as get_transaction_list,
    get_recurring_expenses,
    get_spending_by_month,
    compare_periods,
    get_average_weekly_spend,
    get_spending_to_income_ratio,
    detect_duplicates,
    detect_anomalies,
    get_savings_goal_progress,
    forecast_end_of_month_balance,
)


def spending_by_category(
    category: str | None = None,
    month: str | None = None,
) -> dict:
    """Get total spending for a category and optional month."""
    return get_spending_by_category(
        category=category,
        month=month,
    )

def top_categories(
    limit: int = 5,
    month: str | None = None,
) -> list[dict] | dict:
    """Get the highest-spending categories, optionally for a specific month."""
    return get_top_categories(limit=limit, month=month)


def top_merchants(limit: int = 5) -> list[dict]:
    """Get the merchants with the highest total spending."""
    return get_top_merchants(limit=limit)


def transaction_categories() -> dict:
    """Get the current dataset's category and subcategory values."""
    return get_transaction_categories()


def list_transactions(
    category: str | None = None,
    subcategory: str | None = None,
    merchant: str | None = None,
    month: str | None = None,
    include_logo: bool = False,
    return_all: bool = False,
    limit: int = 25,
) -> dict:
    """Return matching transactions, including logos only when requested."""
    return get_transaction_list(
        category=category,
        subcategory=subcategory,
        merchant=merchant,
        month=month,
        include_logo=include_logo,
        return_all=return_all,
        limit=limit,
    )


def recurring_expenses() -> list[dict]:
    """Get recurring expenses grouped by merchant."""
    return get_recurring_expenses()


def spending_by_month() -> list[dict]:
    """Get total expense spending for each month."""
    return get_spending_by_month()


def compare_spending(period_1: str, period_2: str) -> dict:
    """Compare expense spending between two YYYY-MM periods."""
    return compare_periods(
        period_1=period_1,
        period_2=period_2,
    )


def average_weekly_spend(category: str | None = None) -> dict:
    """Get average weekly spending overall or for a category."""
    return get_average_weekly_spend(category=category)


def duplicate_transactions() -> list[dict]:
    """Find exact duplicate expense transactions."""
    return detect_duplicates()


def unusual_transactions(threshold: float = 2.0) -> list[dict]:
    """Find unusually large expense transactions using a z-score threshold."""
    return detect_anomalies(threshold=threshold)

def spending_to_income_ratio(
    categories: list[str],
    month: str | None = None,
) -> dict:
    """Calculate what percentage of income goes toward selected spending categories."""
    return get_spending_to_income_ratio(
        categories=categories,
        month=month,
    )


def savings_goal_progress(goal_amount: float, month: str | None = None) -> dict:
    """Compare a monthly savings goal with recorded income minus expenses."""
    return get_savings_goal_progress(goal_amount=goal_amount, month=month)


def end_of_month_balance_forecast() -> dict:
    """Forecast a balance using the latest recorded daily spending rate."""
    return forecast_end_of_month_balance()
