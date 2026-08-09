# System Diagrams

The diagrams for this application are documented here as Mermaid diagrams so they can be
rendered directly by GitHub, GitLab, VS Code, or any Mermaid-compatible viewer. There is no
diagram page in the UI; use the code below as living documentation.

## 1. Architecture

```mermaid
graph TD
    A["React SPA (Vite, TS, MUI)"]
    B["FastAPI (REST + JWT, Pydantic)"]
    C[("SQLite (SQLModel)")]
    D["AI Agent (LangChain)"]
    E["Ollama llama3 (local LLM)"]
    F["ReportLab PDF"]
    G["Auto-report + insights"]

    A -->|"HTTP /api (Vite proxy)"| B
    B -->|"SQLAlchemy"| C
    B -->|"JWT auth"| A
    B -->|"initiate"| D
    D -->|"SQLDatabaseToolkit"| C
    D -->|"custom tools"| G
    D -->|"ChatOllama"| E
    E -->|"tokens"| D
    B -->|"generate"| F
    G -->|"text blocks"| F
```

## 2. Entity Relationship (ER) Diagram

```mermaid
erDiagram
    users {
        int id PK
        string username
        string password_hash
        string role
    }
    expenses {
        int id PK
        string category
        float amount
        date date
        string notes
        string payment_mode
        string tags
    }
    servants {
        int id PK
        string name
        string role
        float monthly_salary
        string payment_status
        int attendance_count
    }
    milk_deliveries {
        int id PK
        string supplier
        float quantity
        float rate
        date date
        string month
        string payment_status
    }
    newspaper_deliveries {
        int id PK
        string name
        float monthly_cost
        string month
        string payment_status
    }

    users ||--o{ expenses : "tracks"
    users ||--o{ servants : "tracks"
    users ||--o{ milk_deliveries : "tracks"
    users ||--o{ newspaper_deliveries : "tracks"
```

Notes:

- Months are stored as `YYYY-MM` strings and indexed.
- `payment_status` is one of `pending` | `paid`.
- The relationships shown are logical ownership (application-level); the SQLite schema
  itself has no foreign keys.

## 3. AI Agent Workflow

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant C as Chat API
    participant A as AI Agent
    participant T as Tools
    participant D as SQLite
    participant L as Ollama llama3

    U->>C: POST /ai/chat (message + history)
    C->>A: invoke agent
    A->>T: sql_query_tool
    T->>D: SELECT ...
    D-->>T: rows
    A->>T: financial_insights
    A->>T: generate_monthly_summary
    A->>L: reasoning over tool results
    L-->>A: completion
    A-->>C: final answer
    C-->>U: SSE token stream (data frames)
```

## Fallback behaviour

If Ollama is not running, the agent executes in **fallback mode**: the same tools and database
queries are driven by a deterministic keyword router, so chat, insights, auto-reports and the
monthly PDF all keep working without an LLM.
