import logging
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from models import Transaction, TransactionCreate, Balance, Settings, SpendingStatus
import store

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

app = FastAPI(title="Suisei Money Manager", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok", "service": "suisei-money-manager", "timestamp": datetime.now(timezone.utc).isoformat()}


# --- Balance & Status ---

@app.get("/balance", response_model=Balance)
def get_balance():
    return store.get_balance()


@app.get("/spending-status", response_model=SpendingStatus)
def spending_status():
    return store.get_spending_status()


# --- Settings ---

@app.get("/settings", response_model=Settings)
def get_settings():
    return store.get_settings()


@app.put("/settings", response_model=Settings)
def update_settings(data: Settings):
    return store.update_settings(currency=data.currency, monthly_budget=data.monthly_budget)


# --- Transactions ---

@app.get("/transactions")
def list_transactions(
    type: str | None = Query(None),
    category: str | None = Query(None),
    month: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    all_txs = store.get_all(tx_type=type, category=category, month=month)
    # Sort newest first
    all_txs.sort(key=lambda t: t.created_at, reverse=True)
    total = len(all_txs)
    start = (page - 1) * per_page
    items = all_txs[start:start + per_page]
    return {"items": items, "total": total, "page": page, "per_page": per_page}


@app.get("/transactions/{tx_id}", response_model=Transaction)
def get_transaction(tx_id: str):
    tx = store.get_by_id(tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


@app.post("/transactions", response_model=Transaction, status_code=201)
def create_transaction(data: TransactionCreate):
    return store.create(data)


@app.delete("/transactions/{tx_id}")
def delete_transaction(tx_id: str):
    if not store.delete(tx_id):
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}


# --- Dev ---

@app.post("/dev/reset")
def dev_reset():
    store.clear_all()
    return {"message": "All transactions cleared"}


@app.post("/dev/seed")
def dev_seed():
    store.clear_all()
    store.update_settings(monthly_budget=5_000_000)
    samples = [
        TransactionCreate(type="income", amount=5_000_000, description="Monthly salary", category="salary"),
        TransactionCreate(type="expense", amount=50_000, description="Nasi goreng", category="food"),
        TransactionCreate(type="expense", amount=150_000, description="Internet bill", category="bills"),
        TransactionCreate(type="expense", amount=35_000, description="GoFood lunch", category="food"),
        TransactionCreate(type="expense", amount=500_000, description="Steam game", category="entertainment"),
        TransactionCreate(type="expense", amount=25_000, description="Gorengan + es teh", category="food"),
    ]
    created = [store.create(s) for s in samples]
    return {"message": f"Seeded {len(created)} transactions", "ids": [t.id for t in created]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8802)
