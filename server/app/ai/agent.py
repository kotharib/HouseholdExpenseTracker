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
            if any(k in lowered for k in ("invest", "mutual fund", "ppf", "nps", "sip", "elss", "portfolio", "asset allocation")):
                return self._investment_answer(lowered)
            if any(k in lowered for k in ("insight", "analys", "analyz", "overspend", "suggest")):
                return self._insight_answer(session, lowered)
            if self._is_missing_query(lowered):
                return self._missing_deliveries_answer(session, lowered)
            if self._is_delivery_query(lowered):
                return self._delivery_summary_answer(session, lowered)
            if "bill" in lowered:
                return self._bill_answer(session, lowered)
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

    @staticmethod
    def _is_delivery_query(text: str) -> bool:
        return any(k in text for k in ("delivery", "deliveries", "delivered"))

    @staticmethod
    def _is_missing_query(text: str) -> bool:
        missed_hint = any(
            k in text
            for k in (
                "missing", "missed", "not arrive", "didn't arrive",
                "did not arrive", "not delivered", "skipped",
            )
        )
        return missed_hint and (
            FallbackAgent._is_delivery_query(text)
            or "milk" in text
            or "newspaper" in text
        )

    # ------------------------------------------------- delivery & billing
    def _bill_answer(self, session, text: str) -> str:
        from app.services import delivery as delivery_service

        month = self._resolve_month(text)
        data = delivery_service.monthly_bill(session, month)
        if "milk bill" in text:
            return (
                f"Milk bill for {month_name(month)}: {format_money(data['milk_bill'])} "
                f"across {len(data['milk_details'])} delivered days."
            )
        if "newspaper bill" in text:
            lines = [
                f"Newspaper bill for {month_name(month)}: {format_money(data['newspaper_bill'])}"
            ]
            for nd in data["newspaper_details"]:
                lines.append(
                    f"  - {nd['name']}: {format_money(nd['monthly_cost'])} x "
                    f"{nd['days_delivered']} days = {format_money(nd['total'])}"
                )
            return "\n".join(lines)
        lines = [
            f"MONTHLY BILL — {month_name(month)}",
            f"Milk bill: {format_money(data['milk_bill'])}",
            f"Newspaper bill: {format_money(data['newspaper_bill'])}",
            f"Servant salaries: {format_money(data['servant_salary_total'])}",
            f"Expenses: {format_money(data['expenses_total'])}",
            f"GRAND TOTAL: {format_money(data['grand_total'])}",
        ]
        return "\n".join(lines)

    def _delivery_summary_answer(self, session, text: str) -> str:
        from app.services import delivery as delivery_service

        month = self._resolve_month(text)
        if "newspaper" in text and "milk" not in text:
            data = delivery_service.newspaper_daily_summary(session, month)
            if not data["newspapers"]:
                return f"No newspaper deliveries recorded for {month_name(month)}."
            lines = [
                f"Newspaper deliveries for {month_name(month)} "
                f"({data['total_delivered']} delivered days):"
            ]
            for g in data["newspapers"]:
                lines.append(f"  - {g['name']}: {g['days_delivered']}/{g['days_total']} days delivered")
            return "\n".join(lines)
        if "milk" in text and "newspaper" not in text:
            data = delivery_service.milk_daily_summary(session, month)
            if not data["days"]:
                return f"No milk deliveries recorded for {month_name(month)}."
            return (
                f"Milk deliveries for {month_name(month)}: {data['delivered_days']} delivered days, "
                f"{data['missed_days']} missed days."
            )
        milk = delivery_service.milk_daily_summary(session, month)
        papers = delivery_service.newspaper_daily_summary(session, month)
        paper_lines = [
            f"  - {g['name']}: {g['days_delivered']}/{g['days_total']} days"
            for g in papers["newspapers"]
        ]
        return (
            f"Delivery summary for {month_name(month)}:\n"
            f"- Milk: {milk['delivered_days']} delivered, {milk['missed_days']} missed.\n"
            + ("\n".join(paper_lines) if paper_lines else "- No newspapers recorded.")
        )

    def _missing_deliveries_answer(self, session, text: str) -> str:
        from app.services import delivery as delivery_service

        month = self._resolve_month(text)
        missed = delivery_service.missing_deliveries(session, month)
        if not missed:
            return f"No missed milk or newspaper deliveries for {month_name(month)}."
        lines = [f"Missed deliveries for {month_name(month)} ({len(missed)}):"]
        for item in missed:
            lines.append(f"- {item['date']} ({item['type']}): {item['detail']}")
        return "\n".join(lines)

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

    def _investment_answer(self, text: str) -> str:
        from app.ai.tools import _investment_advice
        from app.services import investment_advisor

        amount = 0.0
        numbers = re.findall(r"(?:₹|rs\.?|rs)?\s*([\d,]+)", text)
        if numbers:
            try:
                amount = float(numbers[0].replace(",", ""))
            except ValueError:
                amount = 0.0
        profile = "moderate"
        for candidate in ("conservative", "moderate", "aggressive"):
            if candidate in text:
                profile = candidate
                break
        if "profile" in text and not any(p in text for p in ("conservative", "moderate", "aggressive")):
            lines = ["Choose a risk profile to get a custom allocation:"]
            for p in investment_advisor.risk_profiles():
                lines.append(f"- {p['key']}: {p['label']}")
            lines.append(
                "\nExample: 'Suggest investments for ₹1,00,000 with an aggressive profile.'"
            )
            return "\n".join(lines)
        return _investment_advice(str(amount), profile)

    def _help_answer(self, session) -> str:
        data = insight_service.compute_insights(session)
        return (
            "I'm your household finance assistant. I can query the database and analyze spending.\n\n"
            "Try asking things like:\n"
            "  - How much did I spend last month?\n"
            "  - Which servant salary is pending?\n"
            "  - Summarize my milk expenses for July.\n"
            "  - What is my milk bill for July?\n"
            "  - How many newspaper deliveries happened this month?\n"
            "  - Which days did milk not arrive?\n"
            "  - Generate my monthly bill summary.\n"
            "  - Give me financial insights.\n"
            "  - Generate a monthly report.\n"
            "  - Suggest investments for ₹1,00,000 (conservative profile).\n\n"
            f"Quick status for {data['month_label']}: spent {format_money(data['current_month_total'])}, "
            f"pending payments {format_money(data['pending']['total'])}.\n\n"
            f"(Note: local LLM 'llama3' via Ollama is {'connected' if ollama_available() else 'not detected'} — "
            "running in fallback mode. Install Ollama and run `ollama pull llama3` for AI-powered answers.)"
        )


agent = AIAgent()
