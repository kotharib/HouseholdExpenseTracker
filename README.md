# Household Finance Manager

A full-stack **household management & expense tracking** application with an **AI agent** powered by a
local LLM (Llama 3 via Ollama), monthly financial PDFs, auto-reports and diagram generation.

- **Frontend**: React 18 + TypeScript + Vite + Material UI + Zustand + Recharts + Axios
- **Backend**: FastAPI + SQLModel (SQLAlchemy) + SQLite + Alembic + JWT auth
- **AI**: LangChain (`SQLDatabaseToolkit`, `ConversationBufferMemory`) + `langchain-ollama` (Llama 3), with a deterministic fallback engine when Ollama is offline
- **Reports**: ReportLab PDF with charts + tables + AI text
- **Diagrams**: dependency-free ASCII + SVG generators

---

## Features

- Daily expense tracking (category / amount / date / payment mode / tags)
- Servant salary tracking (home cleaning, utensil cleaning, car cleaning, cook, custom roles)
- Milk delivery tracking (supplier, quantity, rate, month)
- Newspaper subscription tracking
- Bulk delete (multiple selected records or everything) on every list page
- Monthly summaries + dashboard with charts (trend bar chart, category pie chart)
- AI chat that reads the SQLite database and answers financial questions
- Financial insights: overspending detection, category analysis, savings suggestions
- Auto-report generator and monthly financial PDF
- Architecture / ER / AI-workflow diagrams documented as Mermaid diagrams in `docs/DIAGRAMS.md`
- All amounts in **Indian Rupees (₹)** with Indian digit grouping
- JWT auth (register/login), admin/user roles
- Dark mode toggle

---

## Folder structure

```
.
├── start.sh                  # Runs backend + frontend together
├── server/                   # FastAPI backend
│   ├── app/
│   │   ├── main.py           # App factory, CORS, routers, lifespan (seed)
│   │   ├── config.py         # Settings from env vars
│   │   ├── database.py       # Engine, session, init_db
│   │   ├── models/           # SQLModel tables (users, expenses, servants, milk, newspaper)
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── routers/          # auth, expenses, servants, milk, newspaper, dashboard, ai, reports, diagrams
│   │   ├── services/         # insights (financial math), seed (sample data)
│   │   ├── auth/             # password hashing + JWT + dependencies
│   │   ├── ai/               # agent.py (LangChain + fallback), tools.py (custom LangChain tools)
│   │   ├── reports/          # pdf.py (ReportLab generator)
│   │   ├── diagrams/         # generators.py (ASCII + SVG)
│   │   └── utils/            # helpers (month math, formatting)
│   ├── migrations/           # Alembic env + version 0001_init.py
│   ├── alembic.ini
│   ├── requirements.txt
│   └── seed_run.py           # explicit seed runner
└── frontend/                 # React + TS + Vite
    ├── vite.config.ts        # /api reverse proxy -> http://localhost:8000
    └── src/
        ├── api/client.ts     # Axios instance + auth interceptor
        ├── store/            # Zustand stores (auth, theme)
        ├── components/       # ExpenseForm/List, ServantForm/List, MilkForm/List,
        │                     # NewspaperForm/List, DashboardCharts, ChatUI, ReportViewer
        ├── utils/            # format.ts (INR formatting)
        └── pages/            # Auth, Dashboard, Expenses, Servants, Milk, Newspaper,
                              # Chat, Reports, Settings
```

> Diagrams (architecture, ER, AI workflow) live as Mermaid docs in `docs/DIAGRAMS.md`.
> They are intentionally not rendered in the UI.

---

## 1. Backend setup (FastAPI + SQLite)

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# (optional) run migrations explicitly
# alembic upgrade head

# start the API on http://localhost:8000  (Swagger docs at /docs)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The app seeds a SQLite database at `server/data/household.db` on startup with sample data.

**Default accounts**
| Username | Password | Role  |
|----------|----------|-------|
| admin    | admin123 | admin |
| demo     | demo123  | user  |

## 2. Frontend setup (React + TypeScript + Vite)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

`vite.config.ts` proxies every `/api/*` request to the backend on `:8000` (the `/api` prefix is
stripped), so there are **no CORS issues in development**. `allowedHosts` includes
`.monkeycode-ai.live` for preview environments.

Build & checks:

```bash
npm run build      # tsc + vite build
npm run lint       # eslint --ext ts,tsx --max-warnings 0
```

## 3. Run both together

```bash
./start.sh
```

## 4. Local LLM (Ollama + Llama 3)

