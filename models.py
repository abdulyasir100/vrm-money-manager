from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid


class TransactionCreate(BaseModel):
    type: str = Field(pattern="^(income|expense)$")
    amount: int = Field(gt=0)
    description: str = ""
    category: str = ""


class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # "income" | "expense"
    amount: int
    description: str = ""
    category: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Balance(BaseModel):
    balance: int
    total_income: int
    total_expense: int
    currency: str
    monthly_income: int
    monthly_expense: int
    transaction_count: int


class Settings(BaseModel):
    currency: str = "IDR"
    monthly_budget: int = 0  # 0 = not set


class SpendingStatus(BaseModel):
    monthly_budget: int
    monthly_expense: int
    spent_percent: float  # 0-100+
    threshold: str  # "ok" | "warning" | "critical"
    currency: str
