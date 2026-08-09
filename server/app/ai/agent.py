"""AI Agent: LangChain + Ollama with a deterministic fallback.

When a local Ollama server with the configured model is reachable, the agent
uses LangChain (SQLDatabaseToolkit + custom tools + ConversationBufferMemory)
to answer questions. Otherwise it falls back to a keyword-driven agent that
queries the same data, so every feature keeps working without the LLM.
"""

from __future__ import annotations

import re
from datetime import date

from app.config import settings
from app.database import engine
from app.services import insights as insight_service
from app.utils.helpers import format_money, last_month, month_name

MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def ollama_available() -> bool:
    """Check whether the Ollama server responds with the expected model."""
    try:
        import httpx

        resp = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2.0)
        resp.raise_for_status()
        tags = resp.json().get("models", [])
        wanted = settings.OLLAMA_MODEL.split(":")[0]
        return any(t.get("name", "").split(":")[0] == wanted for t in tags)
    except Exception:
        return False


class AIAgent:
    def __init__(self) -> None:
        self.llm_available = False
        self._executor = None
        self._init_llm()

    # ------------------------------------------------------------------ init
    def _init_llm(self) -> None:
        try:
            if not ollama_available():
                return
            from langchain.agents import AgentExecutor, create_sql_agent
            from langchain.agents.agent_types import AgentType
            from langchain.memory import ConversationBufferMemory
            from langchain_community.agent_toolkits import SQLDatabaseToolkit
            from langchain_community.utilities import SQLDatabase
            from langchain_ollama import ChatOllama

            self._llm = ChatOllama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
                temperature=0.2,
            )
            db = SQLDatabase.from_engine(engine)
            toolkit = SQLDatabaseToolkit(db=db, llm=self._llm)

            from app.ai.tools import build_langchain_tools

            memory = ConversationBufferMemory(
                memory_key="chat_history", return_messages=True, k=8
            )
            self._executor: AgentExecutor = create_sql_agent(
                llm=self._llm,
                toolkit=toolkit,
                extra_tools=build_langchain_tools(),
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=False,
                handle_parsing_errors=True,
                agent_executor_kwargs={"memory": memory},
            )
            self.llm_available = True
        except Exception:
            self.llm_available = False
            self._executor = None

    # ------------------------------------------------------------------ API
    @property
    def is_available(self) -> bool:
        return self.llm_available and self._executor is not None

    def chat(self, message: str, history: list[dict] | None = None) -> str:
        if self.is_available:
            try:
                history = history or []
                if len(history) <= 2:
                    prompt = message
                else:
                    recent = history[-6:]
                    prompt = (
                        "Recent conversation:\n"
                        + "\n".join(f"{m['role']}: {m['content']}" for m in recent)
                        + f"\nuser: {message}"
                    )
                result = self._executor.invoke({"input": prompt})
                return str(result.get("output", "")).strip()
            except Exception:
                pass
        return FallbackAgent().respond(message)

    def insights(self) -> str:
        if self.is_available:
            try:
                result = self._executor.invoke(
                    {
                        "input": (
                            "Use the financial_insights and generate_monthly_summary tools to "
                            "produce a concise set of financial insights for the current month, "
                            "including overspending detection, category analysis and savings "
                            "suggestions. Write 4-6 bullet points."
                        )
                    }
                )
                return str(result.get("output", "")).strip()
            except Exception:
                pass
        from app.ai.tools import _financial_insights

        return _financial_insights("")

    def monthly_report(self, month: str | None = None) -> str:
        target = month or date.today().strftime("%Y-%m")
        if self.is_available:
            try:
                result = self._executor.invoke(
                    {
                        "input": (
                            f"Generate a monthly financial report for {target}. Use "
                            f"generate_monthly_summary and financial_insights tools. Include "
                            "totals, category breakdown, pending payments and 3 savings suggestions."
                        )
                    }
                )
                return str(result.get("output", "")).strip()
            except Exception:
                pass
        from app.ai.tools import _monthly_summary

        return _monthly_summary(target)


