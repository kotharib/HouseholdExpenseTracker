# Implementation Guide

This guide walks through **how each feature is implemented**, pointing to the exact files and
functions. It is written to be readable by beginners — you can follow along in the code.

> Start with [ARCHITECTURE.md](ARCHITECTURE.md) if you have not read it yet.

---

## 1. Authentication (JWT)

**Goal:** let users log in and protect private data.

**Files:** `server/app/auth/security.py`, `server/app/auth/dependencies.py`,
`server/app/routers/auth.py`, `frontend/src/store/authStore.ts`

How it works:

1. `POST /auth/register` creates a user. The password is **hashed** (never stored in plain text)
   using `bcrypt`.
2. `POST /auth/login` verifies the password and returns a **JWT** — a signed token that proves
   who you are and expires later.
3. The frontend saves the token (`authStore.ts`) and sends it as
   `Authorization: Bearer <token>` on every API call (`api/client.ts`).
4. `get_current_user` in `dependencies.py` decodes the token on every protected route. If it is
   invalid/expired, the request is rejected with `401`.

### Read it

- Hash & create token → `security.py`
- Protect a route → decorator/dependency `dependencies.py:get_current_user`
- Login/register endpoints → `routers/auth.py`

---

## 2. Database models (SQLModel)

**Goal:** define the tables the app stores data in.

**Files:** `server/app/models/` (one file per table), `server/app/database.py`

Each model is a Python class that SQLModel turns into a database table:

```python
# server/app/models/expense.py (simplified)
class Expense(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    category: str = Field(index=True, max_length=64)
    amount: float
    date: date
    notes: str | None = None
    payment_mode: str | None = None
```

- `index=True` tells SQLite to make lookups by that column fast.
- Months (e.g. `2026-08`) are stored as `YYYY-MM` strings and indexed, so monthly reports are
  quick.
- `Expense.month` is a computed Python `@property`, **not** a database column — so it cannot be
  used in SQL `WHERE` clauses. Monthly queries use a helper `month_range()` that computes the
  start and end dates of a month.

### Read it

- Table definitions → `models/expense.py`, `models/servant.py`, `models/milk.py`,
  `models/newspaper.py`, `models/user.py`
- Engine + session → `database.py`
- Migration file → `migrations/versions/0001_init.py`

---

## 3. CRUD + bulk delete endpoints

**Goal:** create, read, update, delete records — individually or in bulk.

**Files:** `server/app/routers/expenses.py` (the others mirror it),
`server/app/schemas/common.py`, `server/app/schemas/expense.py`

Each resource router provides:

| Method   | Endpoint                | Purpose                          |
|----------|-------------------------|----------------------------------|
| `GET`    | `/expenses`             | list (with `month`/`category` filters) |
| `POST`   | `/expenses`             | create one                       |
| `PUT`    | `/expenses/{id}`        | update one                       |
| `DELETE` | `/expenses/{id}`        | delete one                       |
| `POST`   | `/expenses/bulk-delete` | delete many, or all              |

### Bulk delete

`POST /{resource}/bulk-delete` accepts a body of either:

```json
{ "ids": [1, 2, 3] }
// or
{ "all": true }
```

The shared request/response models live in `schemas/common.py`:

```python
class BulkDeleteRequest(BaseModel):
    ids: list[int] | None = None
    all: bool = False

class BulkDeleteResponse(BaseModel):
    deleted: int
```

The router returns `400 Bad Request` if neither `ids` nor `all` is provided. This design avoids
sending a request body with `DELETE` (which some tools dislike), so it uses `POST` instead.

---

## 4. Filtering & sorting (frontend)

**Goal:** every column of every list can be sorted and filtered.

**Files:** `frontend/src/utils/useTableControls.ts`,
`frontend/src/components/TableControls.tsx`

- `useTableControls` is a **React hook** that keeps three pieces of state: which column is
  sorted, the direction (asc/desc), and the active filter text per column.
- It computes `sortedAndFiltered` from the raw rows using `useMemo`:
  1. **Filter**: for each active column, keep rows whose cell text contains the filter text
     (case-insensitive).
  2. **Sort**: compare values — numbers numerically, everything else as text.
- `TableControls.tsx` exports two small components:
  - `SortableHeader` — the clickable column title (MUI `TableSortLabel`).
  - `FilterCell` — the small text box under each column header.

Each list page (Expenses, Servants, Milk, Newspaper) wires these into its table, and the totals
row + selection only count the **filtered** rows.

### Read it

- Hook logic → `utils/useTableControls.ts`
- Header/filter components → `components/TableControls.tsx`
- Example usage → `components/ExpenseList.tsx`

---

## 5. Indian Rupee (₹) formatting

**Goal:** every amount shows as Indian Rupees with Indian digit grouping (e.g. `₹1,23,456.78`).

**Files:** `server/app/utils/helpers.py`, `frontend/src/utils/format.ts`,
`server/app/reports/pdf.py`

- **Backend text** (AI answers, auto-reports) uses one shared helper `format_money()` in
  `helpers.py`.
- **Frontend** uses `Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })` in
  `format.ts` — the browser's built-in Indian formatting.
