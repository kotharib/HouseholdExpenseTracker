# Household Finance Manager

A full-stack **household management & expense tracking** application with an **AI assistant**,
monthly financial PDFs, auto-reports and system diagrams — all amounts in **Indian Rupees (₹)**.

This README is written so that even someone new to software development or AI can understand
**what the app does**, **how it is built**, and **how to run it**. Deeper guides live in `docs/`.

- **Beginner-friendly architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **How the AI works (LLM explained)**: [docs/AI_GUIDE.md](docs/AI_GUIDE.md)
- **Feature-by-feature implementation**: [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md)
- **System diagrams (Mermaid)**: [docs/DIAGRAMS.md](docs/DIAGRAMS.md)

---

## Table of contents

1. [What does this app do?](#what-does-this-app-do)
2. [Tech stack](#tech-stack)
3. [Features](#features)
4. [Architecture in one picture](#architecture-in-one-picture)
5. [Folder structure](#folder-structure)
6. [Run it yourself](#run-it-yourself)
7. [How the AI assistant works (quick version)](#how-the-ai-assistant-works-quick-version)
8. [API documentation](#api-documentation)
9. [Database schema](#database-schema)
10. [Validation performed](#validation-performed)

---

## What does this app do?

It is a personal finance tracker for a household. You can record everyday expenses, track
servant salaries, milk deliveries and newspaper subscriptions, and log **investments**
(mutual funds, PPF, NPS and other Indian options) — then ask an **AI assistant**
questions about your money, get monthly summaries, and download a **PDF report**.

Think of it as a spreadsheet that can *talk to you*.

## Tech stack

| Layer     | Technology                                                             | Why it is used                        |
|-----------|------------------------------------------------------------------------|---------------------------------------|
| Frontend  | React 18 + TypeScript + Vite + Material UI + Zustand + Recharts + Axios | Interactive, modern browser app       |
| Backend   | FastAPI + SQLModel (SQLAlchemy) + SQLite + Alembic + JWT auth           | Simple Python API with a file database|
| AI        | LangChain + local Llama 3 (Ollama), with a deterministic fallback engine| Ask questions in plain English        |
| Reports   | ReportLab (PDF), Recharts (charts)                                     | Monthly PDF + interactive charts      |

> **No cloud AI required.** The AI model runs locally through [Ollama](https://ollama.com),
> so you need no API keys. If Ollama is not installed, the app still works using a built-in
> "fallback engine" that answers from the database directly.

## Features

- Daily expense tracking (category / amount / date / payment mode / tags)
- Servant salary tracking (cook, cleaning, driver and custom roles)
- Milk delivery tracking (supplier, quantity, rate, month)
- Newspaper subscription tracking
- **Investment tracking** (mutual funds, PPF, NPS, ELSS, Sukanya Samriddhi, FDs…)
- **Investment Advisor**: risk-based asset allocation + representative Indian schemes
- **Filter and sort** on every column of every list
- **Bulk delete** (delete selected rows, or delete everything) on every list
- Dashboard with animated metric cards and charts (trend bar + category pie)
- AI chat that reads the SQLite database and answers financial questions
- Financial insights: overspending detection, category analysis, savings suggestions
- Auto-report generator and a downloadable monthly PDF
- Column filtering/sorting, dark mode, and polished animations
- All amounts in **Indian Rupees (₹)** with Indian digit grouping
- JWT authentication (register/login) with admin/user roles
- System diagrams documented as Mermaid in `docs/DIAGRAMS.md`

## Architecture in one picture

```
Browser (React app)
      │  every /api/* request is proxied to the backend by Vite
      ▼
FastAPI backend  ──────────►  SQLite database (one file: household.db)
      │
      ├── JWT auth (login/register)
      ├── REST endpoints (expenses, servants, milk, newspaper, investments, dashboard)
      └── AI agent (LangChain + Ollama llama3, or fallback engine)
```

A request (for example "How much did I spend this month?") flows like this:

1. The **frontend** sends the question to `/api/ai/chat`.
2. The **backend** agent asks the **AI model** what to do; the model chooses tools.
3. A tool **queries the database** (SQL) and returns numbers.
4. The AI model turns the numbers into a friendly sentence.
5. The answer streams back to the browser **token by token** (like ChatGPT).

Detailed diagrams: [docs/DIAGRAMS.md](docs/DIAGRAMS.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Folder structure

```
.
├── start.sh                  # Starts backend + frontend together
├── docs/                     # Beginner-friendly documentation + Mermaid diagrams
├── server/                   # FastAPI backend (Python)
│   ├── app/
│   │   ├── main.py           # App factory, CORS, routers, startup seeding
│   │   ├── config.py         # Settings from environment variables
│   │   ├── database.py       # Database engine, sessions, init_db
│   │   ├── models/           # SQLModel tables (users, expenses, servants, milk, newspaper, investments)
│   │   ├── schemas/          # Pydantic request/response models (data shapes)
│   │   ├── routers/          # auth, expenses, servants, milk, newspaper, investments, dashboard, ai, reports, diagrams
│   │   ├── services/         # insights (financial math), investment_advisor, seed (sample data)
│   │   ├── auth/             # password hashing + JWT + dependencies
│   │   ├── ai/               # agent.py (LangChain + fallback), tools.py (custom tools)
│   │   ├── reports/          # pdf.py (ReportLab generator)
│   │   ├── diagrams/         # generators.py (ASCII + SVG)
│   │   └── utils/            # helpers (month math, INR formatting)
│   ├── migrations/           # Alembic database migrations
│   ├── alembic.ini
│   ├── requirements.txt
│   └── seed_run.py           # Explicit seed runner
└── frontend/                 # React + TypeScript + Vite
    ├── vite.config.ts        # /api reverse proxy -> http://localhost:8000
    └── src/
        ├── api/client.ts     # Axios instance + auth interceptor
        ├── store/            # Zustand stores (auth, theme)
        ├── components/       # Forms/Lists, DashboardCharts, ChatUI, ReportViewer, TableControls
        ├── utils/            # format.ts (INR), useTableControls, useCountUp
        └── pages/            # Auth, Dashboard, Expenses, Servants, Milk, Newspaper, Chat, Reports, Settings
```

## Run it yourself

### Option A: one command (recommended)

```bash
./start.sh
```

This starts the backend on `:8000` and the frontend on `:5173`.

### Option B: run each part manually

**Backend**

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start the API on http://localhost:8000 (Swagger docs at /docs)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The app creates and seeds a SQLite database at `server/data/household.db` on startup.

**Frontend**

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

`vite.config.ts` proxies every `/api/*` request to the backend on `:8000`, so there are
**no CORS issues in development**. `allowedHosts` includes `.monkeycode-ai.live` for preview
environments.

**Build & checks**

```bash
cd frontend
npm run build      # tsc + vite build (production bundle)
npm run lint       # eslint --ext ts,tsx --max-warnings 0
```

**Default accounts**

| Username | Password | Role  |
|----------|----------|-------|
| admin    | admin123 | admin |
| demo     | demo123  | user  |

## How the AI assistant works (quick version)

The AI assistant is powered by a **local** Large Language Model (LLM) running via Ollama:

1. **Install Ollama** and pull the model:

   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull llama3
   ```

2. **Configure the backend** (defaults shown):

   ```bash
   export OLLAMA_BASE_URL=http://localhost:11434
   export OLLAMA_MODEL=llama3
   ```

3. Restart the backend. `GET /health` reports `"llm_available": true` when connected.

**No LLM? No problem.** If Ollama is unreachable, the app switches to a **deterministic
fallback engine** that answers from the database directly, so every feature (chat, insights,
reports, PDF) keeps working.

- `app/ai/agent.py` builds the LangChain agent and the fallback engine.
- `app/ai/tools.py` defines the tools the model can call (SQL query, insights, summaries).
- `/ai/chat` streams answers as SSE tokens; `/ai/insights` and `/ai/report/monthly` return JSON.

Read the full beginner guide: [docs/AI_GUIDE.md](docs/AI_GUIDE.md).

### Example questions for the AI agent

- "How much did I spend last month?"
- "Which servant salary is pending?"
- "Summarize my milk expenses for July."
- "What is my top spending category this month?"
- "Give me financial insights and savings suggestions."
- "Generate a monthly report for 2026-08."
- "Suggest investments for ₹1,00,000 with an aggressive profile."

## API documentation

Interactive docs at `http://localhost:8000/docs`.

All data endpoints require `Authorization: Bearer <token>`.

### Auth

| Method | Endpoint            | Body                                   |
|--------|---------------------|----------------------------------------|
| POST   | `/auth/register`    | `{username, password, role?}`          |
| POST   | `/auth/login`       | `{username, password}`                 |
| GET    | `/auth/me`          | — (Bearer token)                       |

### Expenses

| Method | Endpoint                | Notes                                            |
|--------|-------------------------|--------------------------------------------------|
| GET    | `/expenses`             | query: `month=YYYY-MM`, `category`               |
| POST   | `/expenses`             | `{category, amount, date, notes?, payment_mode?, tags?}` |
| PUT    | `/expenses/{id}`        | partial update                                  |
| DELETE | `/expenses/{id}`        | —                                               |
| POST   | `/expenses/bulk-delete` | body `{"ids": [..]}` or `{"all": true}`         |

### Servants

| Method | Endpoint                | Notes |
|--------|-------------------------|-------|
| GET    | `/servants`             | query: `role`, `payment_status` |
| POST   | `/servants`             | `{name, role, monthly_salary, payment_status?, attendance_count?}` |
| PUT    | `/servants/{id}`        | partial update |
| DELETE | `/servants/{id}`        | — |
| POST   | `/servants/bulk-delete` | body `{"ids": [..]}` or `{"all": true}` |

### Milk

| Method | Endpoint         | Notes |
|--------|------------------|-------|
| GET    | `/milk`          | query: `month`, `supplier`, `payment_status` |
| POST   | `/milk`          | `{supplier, quantity, rate, date, month, payment_status?}` |
| PUT    | `/milk/{id}`     | partial update |
| DELETE | `/milk/{id}`     | — |
| POST   | `/milk/bulk-delete` | body `{"ids": [..]}` or `{"all": true}` |

### Newspaper

| Method | Endpoint                  | Notes |
|--------|---------------------------|-------|
| GET    | `/newspaper`              | query: `month`, `payment_status` |
| POST   | `/newspaper`              | `{name, monthly_cost, month, payment_status?}` |
| PUT    | `/newspaper/{id}`         | partial update |
| DELETE | `/newspaper/{id}`         | — |
| POST   | `/newspaper/bulk-delete`  | body `{"ids": [..]}` or `{"all": true}` |

### Investments

| Method | Endpoint                     | Notes |
|--------|------------------------------|-------|
| GET    | `/investments`               | query: `month`, `category` |
| POST   | `/investments`               | `{scheme_name, category, amount, date, month?, expected_return?, notes?}` |
| PUT    | `/investments/{id}`          | partial update |
| DELETE | `/investments/{id}`          | — |
| POST   | `/investments/bulk-delete`   | body `{"ids": [..]}` or `{"all": true}` |
| GET    | `/investments/options`       | curated catalog of Indian options (PPF, NPS, ELSS, SSY, FDs, MFs…) |
| GET    | `/investments/profiles`      | risk profiles: conservative / moderate / aggressive |
| POST   | `/investments/advisor`       | `{amount, profile}` → asset allocation + representative schemes |
| GET    | `/investments/summary`       | total invested + breakdown by category |

### Dashboard

| Method | Endpoint                     | Notes |
|--------|------------------------------|-------|
| GET    | `/dashboard/summary`         | totals, category totals, monthly trend, pending payments |
| GET    | `/dashboard/monthly-expenses`| `?month=YYYY-MM` → total + items |
| GET    | `/dashboard/pending-payments`| grouped pending list + total |

### AI

| Method | Endpoint                 | Notes |
|--------|--------------------------|-------|
| POST   | `/ai/chat`               | SSE streaming response |
| GET    | `/ai/insights`           | insights text + structured data |
| GET    | `/ai/report/monthly`     | `?month=YYYY-MM` → AI summary text |

### Reports

| Method | Endpoint                 | Notes |
|--------|--------------------------|-------|
| GET    | `/reports/monthly/pdf`   | `?month=YYYY-MM` → ReportLab PDF attachment |
| GET    | `/reports/auto`          | `?month=YYYY-MM` → structured auto-report |

### Diagrams (API only)

The backend exposes ASCII/SVG diagram endpoints for scripting, but the diagrams are
**documented as Mermaid** in `docs/DIAGRAMS.md` and are not rendered in the UI.

| Method | Endpoint                       | Notes |
|--------|--------------------------------|-------|
| GET    | `/diagrams/architecture`       | `?format=ascii\|svg` |
| GET    | `/diagrams/er`                 | `?format=ascii\|svg` |
| GET    | `/diagrams/ai-workflow`        | `?format=ascii\|svg` |

## Database schema

```
users               expenses
- id                - id
- username (unique) - category (indexed)
- password_hash     - amount
- role              - date (indexed)
                    - notes / payment_mode / tags

servants            milk_deliveries         newspaper_deliveries
- id                - id                    - id
- name (indexed)    - supplier (indexed)    - name (indexed)
- role              - quantity / rate       - monthly_cost
- monthly_salary    - date / month(indexed) - month (indexed)
- payment_status    - payment_status        - payment_status
- attendance_count

investments
- id
- scheme_name (indexed)
- category (indexed)   # ppf, nps, ssy, scss, nsc, fd, rd, sgb, elss,
                       # equity_mf, index_fund, debt_mf, hybrid_mf
- amount
- date (indexed) / month (indexed)
- expected_return / notes
```

Months are stored as `YYYY-MM`. Migration: `server/migrations/versions/0001_init.py`.

## Validation performed

- All API endpoints exercised (auth, CRUD, bulk delete, dashboard, AI chat/insights/report, PDF, diagrams)
- `alembic upgrade head` creates all tables cleanly on a fresh DB
- PDF output validated as a real `%PDF` document
- Fallback AI agent answers validated against seeded data
- `tsc --noEmit` clean, `eslint` 0 warnings, `vite build` succeeds
- Vite `/api` proxy verified against the running backend
- All amounts verified as Indian Rupees (₹) across API, AI output, UI and PDF