# ---------------------------------------------------------------------------
# Deterministic fallback agent
# ---------------------------------------------------------------------------
class FallbackAgent:
    def _session(self):
        from sqlmodel import Session

        return Session(engine)

    # ------------------------------------------------------------- helpers
    @staticmethod
    def _resolve_month(text: str, default: str | None = None) -> str:
        today = date.today()
        m = re.search(r"\b(\d{4})-(\d{2})\b", text)
        if m:
            return f"{m.group(1)}-{m.group(2)}"
        lowered = text.lower()
        for name, num in MONTH_NAMES.items():
            if name in lowered:
                year = today.year
                if name in ("january", "february", "march") and today.month < num and "last" not in lowered:
                    year -= 1
                return f"{year}-{num:02d}"
        return default or today.strftime("%Y-%m")

    # ------------------------------------------------------------ responses
    def respond(self, message: str) -> str:
        lowered = message.lower().strip()
        with self._session() as session:
            if any(k in lowered for k in ("insight", "analys", "analyz", "overspend", "suggest")):
                return self._insight_answer(session, lowered)
            if "report" in lowered:
                month = self._resolve_month(lowered)
                return self._report_answer(session, month)
            if "servant" in lowered or "salary" in lowered or "maid" in lowered:
                return self._servant_answer(session, lowered)
            if "milk" in lowered:
                return self._milk_answer(session, lowered)
            if "newspaper" in lowered or "paper" in lowered:
                return self._newspaper_answer(session, lowered)
            if any(k in lowered for k in ("spend", "expense", "money", "cost", "how much")):
                return self._spend_answer(session, lowered)
            return self._help_answer(session)

    def _spend_answer(self, session, text: str) -> str:
        month = self._resolve_month(text)
        from sqlmodel import select
        from app.utils.helpers import month_range

        from app.models.expense import Expense

        start, end = month_range(month)
        rows = session.exec(
            select(Expense).where(Expense.date >= start, Expense.date <= end)
        ).all()
        total = sum(e.amount for e in rows)
        prev = last_month(month)
        prev_start, prev_end = month_range(prev)
        prev_rows = session.exec(
            select(Expense).where(Expense.date >= prev_start, Expense.date <= prev_end)
        ).all()
        prev_total = sum(e.amount for e in prev_rows)
        delta = total - prev_total
        top: dict[str, float] = {}
        for e in rows:
            top[e.category] = top.get(e.category, 0.0) + e.amount
        top_str = ", ".join(f"{k} ({format_money(v)})" for k, v in sorted(top.items(), key=lambda x: x[1], reverse=True)[:3])
        return (
            f"For {month_name(month)} you spent {format_money(total)} across {len(rows)} expenses "
            f"(previous month: {format_money(prev_total)}, {('+' if delta >= 0 else '')}{format_money(delta)}).\n"
            f"Top categories: {top_str or 'none'}."
        )

    def _servant_answer(self, session, text: str) -> str:
        from sqlmodel import select

        from app.models.servant import Servant

        pending = session.exec(select(Servant).where(Servant.payment_status == "pending")).all()
        if "pending" not in text and not pending:
            all_s = session.exec(select(Servant)).all()
            if not all_s:
                return "No servants are registered yet."
            lines = [f"{s.name} ({s.role}) - {format_money(s.monthly_salary)}/month - {s.payment_status}" for s in all_s]
            return "Servant payroll:\n" + "\n".join(lines)
        if not pending:
            return "Great news — all servant salaries are paid!"
        lines = [f"{s.name} ({s.role}) - {format_money(s.monthly_salary)} pending" for s in pending]
        return "Pending servant salaries:\n" + "\n".join(lines)

    def _milk_answer(self, session, text: str) -> str:
        month = self._resolve_month(text)
        from sqlmodel import select

        from app.models.milk import MilkDelivery

        rows = session.exec(select(MilkDelivery).where(MilkDelivery.month == month)).all()
        if not rows:
            return f"No milk deliveries recorded for {month_name(month)}."
        total = sum(r.quantity * r.rate for r in rows)
        liters = sum(r.quantity for r in rows)
        pending = sum(r.quantity * r.rate for r in rows if r.payment_status == "pending")
        return (
            f"Milk summary for {month_name(month)}: {len(rows)} deliveries, "
            f"{liters:.2f} liters total, costing {format_money(total)} "
            f"(suppliers: {', '.join(sorted({r.supplier for r in rows}))}). "
            f"Pending amount: {format_money(pending)}."
        )

    def _newspaper_answer(self, session, text: str) -> str:
        month = self._resolve_month(text)
        from sqlmodel import select

        from app.models.newspaper import NewspaperDelivery

        rows = session.exec(select(NewspaperDelivery).where(NewspaperDelivery.month == month)).all()
        if not rows:
            return f"No newspaper subscriptions recorded for {month_name(month)}."
        total = sum(r.monthly_cost for r in rows)
        pending = [r.name for r in rows if r.payment_status == "pending"]
        return (
            f"Newspaper subscriptions for {month_name(month)}: {format_money(total)} total. "
            + (f"Pending: {', '.join(pending)}." if pending else "All paid.")
        )

    def _insight_answer(self, session, text: str) -> str:
        data = insight_service.compute_insights(session)
        lines = [
            f"Financial insights for {data['month_label']}:",
            f"- You spent {format_money(data['current_month_total'])} this month "
            f"({'up' if data['delta'] > 0 else 'down'} {abs(data['delta']):,.2f} vs last month).",
        ]
        if data["top_category"]:
            lines.append(f"- Top spending category: {data['top_category']}.")
        for cat in data["category_totals"][:3]:
            lines.append(f"- {cat['category']}: {format_money(cat['total'])}")
        if data["overspending"]:
            lines.append(f"- Overspending detected: {format_money(data['over_spent_by'])} above last month.")
        lines.append(f"- Pending payments total: {format_money(data['pending']['total'])}.")
        if data["savings_hints"]:
            lines.append("Savings suggestions:")
            lines.extend(f"  * {h}" for h in data["savings_hints"])
        else:
            lines.append("- No category exceeds 20% of spending; keep it up.")
        return "\n".join(lines)

    def _report_answer(self, session, month: str) -> str:
        data = insight_service.compute_insights(session, month)
        lines = [
            f"MONTHLY REPORT — {data['month_label']}",
            f"Total expenses: {format_money(data['current_month_total'])} ({data['expense_count']} transactions).",
            f"Previous month: {format_money(data['previous_month_total'])}.",
            "Category breakdown:",
        ]
        for cat in data["category_totals"]:
            lines.append(f"  - {cat['category']}: {format_money(cat['total'])}")
        lines.append(
            f"Pending payments: {format_money(data['pending']['total'])} "
            f"(servants {format_money(data['pending']['servant'])}, "
            f"milk {format_money(data['pending']['milk'])}, newspaper {format_money(data['pending']['newspaper'])})."
        )
        lines.append("Suggestions:")
        lines.extend(f"  - {h}" for h in data["savings_hints"] or ["No specific suggestions available."])
        return "\n".join(lines)

    def _help_answer(self, session) -> str:
        data = insight_service.compute_insights(session)
        return (
            "I'm your household finance assistant. I can query the database and analyze spending.\n\n"
            "Try asking things like:\n"
            "  - How much did I spend last month?\n"
            "  - Which servant salary is pending?\n"
            "  - Summarize my milk expenses for July.\n"
            "  - Give me financial insights.\n"
            "  - Generate a monthly report.\n\n"
            f"Quick status for {data['month_label']}: spent {format_money(data['current_month_total'])}, "
            f"pending payments {format_money(data['pending']['total'])}.\n\n"
            f"(Note: local LLM 'llama3' via Ollama is {'connected' if ollama_available() else 'not detected'} — "
            "running in fallback mode. Install Ollama and run `ollama pull llama3` for AI-powered answers.)"
        )


agent = AIAgent()
