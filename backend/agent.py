import os
from calendar import month_name

from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend import tools
from datetime import date

load_dotenv()

MODEL_NAME = "gemini-3.6-flash"
CURRENT_DATE = date.today().isoformat()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="spending_by_category",
        description=(
            "Get total expense spending for a specific category, "
            "optionally filtered by month."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "category": types.Schema(
                    type="STRING",
                    description=(
                        "Spending category, such as Groceries, "
                        "Dining, Shopping, or Transportation."
                    ),
                ),
                "month": types.Schema(
                    type="STRING",
                    description=(
                        "Optional month in YYYY-MM format, "
                        "such as 2026-06."
                    ),
                ),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="top_categories",
        description="Get the highest-spending expense categories, optionally for a specific month.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "limit": types.Schema(
                    type="INTEGER",
                    description="Number of categories to return.",
                ),
                "month": types.Schema(
                    type="STRING",
                    description="Optional month in YYYY-MM format, such as 2026-04.",
                ),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="top_merchants",
        description="Get the merchants with the highest total spending.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "limit": types.Schema(
                    type="INTEGER",
                    description="Number of merchants to return.",
                ),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="transaction_categories",
        description=(
            "Get every category and subcategory currently available in the "
            "transaction dataset. Use this to resolve a natural-language "
            "filter before listing transactions."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={},
        ),
    ),
    types.FunctionDeclaration(
        name="list_transactions",
        description=(
            "List transactions matching exact dataset metadata. Set "
            "include_logo=true only when the user asks to see logos. Set "
            "return_all=true when the user asks for all matching transactions."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "category": types.Schema(type="STRING"),
                "subcategory": types.Schema(type="STRING"),
                "merchant": types.Schema(type="STRING"),
                "month": types.Schema(
                    type="STRING",
                    description="Optional YYYY-MM filter.",
                ),
                "include_logo": types.Schema(type="BOOLEAN"),
                "return_all": types.Schema(type="BOOLEAN"),
                "limit": types.Schema(type="INTEGER"),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="recurring_expenses",
        description="Get recurring expenses grouped by merchant.",
        parameters=types.Schema(
            type="OBJECT",
            properties={},
        ),
    ),
    types.FunctionDeclaration(
        name="spending_by_month",
        description="Get total expense spending for each month.",
        parameters=types.Schema(
            type="OBJECT",
            properties={},
        ),
    ),
    types.FunctionDeclaration(
        name="compare_spending",
        description="Compare total expense spending between two months.",
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "period_1": types.Schema(
                    type="STRING",
                    description="First month in YYYY-MM format.",
                ),
                "period_2": types.Schema(
                    type="STRING",
                    description="Second month in YYYY-MM format.",
                ),
            },
            required=["period_1", "period_2"],
        ),
    ),
    types.FunctionDeclaration(
        name="average_weekly_spend",
        description=(
            "Get average weekly expense spending overall "
            "or for a specific category."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "category": types.Schema(
                    type="STRING",
                    description="Optional spending category.",
                ),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="spending_to_income_ratio",
        description=(
            "Calculate what percentage of recorded income is spent on "
            "one or more spending categories."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "categories": types.Schema(
                    type="ARRAY",
                    items=types.Schema(
                        type="STRING",
                    ),
                    description=(
                        "One or more spending categories, such as "
                        "Groceries, Dining, Shopping, Housing, or Utilities."
                    ),
                ),
                "month": types.Schema(
                    type="STRING",
                    description="Optional month in YYYY-MM format.",
                ),
            },
            required=["categories"],
        ),
    ),
    types.FunctionDeclaration(
        name="duplicate_transactions",
        description="Find exact duplicate expense transactions.",
        parameters=types.Schema(
            type="OBJECT",
            properties={},
        ),
    ),
    types.FunctionDeclaration(
        name="unusual_transactions",
        description=(
            "Find unusually large expense transactions "
            "using a z-score threshold."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "threshold": types.Schema(
                    type="NUMBER",
                    description=(
                        "Z-score threshold for unusual transactions. "
                        "Default is 2.0."
                    ),
                ),
            },
        ),
    ),
    types.FunctionDeclaration(
        name="savings_goal_progress",
        description=(
            "Compare a user's monthly savings goal with recorded income minus expenses. "
            "Ask for the goal amount before calling this tool when it is missing."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={
                "goal_amount": types.Schema(
                    type="NUMBER",
                    description="The user's monthly savings goal in dollars.",
                ),
                "month": types.Schema(
                    type="STRING",
                    description="Optional month in YYYY-MM format.",
                ),
            },
            required=["goal_amount"],
        ),
    ),
    types.FunctionDeclaration(
        name="end_of_month_balance_forecast",
        description=(
            "Forecast the end-of-month balance using the latest recorded daily spending rate."
        ),
        parameters=types.Schema(
            type="OBJECT",
            properties={},
        ),
    ),
]


TOOLS = [
    types.Tool(
        function_declarations=TOOL_DECLARATIONS
    )
]

TOOL_FUNCTIONS = {
    "spending_by_category": tools.spending_by_category,
    "top_categories": tools.top_categories,
    "top_merchants": tools.top_merchants,
    "transaction_categories": tools.transaction_categories,
    "list_transactions": tools.list_transactions,
    "recurring_expenses": tools.recurring_expenses,
    "spending_by_month": tools.spending_by_month,
    "compare_spending": tools.compare_spending,
    "average_weekly_spend": tools.average_weekly_spend,
    "spending_to_income_ratio": tools.spending_to_income_ratio,
    "duplicate_transactions": tools.duplicate_transactions,
    "unusual_transactions": tools.unusual_transactions,
    "savings_goal_progress": tools.savings_goal_progress,
    "end_of_month_balance_forecast": tools.end_of_month_balance_forecast,
}


