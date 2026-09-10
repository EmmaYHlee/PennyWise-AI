import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
"""
Analytics functions:
- load_transactions(): Load and prepare enriched transaction data.
- get_data_coverage(): Make data coverage an explicit part of the analytics layer.
- get_spending_by_category(): Calculate spending for a category.
- get_top_categories(): Rank categories by total spending.
- get_top_merchants(): Rank merchants by total spending.
- get_transactions_by_merchant(): Searches the actual enriched transaction data.
- get_recurring_expenses(): Identify recurring expenses and totals.
- get_spending_by_month(): Calculate total spending by month.
- compare_periods(): Compare spending between two periods.
- get_average_weekly_spend(): Calculate average weekly spending.
- get_spending_to_income_ratio(): Calculate spending to income ratio.
- detect_duplicates(): Detect exact duplicate expense transactions.
- detect_anomalies(): Identify unusually large expense transactions.
"""

def load_transactions(
    path: str = "data/enriched_transactions.csv",
) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df

def get_data_coverage(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = load_transactions()

    return {
        "start_date": df["date"].min().date().isoformat(),
        "end_date": df["date"].max().date().isoformat(),
    }


def get_savings_goal_progress(
    goal_amount: float,
    month: str | None = None,
    df: pd.DataFrame | None = None,
) -> dict:
    """Compare a monthly savings goal with recorded income minus expenses."""
    if df is None:
        df = load_transactions()

    if goal_amount < 0:
        raise ValueError("goal_amount must be zero or greater")

    data_start = df["date"].min().date()
    data_end = df["date"].max().date()
    available_months = df["date"].dt.to_period("M")

    if month:
        requested_month = pd.Period(month, freq="M")
        if requested_month < available_months.min() or requested_month > available_months.max():
            return {
                "available": False,
                "reason": "requested month is outside available transaction data",
                "data_start": data_start.isoformat(),
                "data_end": data_end.isoformat(),
            }
        selected_month = requested_month
    else:
        income_months = df.loc[
            df["transaction_type"] == "income", "date"
        ].dt.to_period("M")
        if income_months.empty:
            return {
                "available": False,
                "reason": "no recorded income is available to calculate savings progress",
                "data_start": data_start.isoformat(),
                "data_end": data_end.isoformat(),
            }
        selected_month = income_months.max()

    selected = df[available_months == selected_month]
    income = selected.loc[selected["transaction_type"] == "income", "amount"].sum()
    expenses = selected.loc[selected["transaction_type"] == "expense", "amount"].sum()
    net_savings = income - expenses

    return {
        "available": True,
        "month": str(selected_month),
        "goal_amount": round(float(goal_amount), 2),
        "income": round(float(income), 2),
        "expenses": round(float(expenses), 2),
        "net_savings": round(float(net_savings), 2),
        "difference": round(float(net_savings - goal_amount), 2),
        "on_track": bool(net_savings >= goal_amount),
    }


def forecast_end_of_month_balance(
    current_balance: float,
    df: pd.DataFrame | None = None,
) -> dict:
    """Project month-end balance from the latest month's recorded daily spending rate."""
    if df is None:
        df = load_transactions()

    latest_date = df["date"].max()
    month_expenses = df.loc[
        (df["transaction_type"] == "expense")
        & (df["date"].dt.to_period("M") == latest_date.to_period("M")),
        "amount",
    ].sum()
    days_in_month = latest_date.days_in_month
    days_elapsed = latest_date.day
    days_remaining = days_in_month - days_elapsed
    daily_spend = (
        Decimal(f"{month_expenses:.2f}") / Decimal(days_elapsed)
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    projected_remaining_spend = (
        daily_spend * Decimal(days_remaining)
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    forecast_balance = (
        Decimal(f"{current_balance:.2f}") - projected_remaining_spend
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "as_of_date": latest_date.date().isoformat(),
        "current_balance": round(float(current_balance), 2),
        "daily_spend_rate": float(daily_spend),
        "days_remaining": int(days_remaining),
        "projected_remaining_spend": float(projected_remaining_spend),
        "forecast_balance": float(forecast_balance),
        "assumption": "Spending continues at the latest month's recorded daily expense rate; future income and transfers are excluded.",
    }

def get_spending_by_category(
    category: str | None = None,
    month: str | None = None,
    df: pd.DataFrame | None = None,
) -> dict:
    if df is None:
        df = load_transactions()

    expenses = df[df["transaction_type"] == "expense"].copy()

    if category:
        expenses = expenses[
            expenses["category"].str.lower() == category.lower()
        ]

    if month:
        data_start = df["date"].min().date()
        data_end = df["date"].max().date()

        requested_month = pd.Period(month, freq="M")
        data_start_month = pd.Period(data_start, freq="M")
        data_end_month = pd.Period(data_end, freq="M")

        if requested_month < data_start_month or requested_month > data_end_month:
            return {
                "category": category,
                "month": month,
                "available": False,
                "reason": "requested month is outside available transaction data",
                "data_start": data_start.isoformat(),
                "data_end": data_end.isoformat(),
            }

        expenses = expenses[
            expenses["date"].dt.to_period("M").astype(str) == month
        ]

    total = expenses["amount"].sum()

    return {
        "category": category,
        "month": month,
        "available": True,
        "total": round(float(total), 2),
        "transaction_count": int(len(expenses)),
    }

def get_top_categories(
    limit: int = 5,
    month: str | None = None,
    df: pd.DataFrame | None = None,
) -> list[dict] | dict:
    if df is None:
        df = load_transactions()

    expenses = df[df["transaction_type"] == "expense"].copy()

    if month:
        data_start = df["date"].min().date()
        data_end = df["date"].max().date()
        requested_month = pd.Period(month, freq="M")
        data_start_month = pd.Period(data_start, freq="M")
        data_end_month = pd.Period(data_end, freq="M")

        if requested_month < data_start_month or requested_month > data_end_month:
            return {
                "month": month,
                "available": False,
                "reason": "requested month is outside available transaction data",
                "data_start": data_start.isoformat(),
                "data_end": data_end.isoformat(),
            }

        expenses = expenses[
            expenses["date"].dt.to_period("M").astype(str) == month
        ]

    result = (
        expenses.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
        .head(limit)
    )

    return [
        {
            "category": row["category"],
            "total": round(float(row["amount"]), 2),
        }
        for _, row in result.iterrows()
    ]

def get_top_merchants(
    limit: int = 5,
    df: pd.DataFrame | None = None,
) -> list[dict]:
    if df is None:
        df = load_transactions()

    expenses = df[df["transaction_type"] == "expense"].copy()

    result = (
        expenses.groupby("merchant", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
        .head(limit)
    )

    return [
        {
            "merchant": row["merchant"],
            "total": round(float(row["amount"]), 2),
        }
        for _, row in result.iterrows()
    ]


def get_transaction_categories(
    df: pd.DataFrame | None = None,
) -> dict:
    """Return the dataset's current category and subcategory vocabulary."""
    if df is None:
        df = load_transactions()

    return {
        "categories": sorted(df["category"].dropna().unique().tolist()),
        "subcategories": sorted(df["subcategory"].dropna().unique().tolist()),
    }


def list_transactions(
    category: str | None = None,
    subcategory: str | None = None,
    merchant: str | None = None,
    month: str | None = None,
    include_logo: bool = False,
    return_all: bool = False,
    limit: int = 25,
    df: pd.DataFrame | None = None,
) -> dict:
    """List transactions using only metadata-driven filters from the dataset."""
    if df is None:
        df = load_transactions()

    filtered = df.copy()

    for column, value in (
        ("category", category),
        ("subcategory", subcategory),
        ("merchant", merchant),
    ):
        if value:
            filtered = filtered[
                filtered[column].str.casefold() == value.casefold()
            ]

    if month:
        filtered = filtered[
            filtered["date"].dt.to_period("M").astype(str) == month
        ]

    filtered = filtered.sort_values("date", ascending=False)
    total_matches = int(len(filtered))

    if not return_all:
        filtered = filtered.head(max(1, min(limit, 100)))

    transactions = []
    for _, row in filtered.iterrows():
        transaction = {
            "merchant": row["merchant"],
            "date": row["date"].strftime("%Y-%m-%d"),
            "amount": round(float(row["amount"]), 2),
            "category": row["category"],
            "subcategory": row["subcategory"],
            "transaction_type": row["transaction_type"],
        }
        if include_logo:
            transaction["logo_url"] = (
                row["logo_url"] if pd.notna(row["logo_url"]) else None
            )
        transactions.append(transaction)

    return {
        "filters": {
            "category": category,
            "subcategory": subcategory,
            "merchant": merchant,
            "month": month,
        },
        "total_matches": total_matches,
        "returned_count": int(len(transactions)),
        "include_logo": include_logo,
        "transactions": transactions,
    }

def get_transactions_by_merchant(
    merchant: str,
    df: pd.DataFrame | None = None,
) -> dict:
    if df is None:
        df = load_transactions()

    matches = df[
        df["merchant"].str.lower() == merchant.lower()
    ].copy()

    if matches.empty:
        return {
            "merchant": merchant,
            "available": False,
            "transaction_count": 0,
            "transactions": [],
        }

    transactions = matches[
        ["date", "amount", "category", "subcategory", "transaction_type"]
    ].copy()

    transactions["date"] = transactions["date"].dt.strftime("%Y-%m-%d")

    return {
        "merchant": merchant,
        "available": True,
        "transaction_count": len(transactions),
        "transactions": transactions.to_dict(orient="records"),
    }

def get_recurring_expenses(
    df: pd.DataFrame | None = None,
) -> list[dict]:
    if df is None:
        df = load_transactions()

    subscriptions = df[
        (df["transaction_type"] == "expense") &
        (df["is_recurring"] == True)
    ].copy()

    result = (
        subscriptions.groupby("merchant", as_index=False)
        .agg(
            total=("amount", "sum"),
            transaction_count=("amount", "count"),
        )
        .sort_values("total", ascending=False)
    )

    return [
        {
            "merchant": row["merchant"],
            "total": round(float(row["total"]), 2),
            "transaction_count": int(row["transaction_count"]),
        }
        for _, row in result.iterrows()
    ]

def get_spending_by_month(
    df: pd.DataFrame | None = None,
) -> list[dict]:
    if df is None:
        df = load_transactions()

    expenses = df[df["transaction_type"] == "expense"].copy()

    expenses["month"] = expenses["date"].dt.to_period("M").astype(str)

    result = (
        expenses.groupby("month", as_index=False)["amount"]
        .sum()
        .sort_values("month")
    )

    return [
        {
            "month": row["month"],
            "total": round(float(row["amount"]), 2),
        }
        for _, row in result.iterrows()
    ]

def compare_periods(
    period_1: str,
    period_2: str,
    df: pd.DataFrame | None = None,
) -> dict:
    if df is None:
        df = load_transactions()

    expenses = df[df["transaction_type"] == "expense"].copy()
    expenses["month"] = expenses["date"].dt.to_period("M").astype(str)

    period_1_total = expenses.loc[
        expenses["month"] == period_1, "amount"
    ].sum()

    period_2_total = expenses.loc[
        expenses["month"] == period_2, "amount"
    ].sum()

    difference = period_1_total - period_2_total

    if period_2_total != 0:
        percentage_change = (difference / period_2_total) * 100
    else:
        percentage_change = None

    return {
        "period_1": period_1,
        "period_1_total": round(float(period_1_total), 2),
        "period_2": period_2,
        "period_2_total": round(float(period_2_total), 2),
        "difference": round(float(difference), 2),
        "percentage_change": (
            round(float(percentage_change), 2)
            if percentage_change is not None
            else None
        ),
    }

def get_average_weekly_spend(
    category: str | None = None,
    df: pd.DataFrame | None = None,
) -> dict:
    if df is None:
        df = load_transactions()

    expenses = df[df["transaction_type"] == "expense"].copy()

    if category:
        expenses = expenses[
            expenses["category"].str.lower() == category.lower()
        ]

    if expenses.empty:
        return {
            "category": category,
            "average_weekly_spend": 0.0,
            "weeks": 0,
        }

    expenses["week"] = expenses["date"].dt.to_period("W")

    weekly_totals = expenses.groupby("week")["amount"].sum()

    average = weekly_totals.mean()

    return {
        "category": category,
        "average_weekly_spend": round(float(average), 2),
        "weeks": int(len(weekly_totals)),
    }

def detect_duplicates(
    df: pd.DataFrame | None = None,
) -> list[dict]:
    if df is None:
        df = load_transactions()

    expenses = df[df["transaction_type"] == "expense"].copy()

    duplicates = expenses[
        expenses.duplicated(
            subset=["merchant", "amount", "date"],
            keep=False,
        )
    ].copy()

    if duplicates.empty:
        return []

    duplicates = duplicates.sort_values(
        ["date", "merchant", "amount"]
    )

    return [
        {
            "date": row["date"].strftime("%Y-%m-%d"),
            "merchant": row["merchant"],
            "amount": round(float(row["amount"]), 2),
        }
        for _, row in duplicates.iterrows()
    ]


def get_spending_to_income_ratio(
    categories: list[str],
    month: str | None = None,
    df: pd.DataFrame | None = None,
) -> dict:
    if df is None:
        df = load_transactions()

    # Check whether requested month is within available data
    if month:
        data_start = df["date"].min().date()
        data_end = df["date"].max().date()

        requested_month = pd.Period(month, freq="M")
        data_start_month = pd.Period(data_start, freq="M")
        data_end_month = pd.Period(data_end, freq="M")

        if requested_month < data_start_month or requested_month > data_end_month:
            return {
                "categories": categories,
                "month": month,
                "available": False,
                "reason": "requested month is outside available transaction data",
                "data_start": data_start.isoformat(),
                "data_end": data_end.isoformat(),
            }

    # Validate categories
    available_categories = set(
        df.loc[df["transaction_type"] == "expense", "category"]
    )

    invalid_categories = [
        category
        for category in categories
        if category not in available_categories
    ]

    if invalid_categories:
        return {
            "categories": categories,
            "month": month,
            "available": False,
            "reason": "invalid spending category",
            "invalid_categories": invalid_categories,
            "available_categories": sorted(available_categories),
        }

    # Filter to requested month if provided
    filtered = df.copy()

    if month:
        filtered = filtered[
            filtered["date"].dt.to_period("M").astype(str) == month
        ]

    # Find recorded income
    income = filtered[
        filtered["transaction_type"] == "income"
    ]

    # If no month was specified, check income coverage
    if month is None:
        income_months = sorted(
            df.loc[df["transaction_type"] == "income", "date"]
            .dt.to_period("M")
            .astype(str)
            .unique()
        )

        # Sparse income data makes a full-period ratio misleading
        if len(income_months) < 3:
            return {
                "categories": categories,
                "month": None,
                "available": False,
                "reason": "insufficient income coverage",
                "income_months": income_months,
                "income_transaction_count": int(len(income)),
            }

    total_income = income["amount"].sum()

    # Calculate spending for requested categories
    spending = filtered[
        (filtered["transaction_type"] == "expense")
        & (filtered["category"].isin(categories))
    ]

    total_spending = spending["amount"].sum()

    if total_income == 0:
        return {
            "categories": categories,
            "month": month,
            "available": False,
            "reason": "no recorded income for the requested period",
        }

    percentage = (total_spending / total_income) * 100

    return {
        "categories": categories,
        "month": month,
        "available": True,
        "income": round(float(total_income), 2),
        "spending": round(float(total_spending), 2),
        "percentage": round(float(percentage), 2),
        "income_transaction_count": int(len(income)),
        "spending_transaction_count": int(len(spending)),
    }

def detect_anomalies(
    threshold: float = 2.0,
    df: pd.DataFrame | None = None,
) -> list[dict]:
    if df is None:
        df = load_transactions()

    expenses = df[df["transaction_type"] == "expense"].copy()

    if expenses.empty:
        return []

    mean = expenses["amount"].mean()
    std = expenses["amount"].std()

    if std == 0:
        return []

    expenses["z_score"] = (
        (expenses["amount"] - mean) / std
    )

    anomalies = expenses[
        expenses["z_score"] >= threshold
    ].copy()

    anomalies = anomalies.sort_values(
        "amount",
        ascending=False,
    )

    return [
        {
            "date": row["date"].strftime("%Y-%m-%d"),
            "merchant": row["merchant"],
            "category": row["category"],
            "amount": round(float(row["amount"]), 2),
            "z_score": round(float(row["z_score"]), 2),
        }
        for _, row in anomalies.iterrows()
    ]
