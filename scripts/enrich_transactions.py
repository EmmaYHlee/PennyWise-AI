#!/usr/bin/env python3
"""Validate and enrich PennyWise's raw transaction export.

The raw export contains unsigned amounts, so transaction direction is derived
from well-defined transaction semantics rather than from the amount column.
By default the script uses the local, controlled merchant taxonomy.  Pass
``--use-llm`` to let OpenAI refine classifications; each response is validated
against that same taxonomy before it is accepted.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "sample_transactions.csv"
OUTPUT_PATH = ROOT / "data" / "enriched_transactions.csv"
PROFILE_PATH = ROOT / "data" / "data_profile.json"
REQUIRED_COLUMNS = ("transaction_description", "amount", "date")

# A controlled taxonomy keeps downstream analytics stable.  The values are the
# only category/subcategory pairs that may appear in the output.
TAXONOMY = {
    "Housing": {"Home Improvement", "Furniture"},
    "Groceries": {"Grocery Store", "Warehouse Club"},
    "Dining": {"Restaurant", "Coffee", "Fast Food", "Delivery"},
    "Transportation": {"Rideshare", "Public Transit", "Rail", "Gas", "Parking"},
    "Entertainment": {"Movies", "Events", "Gaming", "Streaming"},
    "Healthcare": {"Pharmacy", "Medical"},
    "Shopping": {"General Retail", "Clothing", "Electronics", "Online Retail"},
    "Utilities": {"Electricity", "Gas Utility", "Mobile & Internet", "Taxes"},
    "Insurance": {"Insurance"},
    "Subscriptions": {"Software", "Digital Services", "Membership"},
    "Banking Fees": {"Transfer Fee", "Card Fee", "Late Fee", "Overdraft Fee", "ATM Fee", "Account Fee", "Foreign Transaction Fee"},
    "Transfers": {"Bank Transfer", "Peer-to-Peer Transfer"},
    "Income": {"Payroll"},
    "Giving": {"Charity"},
    "Other": {"Unclassified"},
}

# Rules are intentionally deterministic and ordered from specific to broad.
RULES: Tuple[Tuple[Tuple[str, ...], str, str, str, bool], ...] = (
    (("PAYROLL DEPOSIT",), "Payroll Deposit", "Income", "Payroll", "income", False),
    (("WIRE TRANSFER FEE",), "Wire Transfer Fee", "Banking Fees", "Transfer Fee", "expense", False),
    (("FOREIGN TRANSACTION FEE",), "Foreign Transaction Fee", "Banking Fees", "Foreign Transaction Fee", "expense", False),
    (("ATM WITHDRAWAL FEE",), "ATM Withdrawal Fee", "Banking Fees", "ATM Fee", "expense", False),
    (("LATE PAYMENT FEE",), "Late Payment Fee", "Banking Fees", "Late Fee", "expense", False),
    (("OVERDRAFT FEE",), "Overdraft Fee", "Banking Fees", "Overdraft Fee", "expense", False),
    (("NSF FEE",), "NSF Fee", "Banking Fees", "Overdraft Fee", "expense", False),
    (("ANNUAL CARD FEE",), "Annual Card Fee", "Banking Fees", "Card Fee", "expense", False),
    (("PAPER STATEMENT FEE",), "Paper Statement Fee", "Banking Fees", "Account Fee", "expense", False),
    (("MONTHLY MAINTENANCE FEE",), "Monthly Maintenance Fee", "Banking Fees", "Account Fee", "expense", False),
    (("WALMART PHARMACY",), "Walmart Pharmacy", "Healthcare", "Pharmacy", "expense", False),
    (("WALMART GROCERY",), "Walmart", "Groceries", "Grocery Store", "expense", False),
    (("TARGET GROCERY",), "Target", "Groceries", "Grocery Store", "expense", False),
    (("CVS/PHARMACY", "WALGREENS", "RITE AID", "REXALL", "SHOPPERS DRUG MART", "GOODRX", "KAISER PERMANENTE RX", "PHARMACA"), "Pharmacy", "Healthcare", "Pharmacy", "expense", False),
    (("NETFLIX", "HULU", "DISNEY PLUS", "PARAMOUNT+", "HBO MAX"), "Streaming Service", "Entertainment", "Streaming", "expense", True),
    (("SPOTIFY", "AUDIBLE", "YOUTUBEPREMIUM"), "Digital Media", "Subscriptions", "Digital Services", "expense", True),
    (("ADOBE", "MICROSOFT*M365", "CHATGPT SUBSCRIPTION", "APPLE.COM/BILL"), "Software Service", "Subscriptions", "Software", "expense", True),
    (("AMAZON PRIME",), "Amazon Prime", "Subscriptions", "Membership", "expense", True),
    (("XBOX",), "Gaming Service", "Entertainment", "Gaming", "expense", True),
    (("PLAYSTATION", "NINTENDO", "STEAMGAMES", "GOOGLE *PLAY"), "Gaming Service", "Entertainment", "Gaming", "expense", False),
    (("UBER EATS", "DOORDASH"), "Food Delivery", "Dining", "Delivery", "expense", False),
    (("UBER *TRIP", "LYFT *RIDE"), "Rideshare", "Transportation", "Rideshare", "expense", False),
    (("MTA NYC TRANSIT",), "MTA", "Transportation", "Public Transit", "expense", False),
    (("AMTRAK", "VIA RAIL"), "Rail Travel", "Transportation", "Rail", "expense", False),
    (("SHELL OIL", "EXXONMOBIL", "ESSO", "CHEVRON", "PETRO-CANADA"), "Fuel Station", "Transportation", "Gas", "expense", False),
    (("PARKING METER",), "Parking Meter", "Transportation", "Parking", "expense", False),
    (("CON EDISON",), "Con Edison", "Utilities", "Electricity", "expense", True),
    (("NATIONAL GRID GAS",), "National Grid", "Utilities", "Gas Utility", "expense", True),
    (("AT&T", "VERIZON", "T-MOBILE", "BELL CANADA", "ROGERS COMM"), "Telecom Provider", "Utilities", "Mobile & Internet", "expense", True),
    (("GEICO", "STATE FARM"), "Insurance Provider", "Insurance", "Insurance", "expense", True),
    (("IRS USATAXPYMT",), "IRS", "Utilities", "Taxes", "expense", False),
    (("TRANSFER TO CHECKING", "WIRE TRANSFER", "WISE TRANSFER", "ZELLE TRANSFER", "INTERAC E-TRANSFER", "WESTERN UNION"), "Bank Transfer", "Transfers", "Bank Transfer", "transfer", False),
    (("VENMO", "PAYPAL *TRANSFER", "CASH APP", "APPLE CASH SEND"), "Peer-to-Peer Transfer", "Transfers", "Peer-to-Peer Transfer", "transfer", False),
    (("AMERICAN RED CROSS",), "American Red Cross", "Giving", "Charity", "expense", False),
    (("AMC THEATRES", "REGAL CINEMAS", "CINEPLEX"), "Cinema", "Entertainment", "Movies", "expense", False),
    (("TICKETMASTER", "STUBHUB", "LIVE NATION", "DAVE & BUSTERS"), "Events & Attractions", "Entertainment", "Events", "expense", False),
    (("WHOLE FOODS", "TRADER JOES", "ALDI", "COSTCO", "KROGER", "LOBLAWS", "SOBEYS", "PUBLIX", "SAFEWAY"), "Grocery Store", "Groceries", "Grocery Store", "expense", False),
    (("STARBUCKS", "DUNKIN", "TIM HORTONS"), "Coffee Shop", "Dining", "Coffee", "expense", False),
    (("MCDONALDS", "SUBWAY", "CHICK-FIL-A", "TACO BELL"), "Fast Food", "Dining", "Fast Food", "expense", False),
    (("SHAKE SHACK", "CHIPOTLE"), "Restaurant", "Dining", "Restaurant", "expense", False),
    (("AMZN MKTP", "WAYFAIR"), "Online Retailer", "Shopping", "Online Retail", "expense", False),
    (("BEST BUY",), "Best Buy", "Shopping", "Electronics", "expense", False),
    (("NIKE", "ZARA", "H&M", "SHEIN", "MACYS"), "Clothing Retailer", "Shopping", "Clothing", "expense", False),
    (("LOWES", "THE HOME DEPOT"), "Home Improvement Store", "Housing", "Home Improvement", "expense", False),
    (("IKEA",), "IKEA", "Housing", "Furniture", "expense", False),
    (("CANADIAN TIRE", "TARGET "), "General Retailer", "Shopping", "General Retail", "expense", False),
)

# Merchant identity is deliberately more precise than the category rules above.
# Location and reference numbers are not part of the identity, which makes a
# merchant usable for recurring-charge and merchant-spending analysis.
MERCHANT_ALIASES = (
    ("WALMART PHARMACY", "Walmart Pharmacy"), ("WALMART GROCERY", "Walmart"),
    ("TARGET GROCERY", "Target"), ("AMZN MKTP", "Amazon"), ("AMAZON PRIME", "Amazon Prime"),
    ("KAISER PERMANENTE", "Kaiser Permanente"), ("SHOPPERS DRUG MART", "Shoppers Drug Mart"),
    ("CVS/PHARMACY", "CVS Pharmacy"), ("GOOGLE *PLAY", "Google Play"),
    ("MICROSOFT*M365", "Microsoft 365"), ("APPLE.COM/BILL", "Apple"),
    ("WIRE TRANSFER FEE", "Wire Transfer Fee"), ("WIRE TRANSFER", "Wire Transfer"),
    ("TRANSFER TO CHECKING", "Transfer to Checking"), ("PAYPAL *TRANSFER", "PayPal"),
    ("VENMO *PAYMENT", "Venmo"), ("CASH APP", "Cash App"), ("APPLE CASH SEND", "Apple Cash"),
    ("INTERAC E-TRANSFER", "Interac e-Transfer"), ("ZELLE TRANSFER", "Zelle"),
    ("WISE TRANSFER", "Wise"), ("WESTERN UNION", "Western Union"),
    ("NATIONAL GRID", "National Grid"), ("CON EDISON", "Con Edison"),
    ("STATE FARM", "State Farm"), ("GEICO", "GEICO"), ("AT&T", "AT&T"),
    ("VERIZON", "Verizon"), ("T-MOBILE", "T-Mobile"), ("BELL CANADA", "Bell Canada"),
    ("ROGERS COMM", "Rogers"), ("MTA NYC", "MTA"), ("UBER *TRIP", "Uber"),
    ("LYFT *RIDE", "Lyft"), ("UBER EATS", "Uber Eats"), ("DOORDASH", "DoorDash"),
    ("SHELL OIL", "Shell"), ("EXXONMOBIL", "ExxonMobil"), ("ESSO", "Esso"), ("PETRO-CANADA", "Petro-Canada"),
    ("CHEVRON", "Chevron"), ("NETFLIX", "Netflix"), ("DISNEY PLUS", "Disney+"), ("HULU", "Hulu"),
    ("PARAMOUNT+", "Paramount+"), ("HBO MAX", "HBO Max"), ("SPOTIFY", "Spotify"),
    ("AUDIBLE", "Audible"), ("YOUTUBEPREMIUM", "YouTube Premium"), ("ADOBE", "Adobe"),
    ("CHATGPT", "ChatGPT"), ("XBOX", "Xbox Game Pass"), ("PLAYSTATION", "PlayStation Network"),
    ("NINTENDO", "Nintendo"), ("STEAMGAMES", "Steam"), ("GOODRX", "GoodRx"),
    ("WALGREENS", "Walgreens"), ("RITE AID", "Rite Aid"), ("REXALL", "Rexall"),
    ("PHARMACA", "Pharmaca"), ("WHOLE FOODS", "Whole Foods"), ("TRADER JOES", "Trader Joe's"),
    ("COSTCO", "Costco"), ("KROGER", "Kroger"), ("LOBLAWS", "Loblaws"), ("SOBEYS", "Sobeys"),
    ("PUBLIX", "Publix"), ("SAFEWAY", "Safeway"), ("ALDI", "ALDI"), ("METRO ", "Metro"),
    ("STARBUCKS", "Starbucks"), ("DUNKIN", "Dunkin'"), ("TIM HORTONS", "Tim Hortons"),
    ("MCDONALDS", "McDonald's"), ("SUBWAY", "Subway"), ("CHICK-FIL-A", "Chick-fil-A"),
    ("TACO BELL", "Taco Bell"), ("SHAKE SHACK", "Shake Shack"), ("CHIPOTLE", "Chipotle"),
    ("AMC THEATRES", "AMC Theatres"), ("REGAL CINEMAS", "Regal Cinemas"), ("CINEPLEX", "Cineplex"),
    ("TICKETMASTER", "Ticketmaster"), ("STUBHUB", "StubHub"), ("LIVE NATION", "Live Nation"),
    ("DAVE & BUSTERS", "Dave & Buster's"), ("AMTRAK", "Amtrak"), ("VIA RAIL", "VIA Rail"),
    ("BEST BUY", "Best Buy"), ("WAYFAIR", "Wayfair"), ("NIKE", "Nike"), ("ZARA", "Zara"),
    ("H&M", "H&M"), ("SHEIN", "SHEIN"), ("MACYS", "Macy's"), ("LOWES", "Lowe's"),
    ("THE HOME DEPOT", "The Home Depot"), ("IKEA", "IKEA"), ("CANADIAN TIRE", "Canadian Tire"),
    ("TARGET ", "Target"), ("IRS USATAXPYMT", "IRS"), ("AMERICAN RED CROSS", "American Red Cross"),
    ("FOREIGN TRANSACTION FEE", "Foreign Transaction Fee"), ("ATM WITHDRAWAL FEE", "ATM Withdrawal Fee"),
    ("LATE PAYMENT FEE", "Late Payment Fee"), ("OVERDRAFT FEE", "Overdraft Fee"),
    ("NSF FEE", "NSF Fee"), ("ANNUAL CARD FEE", "Annual Card Fee"),
    ("PAPER STATEMENT FEE", "Paper Statement Fee"), ("MONTHLY MAINTENANCE FEE", "Monthly Maintenance Fee"),
    ("PAYROLL DEPOSIT", "Payroll Deposit"), ("PARKING METER", "Parking Meter"),
)

# Public-facing merchant domains used to enrich the local dataset.  Logo URLs
# are generated from these domains rather than hard-coded image files, keeping
# the dataset lightweight and the presentation layer provider-independent.
LOGO_DOMAINS = {
    "ALDI": "aldi.us", "AMC Theatres": "amctheatres.com", "AT&T": "att.com", "Adobe": "adobe.com",
    "Amazon": "amazon.com", "Amazon Prime": "amazon.com", "American Red Cross": "redcross.org",
    "Amtrak": "amtrak.com", "Apple": "apple.com", "Apple Cash": "apple.com", "Audible": "audible.com",
    "Bell Canada": "bell.ca", "Best Buy": "bestbuy.com", "CVS Pharmacy": "cvs.com", "Canadian Tire": "canadiantire.ca",
    "Cash App": "cash.app", "ChatGPT": "openai.com", "Chevron": "chevron.com", "Chick-fil-A": "chick-fil-a.com",
    "Chipotle": "chipotle.com", "Cineplex": "cineplex.com", "Con Edison": "coned.com", "Costco": "costco.com",
    "Dave & Buster's": "daveandbusters.com", "Disney+": "disneyplus.com", "DoorDash": "doordash.com", "Dunkin'": "dunkindonuts.com",
    "Esso": "esso.ca", "ExxonMobil": "exxonmobil.com", "GEICO": "geico.com", "GoodRx": "goodrx.com",
    "Google Play": "play.google.com", "H&M": "hm.com", "HBO Max": "max.com", "Hulu": "hulu.com", "IKEA": "ikea.com",
    "IRS": "irs.gov", "Kaiser Permanente": "kaiserpermanente.org", "Kroger": "kroger.com", "Live Nation": "livenationentertainment.com",
    "Loblaws": "loblaws.ca", "Lowe's": "lowes.com", "Lyft": "lyft.com", "MTA": "mta.info", "Macy's": "macys.com",
    "McDonald's": "mcdonalds.com", "Metro": "metro.ca", "Microsoft 365": "microsoft.com", "National Grid": "nationalgridus.com",
    "Netflix": "netflix.com", "Nike": "nike.com", "Nintendo": "nintendo.com", "Paramount+": "paramountplus.com",
    "PayPal": "paypal.com", "Petro-Canada": "petro-canada.ca", "Pharmaca": "pharmacarx.com", "PlayStation Network": "playstation.com",
    "Publix": "publix.com", "Regal Cinemas": "regmovies.com", "Rexall": "rexall.ca", "Rite Aid": "riteaid.com",
    "Rogers": "rogers.com", "Safeway": "safeway.com", "SHEIN": "shein.com", "Shake Shack": "shakeshack.com",
    "Shell": "shell.com", "Shoppers Drug Mart": "shoppersdrugmart.ca", "Sobeys": "sobeys.com", "Spotify": "spotify.com",
    "Starbucks": "starbucks.com", "State Farm": "statefarm.com", "Steam": "steampowered.com", "StubHub": "stubhub.com",
    "Subway": "subway.com", "T-Mobile": "t-mobile.com", "Taco Bell": "tacobell.com", "Target": "target.com",
    "The Home Depot": "homedepot.com", "Ticketmaster": "ticketmaster.com", "Tim Hortons": "timhortons.com",
    "Trader Joe's": "traderjoes.com", "Uber": "uber.com", "Uber Eats": "ubereats.com", "VIA Rail": "viarail.ca",
    "Venmo": "venmo.com", "Verizon": "verizon.com", "Walgreens": "walgreens.com", "Walmart": "walmart.com",
    "Walmart Pharmacy": "walmart.com", "Wayfair": "wayfair.com", "Western Union": "westernunion.com", "Whole Foods": "wholefoodsmarket.com",
    "Wise": "wise.com", "Xbox Game Pass": "xbox.com", "YouTube Premium": "youtube.com", "Zara": "zara.com", "Zelle": "zellepay.com",
}


def logo_metadata(merchant: str) -> Dict[str, str]:
    domain = LOGO_DOMAINS.get(merchant, "")
    return {
        "merchant_domain": domain,
        "logo_url": f"https://logos.hunter.io/{domain}" if domain else "",
    }


def validate_raw(df: pd.DataFrame) -> None:
    missing = set(REQUIRED_COLUMNS).difference(df.columns)
    if missing:
        raise ValueError(f"Raw CSV is missing required columns: {', '.join(sorted(missing))}")
    if df["transaction_description"].isna().any() or not df["transaction_description"].astype(str).str.strip().all():
        raise ValueError("Raw CSV contains blank transaction descriptions.")
    amounts = pd.to_numeric(df["amount"], errors="coerce")
    if amounts.isna().any():
        raise ValueError("Raw CSV contains non-numeric amounts.")
    if pd.to_datetime(df["date"], errors="coerce").isna().any():
        raise ValueError("Raw CSV contains unparseable dates.")
    duplicates = int(df.duplicated(subset=list(REQUIRED_COLUMNS)).sum())
    if duplicates:
        raise ValueError(f"Raw CSV contains {duplicates} duplicate source rows.")


def normalize_description(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip())


def classify(description: str) -> Dict[str, Any]:
    upper = description.upper()
    # "Metro" may be a grocery banner or a transit provider.  The synthetic
    # export identifies grocery receipts by store number plus city/province;
    # do not apply the grocery rule to a bare or transit-like Metro string.
    if upper.startswith("METRO "):
        grocery_context = re.compile(r"^METRO\s+\d{2,5}\s+(?:ATLANTA GA|EDMONTON AB|MONTREAL QC|OTTAWA ON)$")
        if grocery_context.match(upper):
            return {"merchant": "Metro", "category": "Groceries", "subcategory": "Grocery Store",
                    "transaction_type": "expense", "is_recurring": False, "_recurrence_candidate": False}
        return {"merchant": "Metro", "category": "Other", "subcategory": "Unclassified",
                "transaction_type": "expense", "is_recurring": False, "_recurrence_candidate": False}
    for keywords, merchant, category, subcategory, transaction_type, recurring in RULES:
        if any(keyword in upper for keyword in keywords):
            canonical_merchant = next((name for keyword, name in MERCHANT_ALIASES if keyword in upper), merchant)
            return {"merchant": canonical_merchant, "category": category, "subcategory": subcategory,
                    "transaction_type": transaction_type, "is_recurring": False, "_recurrence_candidate": recurring}
    return {"merchant": "Unknown Merchant", "category": "Other", "subcategory": "Unclassified",
            "transaction_type": "expense", "is_recurring": False, "_recurrence_candidate": False}


def valid_enrichment(item: Dict[str, Any]) -> bool:
    return (isinstance(item.get("merchant"), str) and bool(item["merchant"].strip())
            and item.get("category") in TAXONOMY
            and item.get("subcategory") in TAXONOMY[item["category"]]
            and item.get("transaction_type") in {"income", "expense", "transfer"}
            and isinstance(item.get("is_recurring"), bool))


def llm_enrich(description: str, fallback: Dict[str, Any], client: Any) -> Dict[str, Any]:
    schema = {category: sorted(subcategories) for category, subcategories in TAXONOMY.items()}
    prompt = ("Classify this bank transaction using only the supplied taxonomy. Return JSON with "
              "merchant, category, subcategory, transaction_type (income|expense|transfer), and is_recurring. "
              f"Taxonomy: {json.dumps(schema)}. Transaction: {description!r}")
    for _ in range(2):
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "system", "content": "Return only valid JSON."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}, temperature=0,
        )
        try:
            result = json.loads(response.choices[0].message.content)
        except (json.JSONDecodeError, AttributeError, IndexError):
            continue
        if valid_enrichment(result):
            return result
    return fallback


def recurrence_from_history(records: Iterable[Dict[str, Any]]) -> Dict[str, Tuple[bool, float]]:
    """Return recurrence decisions supported by merchant history, not repetition alone."""
    transactions: Dict[str, list[Tuple[pd.Timestamp, float]]] = {}
    candidates: Dict[str, bool] = {}
    for record in records:
        transactions.setdefault(record["merchant"], []).append((pd.Timestamp(record["date"]), float(record["amount"])))
        candidates[record["merchant"]] = bool(record["_recurrence_candidate"])
    decisions = {}
    for merchant, merchant_transactions in transactions.items():
        ordered = sorted(merchant_transactions)
        repeated = len(ordered) >= 2
        regular = any(20 <= (later_date - earlier_date).days <= 40
                      and abs(later_amount - earlier_amount) <= max(1.0, earlier_amount * 0.10)
                      for (earlier_date, earlier_amount), (later_date, later_amount) in zip(ordered, ordered[1:]))
        if candidates[merchant] and regular:
            decisions[merchant] = (True, 0.98)
        elif candidates[merchant] and repeated:
            decisions[merchant] = (True, 0.85)
        elif candidates[merchant]:
            decisions[merchant] = (False, 0.70)
        else:
            # A repeat at a pharmacy, grocer, or retailer is specifically not
            # enough evidence to call it a recurring charge.
            decisions[merchant] = (False, 0.95 if repeated else 0.90)
    return decisions


def make_profile(df: pd.DataFrame) -> Dict[str, Any]:
    normalized = df["transaction_description"].map(normalize_description)
    return {
        "total_transactions": int(len(df)),
        "date_range": {"start": str(df["date"].min().date()), "end": str(df["date"].max().date())},
        "amounts": {"minimum": float(df["amount"].min()), "maximum": float(df["amount"].max()),
                    "positive": int((df["amount"] > 0).sum()), "negative": int((df["amount"] < 0).sum())},
        "duplicate_source_rows": int(df.duplicated(subset=list(REQUIRED_COLUMNS)).sum()),
        "repeated_descriptions": {key: int(value) for key, value in Counter(normalized).most_common(10) if value > 1},
        "amount_sign_convention": "All amounts are positive; sign cannot determine transaction type.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RAW_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--use-llm", action="store_true", help="Refine each classification with OpenAI after validation.")
    args = parser.parse_args()
    raw = pd.read_csv(args.input)
    validate_raw(raw)
    raw["amount"] = pd.to_numeric(raw["amount"])
    raw["date"] = pd.to_datetime(raw["date"], errors="raise")
    raw["transaction_description"] = raw["transaction_description"].map(normalize_description)
    profile = make_profile(raw)

    client = None
    if args.use_llm:
        from dotenv import load_dotenv
        from openai import OpenAI
        load_dotenv(ROOT / ".env")
        if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "").startswith("your_"):
            raise ValueError("--use-llm requires a valid OPENAI_API_KEY in .env.")
        client = OpenAI()

    records = []
    for row in raw.to_dict("records"):
        enrichment = classify(row["transaction_description"])
        recurrence_candidate = enrichment["_recurrence_candidate"]
        if client:
            enrichment = llm_enrich(row["transaction_description"], enrichment, client)
            # Recurrence is derived only from the transaction history below.
            enrichment["_recurrence_candidate"] = recurrence_candidate
            enrichment["is_recurring"] = False
        if not valid_enrichment(enrichment):
            raise ValueError(f"Invalid enrichment for {row['transaction_description']!r}: {enrichment}")
        records.append({**row, **enrichment, **logo_metadata(enrichment["merchant"])})

    recurrence_decisions = recurrence_from_history(records)
    for record in records:
        record["is_recurring"], record["recurrence_confidence"] = recurrence_decisions[record["merchant"]]
    enriched = pd.DataFrame(records)
    enriched["date"] = enriched["date"].dt.strftime("%Y-%m-%d")
    required_output = [*REQUIRED_COLUMNS, "merchant", "merchant_domain", "logo_url", "category", "subcategory", "transaction_type", "is_recurring", "recurrence_confidence"]
    if enriched[required_output].isna().any().any() or len(enriched) != len(raw):
        raise ValueError("Enriched data failed final row-count or null validation.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    enriched[required_output].to_csv(args.output, index=False)
    PROFILE_PATH.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    print(f"Enriched {len(enriched)} transactions → {args.output}")
    print(f"Profile written → {PROFILE_PATH}")
    print("Transaction type is semantic because every source amount is positive.")
    print(enriched["category"].value_counts().to_string())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, pd.errors.ParserError) as error:
        print(f"Enrichment failed: {error}", file=sys.stderr)
        raise SystemExit(1)