- **PDF**: ReportLab's built-in fonts (Helvetica) do **not** contain the `₹` glyph, so the PDF
  uses `₹` if a capable font is registered, otherwise it falls back to `Rs ` (e.g.
  `Rs 6,893.45`). This is handled by the `CURRENCY_SYMBOL` logic in `pdf.py`.

---

## 6. Dashboard & insights

**Goal:** show totals, trends, category breakdowns and pending payments.

**Files:** `server/app/services/insights.py`, `server/app/routers/dashboard.py`,
`frontend/src/components/DashboardCharts.tsx`

`insights.compute_insights(session, month)` is a single function that computes everything the
dashboard and reports need in one pass:

- current month total and expense count
- previous month total and the **delta** (change)
- per-category totals (sorted by amount)
- pending payments across servants / milk / newspaper
- savings hints (categories over 20% of spending)

`DashboardCharts.tsx` renders metric cards that **count up** to their value (via
`useCountUp`) and charts built with **Recharts** (bar chart for monthly trend, pie chart for
category breakdown).

---

## 7. Reports (auto-report + PDF)

**Goal:** produce a structured monthly report and a downloadable PDF.

**Files:** `server/app/routers/reports.py`, `server/app/reports/pdf.py`,
`server/app/schemas/report.py`, `frontend/src/components/ReportViewer.tsx`

### Auto-report (`GET /reports/auto`)

Returns a structured `AutoReportResponse`:

```json
{
  "month": "2026-08",
  "title": "Auto Report — August 2026",
  "sections": ["Total expenses ...", "Previous month ..."],
  "ai_summary": "In August you spent ...",
  "pending": [{"type": "servant", "name": "Ramesh", "amount": 1500}],
  "totals": { "total_expenses": 6893.45, "pending": 0 },
  "expense_count": 16,
  "previous_month_total": 4262.95,
  "delta": 2630.5,
  "category_totals": [{"category": "groceries", "total": 2523.87}],
  "generated_at": "2026-08-09"
}
```

The frontend `ReportViewer.tsx` presents this as: four animated metric cards (expenses,
transactions, vs last month, pending), the auto-report sections, a **category breakdown with
progress bars**, an AI summary panel, and a pending-payments table.

### PDF (`GET /reports/monthly/pdf`)

`generate_monthly_pdf(month, expenses, pending, ai_text)` in `pdf.py` builds the document with
ReportLab: title page info, summary tables, charts, and the AI text. The browser triggers a
download via a blob URL.

---

## 8. AI agent (LangChain + fallback)

**Goal:** answer financial questions in natural language.

**Files:** `server/app/ai/agent.py`, `server/app/ai/tools.py`, `server/app/routers/ai.py`

Full beginner explanation: [AI_GUIDE.md](AI_GUIDE.md).

Short version:

- `agent.py` builds a **LangChain SQL agent** using `ChatOllama` (Llama 3) with custom tools
  and `ConversationBufferMemory`.
- If Ollama is unreachable, `agent.is_available` is `False` and a **deterministic fallback
  engine** answers using keyword matching over the same database queries.
- `/ai/chat` streams the answer as **SSE** tokens; `/ai/insights` and `/ai/report/monthly`
  return JSON.

### Read it

- Agent + fallback → `agent.py`
- Tool definitions → `tools.py`
- Streaming endpoint → `routers/ai.py`
- Frontend chat → `components/ChatUI.tsx`

---

## 9. UI polish & animations

**Goal:** a nicer look and feel with subtle animations.

**Files:** `frontend/src/theme.ts`, `frontend/src/styles.css`,
`frontend/src/components/Layout.tsx`, `frontend/src/pages/AuthPage.tsx`,
`frontend/src/components/DashboardCharts.tsx`, `frontend/src/components/ChatUI.tsx`

- **Theme** (`theme.ts`) defines the palette, gradient primary/secondary buttons, hover-lift
  cards and shape.
- **Animations** (`styles.css`) are plain CSS keyframes: `fadeInUp`, `fadeIn`, `slideInRight`,
  `floaty`, `gradientShift`, `typingBlink`.
- **Layout**: animated sidebar with a gradient brand badge, an active-link indicator bar and
  icon-only top-bar actions.
- **Dashboard**: `useCountUp` drives count-up metric cards; cards/charts/pending list stagger in.
- **Login page**: animated shifting gradient background with floating shapes.
- **Chat**: fade-in bubbles, gradient user bubbles, and a bouncing three-dot typing indicator.
- **Route transitions**: pages fade in on navigation (keyed on the route path in `Layout.tsx`).

---

## 10. Diagrams (documentation only)

**Goal:** keep system diagrams as living docs, not UI clutter.

**Files:** `server/app/diagrams/generators.py`, `docs/DIAGRAMS.md`

The backend still exposes `GET /diagrams/*` (ASCII/SVG) for scripting, but the UI does **not**
render a diagram page. Instead, the architecture, ER and AI-workflow diagrams are documented as
**Mermaid** diagrams in `docs/DIAGRAMS.md`, which GitHub and VS Code render natively.

---

## Suggested reading order

1. [README](../README.md) — what it is, how to run it
2. [ARCHITECTURE.md](ARCHITECTURE.md) — how the pieces fit
3. [AI_GUIDE.md](AI_GUIDE.md) — how the AI works
4. This file — where each feature is implemented
5. [DIAGRAMS.md](DIAGRAMS.md) — the system pictures