The AI agent uses a **local** model via Ollama — no API keys needed.

1. **Install Ollama** (Linux/macOS):

   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Pull Llama 3**:

   ```bash
   ollama pull llama3
   ```

3. **Verify**:

   ```bash
   ollama run llama3 "hello"
   ```

4. **Configure the app** (env vars, defaults shown):

   ```bash
   export OLLAMA_BASE_URL=http://localhost:11434
   export OLLAMA_MODEL=llama3
   ```

5. Restart the backend. `GET /health` reports `"llm_available": true` when connected.

> **Fallback mode:** if Ollama is unreachable, the agent automatically switches to a deterministic
> engine that queries the same data, so every feature (chat, insights, reports, PDF) keeps working.

## 5. How the AI agent works

1. `app/ai/agent.py` builds a LangChain agent with `create_sql_agent` + `ChatOllama`,
   `SQLDatabaseToolkit` and **custom tools** (`app/ai/tools.py`):
   - `sql_query_tool` — read-only SQL against SQLite
   - `financial_insights` — totals, category analysis, pending payments, savings hints
   - `generate_monthly_summary` — natural-language monthly summaries
   - `generate_pdf_ready_text` — PDF-ready text blocks
2. Memory uses `ConversationBufferMemory(memory_key="chat_history")`.
3. `/ai/chat` streams the answer back as **SSE** tokens; `/ai/insights` and `/ai/report/monthly`
   return JSON.

### Example questions for the AI agent

- “How much did I spend last month?”
- “Which servant salary is pending?”
- “Summarize my milk expenses for July.”
- “What is my top spending category this month?”
- “Give me financial insights and savings suggestions.”
- “Generate a monthly report for 2026-08.”

---

## API documentation

Interactive docs at `http://localhost:8000/docs`.

### Auth
| Method | Endpoint            | Body                                   |
|--------|---------------------|----------------------------------------|
| POST   | `/auth/register`    | `{username, password, role?}`          |
| POST   | `/auth/login`       | `{username, password}`                 |
| GET    | `/auth/me`          | — (Bearer token)                       |

### Expenses
| Method | Endpoint         | Notes                                   |
|--------|------------------|-----------------------------------------|
| GET    | `/expenses`      | query: `month=YYYY-MM`, `category`      |
| POST   | `/expenses`      | `{category, amount, date, notes?, payment_mode?, tags?}` |
| PUT    | `/expenses/{id}` | partial update                          |
| DELETE | `/expenses/{id}` | —                                       |
| POST   | `/expenses/bulk-delete` | body `{"ids": [..]}` or `{"all": true}` |

### Servants
| Method | Endpoint         | Notes |
|--------|------------------|-------|
| GET    | `/servants`      | query: `role`, `payment_status` |
| POST   | `/servants`      | `{name, role, monthly_salary, payment_status?, attendance_count?}` |
| PUT    | `/servants/{id}` | partial update |
| DELETE | `/servants/{id}` | — |
| POST   | `/servants/bulk-delete` | body `{"ids": [..]}` or `{"all": true}` |

### Milk
| Method | Endpoint    | Notes |
|--------|-------------|-------|
| GET    | `/milk`     | query: `month`, `supplier`, `payment_status` |
| POST   | `/milk`     | `{supplier, quantity, rate, date, month, payment_status?}` |
| PUT    | `/milk/{id}` | partial update |
| DELETE | `/milk/{id}` | — |
| POST   | `/milk/bulk-delete` | body `{"ids": [..]}` or `{"all": true}` |

### Newspaper
| Method | Endpoint    | Notes |
|--------|-------------|-------|
| GET    | `/newspaper` | query: `month`, `payment_status` |
| POST   | `/newspaper` | `{name, monthly_cost, month, payment_status?}` |
| PUT    | `/newspaper/{id}` | partial update |
| DELETE | `/newspaper/{id}` | — |
| POST   | `/newspaper/bulk-delete` | body `{"ids": [..]}` or `{"all": true}` |

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
The backend still exposes ASCII/SVG diagram endpoints for scripting. The diagrams are
**documented as Mermaid diagrams** in `docs/DIAGRAMS.md` and are not rendered in the UI.

| Method | Endpoint                       | Notes |
|--------|--------------------------------|-------|
| GET    | `/diagrams/architecture`       | `?format=ascii\|svg` |
| GET    | `/diagrams/er`                 | `?format=ascii\|svg` |
| GET    | `/diagrams/ai-workflow`        | `?format=ascii\|svg` |

All data endpoints require `Authorization: Bearer <token>`.

---

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
