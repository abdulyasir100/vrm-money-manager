import json
import os
import threading
from datetime import datetime, timezone, timedelta
from models import Transaction, TransactionCreate, Settings

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "finance.json")
_lock = threading.Lock()

WIB_OFFSET = timedelta(hours=7)


def _ensure_data_dir():
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)


def _default_data() -> dict:
    return {
        "settings": {"currency": "IDR", "monthly_budget": 0},
        "transactions": [],
    }


def load() -> dict:
    _ensure_data_dir()
    if not os.path.exists(DATA_PATH):
        return _default_data()
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data: dict):
    _ensure_data_dir()
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


# --- Settings ---

def get_settings() -> Settings:
    with _lock:
        data = load()
    return Settings(**data.get("settings", {}))


def update_settings(currency: str | None = None, monthly_budget: int | None = None) -> Settings:
    with _lock:
        data = load()
        if currency is not None:
            data["settings"]["currency"] = currency
        if monthly_budget is not None:
            data["settings"]["monthly_budget"] = monthly_budget
        save(data)
        return Settings(**data["settings"])


# --- Transactions ---

def get_all(
    tx_type: str | None = None,
    category: str | None = None,
    month: str | None = None,  # "YYYY-MM"
) -> list[Transaction]:
    with _lock:
        raw = load()
    txs = [Transaction(**t) for t in raw.get("transactions", [])]

    if tx_type:
        txs = [t for t in txs if t.type == tx_type]
    if category:
        txs = [t for t in txs if t.category.lower() == category.lower()]
    if month:
        txs = [t for t in txs if t.created_at.strftime("%Y-%m") == month]

    return txs


def get_by_id(tx_id: str) -> Transaction | None:
    with _lock:
        raw = load()
    for t in raw.get("transactions", []):
        if t["id"] == tx_id:
            return Transaction(**t)
    return None


def create(data: TransactionCreate) -> Transaction:
    tx = Transaction(**data.model_dump())
    with _lock:
        raw = load()
        raw["transactions"].append(tx.model_dump())
        save(raw)
    return tx


def delete(tx_id: str) -> bool:
    with _lock:
        raw = load()
        txs = raw.get("transactions", [])
        new_txs = [t for t in txs if t["id"] != tx_id]
        if len(new_txs) == len(txs):
            return False
        raw["transactions"] = new_txs
        save(raw)
        return True


def clear_all():
    with _lock:
        data = load()
        data["transactions"] = []
        save(data)


# --- Aggregates ---

def _current_month_wib() -> str:
    now_wib = datetime.now(timezone.utc) + WIB_OFFSET
    return now_wib.strftime("%Y-%m")


def get_balance() -> dict:
    """Calculate total and monthly balance."""
    txs = get_all()
    settings = get_settings()
    month = _current_month_wib()

    total_income = sum(t.amount for t in txs if t.type == "income")
    total_expense = sum(t.amount for t in txs if t.type == "expense")

    monthly_txs = [t for t in txs if t.created_at.strftime("%Y-%m") == month]
    monthly_income = sum(t.amount for t in monthly_txs if t.type == "income")
    monthly_expense = sum(t.amount for t in monthly_txs if t.type == "expense")

    return {
        "balance": total_income - total_expense,
        "total_income": total_income,
        "total_expense": total_expense,
        "currency": settings.currency,
        "monthly_income": monthly_income,
        "monthly_expense": monthly_expense,
        "transaction_count": len(txs),
    }


def get_spending_status() -> dict:
    """Calculate spending percentage against monthly budget."""
    settings = get_settings()
    month = _current_month_wib()
    txs = get_all(month=month)
    monthly_expense = sum(t.amount for t in txs if t.type == "expense")

    budget = settings.monthly_budget
    if budget <= 0:
        return {
            "monthly_budget": 0,
            "monthly_expense": monthly_expense,
            "spent_percent": 0,
            "threshold": "ok",
            "currency": settings.currency,
        }

    percent = (monthly_expense / budget) * 100

    if percent >= 80:
        threshold = "critical"
    elif percent >= 50:
        threshold = "warning"
    else:
        threshold = "ok"

    return {
        "monthly_budget": budget,
        "monthly_expense": monthly_expense,
        "spent_percent": round(percent, 1),
        "threshold": threshold,
        "currency": settings.currency,
    }
