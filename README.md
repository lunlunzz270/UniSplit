# UniSplit

A multi-currency expense sharing and ledger management web application built with Python (Flask), SQLAlchemy, and Docker.

Originally developed for Duke FinTech 512, UniSplit provides shared expense tracking for roommates, travel groups, and student teams. It handles multi-currency conversion, penny-accurate bill splitting, automated payment reminders, and transaction exports.

---

## Architecture

The project follows a standard layered architecture:

```text
[Frontend Client] (HTML5 / Vanilla JS / CSS)
       │
       ▼  HTTP / REST API (JWT Authenticated)
[Flask Backend]
  ├── Routers          (/api/auth, /api/expenses, /api/settlements, /api/currencies)
  ├── Security Layer   (PyJWT verification, bcrypt hashing, request audit logging)
  ├── Services Layer   (Split calculations, currency conversions, reconciliation)
  └── Repositories     (SQLAlchemy ORM with transaction commit/rollback)
       │
       ├──► [Database] (MySQL in staging/production, SQLite in local container & tests)
       └──► [Audit Log] (logs/unisplit_security.log)

[Background Daemon]
  └── Runs every hour to check for 24h unsettled bills and verify ledger consistency
```

---

## Features

- **Bill Splitting & Ledger Integrity**: Supports equal and custom split amounts. Uses decimal quantization and remainder allocation (`_equal_split`) to avoid one-cent rounding errors. All multi-step ledger updates run inside atomic SQLAlchemy transactions that roll back on failure.
- **Multi-Currency Support**: Fetches live exchange rates via the Frankfurter API with an in-memory TTL cache and built-in offline fallback rates (USD, EUR, GBP, CAD, CNY, JPY, AUD) so currency lookups remain responsive even if external services fail.
- **Background Daemon Worker**: A non-blocking daemon thread runs independently of request cycles, checking for unsettled debts older than 24 hours, sending automated reminders, and auditing ledger balances.
- **Security & Auditing**: Stateless authentication via PyJWT, passwords hashed with `bcrypt`, and request-level security logs tracking IP and user actions in `logs/unisplit_security.log`.
- **Spending Analytics & Export**: 30-day category breakdown, balance summaries, and one-click CSV export (`/api/expenses/export`).

---

## Tech Stack

- **Backend**: Python 3.11, Flask, SQLAlchemy, PyJWT, bcrypt, PyMySQL
- **Frontend**: HTML5, Vanilla JavaScript, CSS3
- **Database**: MySQL (production / Duke VCM), SQLite (local container & tests)
- **DevOps**: Docker, Docker Compose, GitLab CI/CD, GitHub Actions, Pytest

---

## REST API Overview

| Route | Method | Description |
| :--- | :--- | :--- |
| `/api/register` | `POST` | Register a new user |
| `/api/login` | `POST` | Authenticate and obtain JWT token |
| `/api/me` | `GET` | Get current user profile and balance |
| `/api/expenses` | `GET` | List expenses (supports search, category, and date filters) |
| `/api/expenses` | `POST` | Record a new group expense and split shares |
| `/api/expenses/summary` | `GET` | Get spending statistics and category breakdowns |
| `/api/expenses/export` | `GET` | Export expense history as CSV |
| `/api/expenses/:id/respond`| `POST` | Accept or dispute an expense split |
| `/api/groups/:id/settlements` | `POST` | Record repayment and update balances |
| `/api/currencies` | `GET` | Get current exchange rates with fallback |

---

## Getting Started

### 1. Docker Compose (Recommended)

Run the full application in a single container exposed on port `3000`:

```bash
docker compose up -d --build
```

- Web App: `http://localhost:3000`
- API Base: `http://localhost:3000/api/...`

To stop:
```bash
docker compose down
```

### 2. Local Development

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
# Runs on http://127.0.0.1:5000
```

**Frontend:**
```bash
cd frontend/src
python -m http.server 8000
# Open http://localhost:8000 in your browser
```

---

## Testing & CI/CD

The test suite covers repositories, business logic, authentication, and REST routes.

```bash
# Run unit and integration tests
pytest -v

# Run backend smoke test
python .gitlab/ci/smoke_backend.py
```

- **GitHub Actions**: Configured in `.github/workflows/ci.yml` to run tests automatically on pushes and pull requests.
- **GitLab CI**: Configured in `.gitlab-ci.yml` with `test`, `smoke`, and `deploy` stages for Duke VCM.