SYSTEM_PROMPT = f"""
You are PennyWise, a personal finance management assistant.

Your job is to help users understand their transaction spending.
Today is {CURRENT_DATE}.

Rules:
- Use the available financial tools whenever a question requires transaction data
  or numerical financial calculations.
- Always use a tool for transaction-specific numbers. Never answer from assumptions,
  memory, or estimation.
- Resolve relative dates such as "last month", "this month", and "last week"
  relative to {CURRENT_DATE}.
- Never guess or assume a date.
- Use the minimum number of tool calls necessary to answer the user's question.
- If one tool can answer the question, call only that tool.
- If a financial tool returns available=false, the requested period
  is outside the available transaction data.
- Do not interpret unavailable data as zero spending.
- Clearly tell the user that the requested data is unavailable and
  state the available data range when provided.
- Never invent or estimate values for unavailable periods.
- Do not call multiple tools when one tool already provides the required information.
- Do not make exploratory or redundant tool calls.
- Pass all relevant filters directly to the tool when possible.
  For example, if the user asks about groceries in June, call
  spending_by_category(category="Groceries", month="2026-06")
  rather than calling a general spending tool first.
- Once a tool has returned the information needed to answer the question,
  do not call another tool for the same information.
- For top-category questions limited to a month, call
  top_categories(limit=<requested count>, month=<requested YYYY-MM>) and give
  only the concise ranked summary. Do not call list_transactions or render a
  transaction list unless the user explicitly asks to see transactions.
- Never invent transaction amounts, spending totals, or financial data.
- Transfers are not spending and should not be included in expense calculations.
- Income is not spending.
- Do not perform financial actions such as transfers, payments, or account changes.
- If the available transaction data cannot answer a question, clearly say so.
- For spending-to-income questions without a specified month, check whether
  the available income data provides meaningful coverage.
- If the tool returns "insufficient income coverage", do not calculate or
  estimate a percentage.
- Explain which months contain recorded income and why a full-period percentage
  would be misleading.
- Offer to calculate the ratio for a month that contains recorded income.
- Never treat missing income records as zero income.
- Only use categories that exist in the available transaction data.
- For requests to list or show transactions using a natural-language category
  or subcategory (for example, "coffee shop visits"), first call
  transaction_categories. Match the request to the returned metadata, then call
  list_transactions with the exact matching category or subcategory value.
- Do not hard-code semantic mappings such as "coffee shop" to "Coffee".
- When a user asks for all matching transactions, call list_transactions with
  return_all=true. When they ask for logos, call it with include_logo=true.
- For a transaction-list response, briefly state the match count and let the UI
  render the returned transactions and optional logos. Do not repeat every row
  in prose.
Examples:
  - "food" or "food and dining" → ["Groceries", "Dining"]
  - "shopping" → ["Shopping"]
  - "housing and utilities" → ["Housing", "Utilities"]
  - "entertainment" → ["Entertainment"]
- The spending-to-income tool calculates the percentage deterministically;
  do not calculate the percentage yourself.
- Give concise, clear answers.
- When a user asks whether they are on track for a savings goal but has not
  provided the monthly goal amount, ask for that amount before calculating.
- If the previous assistant message asked for a savings goal and the user then
  replies with an amount, treat that amount as the monthly goal and call
  savings_goal_progress.
- For a savings-goal check, use savings_goal_progress. Explain that savings is
  calculated as recorded income minus expenses, state the month used, and do
  not treat a month without recorded income as a complete financial picture.
- For an end-of-month balance prediction, use end_of_month_balance_forecast
  and state the as-of date, projected balance, and that future income and
  transfers are excluded.
"""


def chat(message: str, history: list[dict] | None = None) -> dict:
    if history is None:
        history = []

    contents = []

    for item in history:
        contents.append(
            types.Content(
                role=item["role"],
                parts=[types.Part.from_text(text=item["content"])],
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)],
        )
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=TOOLS,
        ),
    )

    transaction_list_data = None
    top_categories_data = None
    top_categories_month = None
    called_functions = set()

    while response.function_calls:
        function_responses = []

        for function_call in response.function_calls:
            function_name = function_call.name
            function_args = dict(function_call.args or {})
            called_functions.add(function_name)

            print(f"[TOOL CALL] {function_name}: {function_args}")

            function = TOOL_FUNCTIONS.get(function_name)

            if function is None:
                raise ValueError(
                    f"Unknown tool requested by Gemini: {function_name}"
                )

            result = function(**function_args)

            if function_name == "list_transactions":
                transaction_list_data = result

            if function_name == "top_categories" and isinstance(result, list):
                top_categories_data = result
                top_categories_month = function_args.get("month")

            if isinstance(result, list):
                result = {"results": result}

            function_responses.append(
                types.Part.from_function_response(
                    name=function_name,
                    response=result,
                )
            )

        contents.extend([
            response.candidates[0].content,
            types.Content(
                role="user",
                parts=function_responses,
            ),
        ])

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=TOOLS,
            ),
        )

    if top_categories_data is not None and top_categories_month:
        year, month = top_categories_month.split("-", maxsplit=1)
        heading = (
            f"Your top {len(top_categories_data)} spending categories in "
            f"{month_name[int(month)]} {year} were:"
        )
        ranking = "\n".join(
            f"**{category['category']}:** ${category['total']:,.2f}"
            for category in top_categories_data
        )
        result = {"response": f"{heading}\n\n{ranking}"}
    else:
        result = {"response": response.text}
    if transaction_list_data is not None and "top_categories" not in called_functions:
        result.update({"type": "transaction_list", "data": transaction_list_data})
    return result
