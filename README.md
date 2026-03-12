# Money Manager

Simple income and expense tracker with a web dashboard. Built with FastAPI and vanilla JavaScript.

## Features

- **Track Expenses & Income** — amount, category, description, date
- **Categories** — food, transport, bills, salary, freelance, etc.
- **Daily & Monthly Summaries** — spending breakdowns by category
- **Balance Tracking** — running total of income minus expenses
- **Pagination** — server-side pagination for transaction history
- **Dashboard** — visual summary with category breakdown

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run
uvicorn main:app --host 0.0.0.0 --port 8802
```

Open `http://localhost:8802` in your browser.

## Docker

```bash
docker build -t money-manager .
docker run -p 8802:8802 money-manager
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/transactions` | List transactions (supports pagination) |
| `POST` | `/transactions` | Add transaction |
| `DELETE` | `/transactions/{id}` | Delete transaction |
| `GET` | `/summary` | Balance + category breakdown |
| `GET` | `/summary/daily` | Today's spending |
| `GET` | `/summary/monthly` | This month's spending |

## Storage

JSON file storage in `data/finance.json` (auto-created). No database required.

## License

MIT
