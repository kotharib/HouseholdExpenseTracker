"""AI Agent: LangChain + Ollama with a deterministic, data-grounded fallback.

Behavior contract (applies to BOTH the LLM path and the fallback path):
- Always rely on actual SQLite data via the provided tools; never guess numbers.
- Provide a direct answer, then a transparent reasoning breakdown, then an insight.
- Admit uncertainty when data is missing; ask a clarifying question when vague.
- Stay within household tracking/billing; never recommend specific investments.

When a local Ollama server with the configured model is reachable, the agent
uses LangChain (SQLDatabaseToolkit + custom tools + ConversationBufferMemory).
Otherwise it falls back to a keyword-driven agent that queries the same data.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from app.config import settings
from app.database import engine
from app.services import insights as insight_service
from app.utils.helpers import format_money, last_month, month_name, month_range

MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}

# Data tools that back every analytical answer.
TOOL_BILL = "get_monthly_bill(year, month)"
TOOL_DELIVERY_SUMMARY = "get_delivery_summary(year, month)"
TOOL_MISSING = "get_missing_deliveries(year, month)"
TOOL_SQL = "run_sql_query(query)"

LLM_STYLE_INSTRUCTION = """\

Answering style (STRICT):
1. Direct Answer first: a short, clear statement of the result, using ₹.
2. Reasoning Breakdown: state exactly what data you fetched, how you processed it,
   and how the final number was derived. Use bullets. Never state a number you did
   not get from a tool or calculation.
3. Optional Insight: trends or suggestions based ONLY on the retrieved data.
4. ALWAYS call a tool when data is required (get_monthly_bill(year, month),
   get_delivery_summary(year, month), get_missing_deliveries(year, month),
   run_sql_query(query)). Never answer from memory or assumptions.
5. Formulas: Milk Bill = SUM(quantity x rate for delivered days);
   Newspaper Bill = monthly_cost x days_delivered.
6. If a tool returns empty results, say: "I could not find any records for that period."
7. If you lack data, say: "I don't have enough data to answer that precisely."
8. Stay strictly within household tracking and billing. Do NOT recommend specific
   investments or financial products. If asked, decline politely.
9. If a question is vague about a month, ask the user whether they want the summary
   for this month or a specific month."""


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
                temperature=0.0,
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
                    prompt = message + LLM_STYLE_INSTRUCTION
                else:
                    recent = history[-6:]
                    prompt = (
                        "Recent conversation:\n"
                        + "\n".join(f"{m['role']}: {m['content']}" for m in recent)
                        + f"\nuser: {message}"
                        + LLM_STYLE_INSTRUCTION
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
                            "produce financial insights for the current month. Follow the strict "
                            "answering format: direct answer, reasoning breakdown (what data was "
                            "fetched and how it was processed), then insights based only on that data."
                            + LLM_STYLE_INSTRUCTION
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
                            "totals, category breakdown, pending payments and savings suggestions "
                            "derived only from the fetched data."
                            + LLM_STYLE_INSTRUCTION
                        )
                    }
                )
                return str(result.get("output", "")).strip()
            except Exception:
                pass
        from app.ai.tools import _monthly_summary

        return _monthly_summary(target)


# ---------------------------------------------------------------------------
# Deterministic, data-grounded fallback agent
# ---------------------------------------------------------------------------
class FallbackAgent:
    # ------------------------------------------------------------- responses
    def respond(self, message: str) -> str:
        lowered = message.lower().strip()
        with self._session() as session:
            if self._is_investment_query(lowered):
                return self._investment_refusal()
            if any(k in lowered for k in ("insight", "analys", "analyz", "overspend")):
                return self._insight_answer(session, lowered)
            if self._is_missing_query(lowered):
                return self._missing_deliveries_answer(session, lowered)
            if self._is_bill_change_query(lowered):
                return self._bill_change_answer(session, lowered)
            if self._is_daily_query(lowered):
                return self._daily_answer(session, lowered)
            if self._is_delivery_query(lowered):
                return self._delivery_summary_answer(session, lowered)
            if "bill" in lowered:
                return self._bill_answer(session, lowered)
            if "report" in lowered:
                return self._report_answer(session, lowered)
            if "servant" in lowered or "salary" in lowered or "maid" in lowered:
                return self._servant_answer(session, lowered)
            if "milk" in lowered:
                return self._milk_answer(session, lowered)
            if "newspaper" in lowered or "paper" in lowered:
                return self._newspaper_answer(session, lowered)
            if any(k in lowered for k in ("spend", "expense", "money", "cost", "how much")):
                return self._spend_answer(session, lowered)
            return self._help_answer(session)

    # ------------------------------------------------------------- helpers
    def _session(self):
        from sqlmodel import Session

        return Session(engine)

    @staticmethod
    def _pct(part: float, total: float) -> str:
        if not total:
            return "0%"
        return f"{part / total * 100:.0f}%"

    @staticmethod
    def _clarify_month() -> str:
        return (
            "Do you want the summary for this month or a specific month? "
            "For example: 'this month', 'last month', 'July', or '2026-07'."
        )

    @staticmethod
    def _no_data(period: str | None = None) -> str:
        if period:
            return f"I could not find any records for {period}."
        return "I could not find any records for that period."

    @staticmethod
    def _resolve_month(text: str) -> str | None:
        """Resolve a YYYY-MM month mentioned in text, or None if none is given."""
        today = date.today()
        m = re.search(r"\b(\d{4})-(\d{2})\b", text)
        if m:
            return f"{m.group(1)}-{m.group(2)}"
        lowered = text.lower()
        if "last month" in lowered or "previous month" in lowered:
            prev = today.replace(day=1) - timedelta(days=1)
            return prev.strftime("%Y-%m")
        if "this month" in lowered or "current month" in lowered:
            return today.strftime("%Y-%m")
        for name, num in MONTH_NAMES.items():
            if name in lowered:
                year = today.year
                if "last year" in lowered:
                    year -= 1
                elif name in ("january", "february", "march") and today.month < num and "last" not in lowered:
                    year -= 1
                return f"{year}-{num:02d}"
        return None

    @staticmethod
    def _resolve_day(text: str) -> date | None:
        """Resolve a specific calendar day mentioned in text, or None."""
        today = date.today()
        lowered = text.lower()
        if "yesterday" in lowered:
            return today - timedelta(days=1)
        if "today" in lowered:
            return today
        m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
        if m:
            try:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                return None
        for name, num in MONTH_NAMES.items():
            if name in lowered:
                after = lowered[lowered.index(name) + len(name):]
                m = re.search(r"\b(\d{1,2})\b", after)
                if m:
                    try:
                        candidate = date(today.year, num, int(m.group(1)))
                    except ValueError:
                        return None
                    if candidate > today:
                        try:
                            candidate = date(today.year - 1, num, int(m.group(1)))
                        except ValueError:
                            return None
                    return candidate
        m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)\b", lowered)
        if m:
            try:
                candidate = date(today.year, today.month, int(m.group(1)))
            except ValueError:
                return None
            if candidate > today:
                try:
                    candidate = date(today.year - 1, today.month, int(m.group(1)))
                except ValueError:
                    return None
            return candidate
        m = re.search(r"\bon\s+(?:the\s+)?(\d{1,2})\b", lowered)
        if m:
            try:
                candidate = date(today.year, today.month, int(m.group(1)))
            except ValueError:
                return None
            if candidate > today:
                try:
                    candidate = date(today.year - 1, today.month, int(m.group(1)))
                except ValueError:
                    return None
            return candidate
        return None

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

    @staticmethod
    def _is_bill_change_query(text: str) -> bool:
        change_hint = any(k in text for k in ("higher", "lower", "increase", "decrease", "why is my bill", "why was my bill"))
        return change_hint and "bill" in text

    @staticmethod
    def _is_daily_query(text: str) -> bool:
        if FallbackAgent._resolve_day(text) is None:
            return False
        return any(k in text for k in ("milk", "newspaper", "paper", "delivery", "deliver", "arrive", "came", "today", "yesterday", "on "))

    @staticmethod
    def _is_investment_query(text: str) -> bool:
        return any(
            k in text
            for k in (
                "invest", "investing", "stock", "equity", "trading", "share market",
                "mutual fund", "mutual funds", "ppf", "nps", "sip", "elss",
                "portfolio", "asset allocation", "sukanya",
            )
        )

    def _investment_refusal(self) -> str:
        return (
            "I can't recommend specific investments or financial products — I'm focused "
            "on your household tracking and billing data. "
            "I can instead help with your milk and newspaper deliveries, monthly bills, "
            "expenses, and servant salaries."
        )

    # ------------------------------------------------ shared reasoning blocks
    def _reason_blocks(self) -> list[str]:
        return ["Reasoning:"]

    @staticmethod
    def _bill_reason_steps(month: str, details: dict) -> list[str]:
        milk_delivered = len(details["milk_details"])
        papers = len(details["newspaper_details"])
        steps = [
            f"- I fetched all milk, newspaper, servant and expense records for {month_name(month)} "
            f"(via {TOOL_BILL}).",
            "- Milk bill = SUM(quantity x rate) over the "
            f"{milk_delivered} delivered day(s); only delivered days are charged.",
            f"- Newspaper bill = monthly_cost x days_delivered for each of the {papers} paper(s).",
            "- Servant salaries are fixed monthly salaries; expenses are the recorded expense totals.",
            "- Adding all four components gives the grand total.",
        ]
        return steps

    # ------------------------------------------------- delivery & billing
    def _bill_answer(self, session, text: str) -> str:
        from app.services import delivery as delivery_service

        month = self._resolve_month(text)
        if month is None:
            return self._clarify_month()
        data = delivery_service.monthly_bill(session, month)
        if "milk bill" in text:
            return self._milk_bill_answer(data, month)
        if "newspaper bill" in text:
            return self._newspaper_bill_answer(data, month)

        grand = data["grand_total"]
        if grand <= 0 and not data["expense_details"] and not data["servant_details"]:
            return self._no_data(month_name(month))
        parts = {
            "milk": data["milk_bill"],
            "newspaper": data["newspaper_bill"],
            "servants": data["servant_salary_total"],
            "other expenses": data["expenses_total"],
        }
        top = max(parts, key=parts.get)
        lines = [
            f"Your {month_name(month)} bill is {format_money(grand)}.",
            "",
            "Reasoning:",
        ]
        lines.extend(self._bill_reason_steps(month, data))
        lines.append("")
        lines.append("Breakdown:")
        lines.append(f"- Milk: {format_money(data['milk_bill'])} ({self._pct(data['milk_bill'], grand)} of total).")
        lines.append(f"- Newspaper: {format_money(data['newspaper_bill'])} ({self._pct(data['newspaper_bill'], grand)} of total).")
        lines.append(f"- Servant salaries: {format_money(data['servant_salary_total'])} ({self._pct(data['servant_salary_total'], grand)} of total).")
        lines.append(f"- Expenses: {format_money(data['expenses_total'])} ({self._pct(data['expenses_total'], grand)} of total).")
        lines.append("")
        lines.append(
            "Insight: "
            f"{top} is the largest component ({self._pct(parts[top], grand)} of the bill). "
            + (
                "If you want to reduce the monthly outgo, this is the area with the most room to act."
                if top != "other expenses"
                else "Review your recorded expenses to see where the money is going."
            )
        )
        return "\n".join(lines)

    def _milk_bill_answer(self, data: dict, month: str) -> str:
        details = data["milk_details"]
        total = data["milk_bill"]
        if not details:
            return self._no_data(f"{month_name(month)} (no milk was delivered)")
        by_supplier: dict[str, list[dict]] = {}
        for d in details:
            by_supplier.setdefault(d["supplier"], []).append(d)
        lines = [
            f"Your milk bill for {month_name(month)} is {format_money(total)}, "
            f"for {len(details)} delivered day(s).",
            "",
            "Reasoning:",
            f"- I fetched all milk deliveries for {month_name(month)} (via {TOOL_BILL}).",
            "- I kept only the delivered days.",
            "- For each day I calculated quantity x rate.",
            "- Summing those values gives the total.",
            "",
            "Per-supplier breakdown:",
        ]
        for supplier, days in sorted(by_supplier.items()):
            sub_total = sum(d["total"] for d in days)
            liters = sum(d["quantity"] for d in days)
            lines.append(
                f"- {supplier}: {len(days)} day(s), {liters:.2f}L total, {format_money(sub_total)}."
            )
        return "\n".join(lines)

    def _newspaper_bill_answer(self, data: dict, month: str) -> str:
        details = data["newspaper_details"]
        total = data["newspaper_bill"]
        if not details:
            return self._no_data(f"{month_name(month)} (no newspapers recorded)")
        lines = [
            f"Your newspaper bill for {month_name(month)} is {format_money(total)} "
            f"across {len(details)} paper(s).",
            "",
            "Reasoning:",
            f"- I fetched all newspaper deliveries for {month_name(month)} (via {TOOL_BILL}).",
            "- For each paper I counted delivered days (delivery_status = delivered).",
            "- Newspaper bill = monthly_cost x days_delivered per paper.",
            "- Summing across papers gives the total.",
            "",
            "Per-paper breakdown:",
        ]
        for nd in details:
            lines.append(
                f"- {nd['name']}: {format_money(nd['monthly_cost'])}/day x "
                f"{nd['days_delivered']} delivered days = {format_money(nd['total'])}."
            )
        return "\n".join(lines)

    def _bill_change_answer(self, session, text: str) -> str:
        from app.services import delivery as delivery_service

        month = self._resolve_month(text)
        if month is None:
            return self._clarify_month()
        prev = last_month(month)
        cur = delivery_service.monthly_bill(session, month)
        old = delivery_service.monthly_bill(session, prev)
        diff = cur["grand_total"] - old["grand_total"]

        parts = [
            ("milk bill", cur["milk_bill"], old["milk_bill"]),
            ("newspaper bill", cur["newspaper_bill"], old["newspaper_bill"]),
            ("servant salaries", cur["servant_salary_total"], old["servant_salary_total"]),
            ("expenses", cur["expenses_total"], old["expenses_total"]),
        ]
        deltas = [(name, c - o, c, o) for name, c, o in parts]

        direction = "higher" if diff > 0 else ("lower" if diff < 0 else "the same as")
        lines = [
            f"Your {month_name(month)} bill is {format_money(cur['grand_total'])}, "
            f"{direction} than {month_name(prev)} ({format_money(old['grand_total'])}) "
            f"by {format_money(abs(diff))}.",
            "",
            "Reasoning:",
            f"- I fetched the full monthly bill for both {month_name(month)} and {month_name(prev)} "
            f"(via {TOOL_BILL}).",
            "- Each bill = milk (quantity x rate for delivered days) + newspaper "
            "(monthly_cost x delivered days) + servant salaries + expenses.",
            "- I compared each component between the two months:",
        ]
        for name, d, c, o in sorted(deltas, key=lambda x: abs(x[1]), reverse=True):
            verb = "increased" if d > 0 else ("decreased" if d < 0 else "stayed the same")
            lines.append(
                f"  - {name}: {format_money(o)} -> {format_money(c)} ({verb} by {format_money(abs(d))})."
            )
        driver = max(deltas, key=lambda x: abs(x[1]))
        if driver[1] > 0:
            lines.append(
                f"- The main driver of the change is {driver[0]}, which added "
                f"{format_money(driver[1])} to the bill."
            )
        elif driver[1] < 0:
            lines.append(
                f"- The main reason the bill fell is {driver[0]}, which dropped by "
                f"{format_money(abs(driver[1]))}."
            )
        if "expenses" in driver[0] and driver[1] > 0:
            cur_cats = {c["category"]: c["total"] for c in insight_service.category_totals(session, month)}
            prev_cats = {c["category"]: c["total"] for c in insight_service.category_totals(session, prev)}
            cat_deltas = sorted(
                ((cat, cur_cats.get(cat, 0) - prev_cats.get(cat, 0)) for cat in set(cur_cats) | set(prev_cats)),
                key=lambda x: x[1],
                reverse=True,
            )
            top_gainer = next((c for c, d in cat_deltas if d > 0), None)
            if top_gainer:
                lines.append(
                    f"- Within expenses, {top_gainer} grew the most "
                    f"({format_money(next(d for c, d in cat_deltas if c == top_gainer))}) and is worth reviewing."
                )
        lines.append("")
        lines.append(
            "Insight: the comparison above is based entirely on recorded data; "
            "no amounts were estimated."
        )
        return "\n".join(lines)

    def _delivery_summary_answer(self, session, text: str) -> str:
        from app.services import delivery as delivery_service

        month = self._resolve_month(text)
        if month is None:
            return self._clarify_month()
        if "newspaper" in text and "milk" not in text:
            data = delivery_service.newspaper_daily_summary(session, month)
            if not data["newspapers"]:
                return self._no_data(month_name(month))
            lines = [
                f"Newspaper deliveries for {month_name(month)}: {data['total_delivered']} delivered "
                f"days and {data['missed_days']} missed days across {len(data['newspapers'])} paper(s).",
                "",
                "Reasoning:",
                f"- I fetched the daily newspaper records for {month_name(month)} "
                f"(via {TOOL_DELIVERY_SUMMARY}).",
                "- I expanded each paper across the full calendar month and counted "
                "delivered vs missed days.",
                "- The numbers below are the exact figures used for billing.",
                "",
                "Per-paper breakdown:",
            ]
            for g in data["newspapers"]:
                pct = g["days_delivered"] / g["days_total"] * 100 if g["days_total"] else 0
                lines.append(
                    f"- {g['name']}: {g['days_delivered']}/{g['days_total']} days "
                    f"({pct:.0f}%), billed at {format_money(g['total'])}."
                )
            if data["missed_days"]:
                saved = sum(g["monthly_cost"] * (g["days_total"] - g["days_delivered"]) for g in data["newspapers"])
                lines.append(
                    "",
                    "Insight: since you pay per delivered day, the missed days saved "
                    f"{format_money(saved)} on the paper bill this month."
                )
            else:
                lines.append("")
                lines.append("Insight: no deliveries were missed — every paper arrived every day.")
            return "\n".join(lines)
        if "milk" in text and "newspaper" not in text:
            data = delivery_service.milk_daily_summary(session, month)
            if not data["days"]:
                return self._no_data(month_name(month))
            delivered_bill = sum(d["total"] for d in data["days"] if d["delivered"])
            lines = [
                f"Milk deliveries for {month_name(month)}: {data['delivered_days']} delivered "
                f"and {data['missed_days']} missed out of {len(data['days'])} recorded days.",
                "",
                "Reasoning:",
                f"- I fetched the daily milk records for {month_name(month)} "
                f"(via {TOOL_DELIVERY_SUMMARY}).",
                "- I counted delivered vs missed days.",
                f"- The billed amount is {format_money(delivered_bill)} = SUM(quantity x rate) "
                "over delivered days only.",
            ]
            if data["missed_days"]:
                missed_cost = sum(d["total"] for d in data["days"] if not d["delivered"])
                lines.append("")
                lines.append(
                    "Insight: the "
                    f"{data['missed_days']} missed day(s) would have added {format_money(missed_cost)} "
                    "to the bill had they been delivered."
                )
            else:
                lines.append("")
                lines.append("Insight: no missed deliveries — all recorded days were delivered.")
            return "\n".join(lines)
        milk = delivery_service.milk_daily_summary(session, month)
        papers = delivery_service.newspaper_daily_summary(session, month)
        lines = [
            f"Delivery summary for {month_name(month)}: "
            f"{milk['missed_days'] + papers['missed_days']} missed deliveries in total.",
            "",
            "Reasoning:",
            f"- I fetched daily milk and newspaper records (via {TOOL_DELIVERY_SUMMARY}).",
            f"- Milk: {milk['delivered_days']} delivered, {milk['missed_days']} missed "
            f"out of {len(milk['days'])} recorded days.",
            f"- Newspaper: {papers['total_delivered']} delivered days, {papers['missed_days']} "
            f"missed across {len(papers['newspapers'])} paper(s):",
        ]
        for g in papers["newspapers"]:
            pct = g["days_delivered"] / g["days_total"] * 100 if g["days_total"] else 0
            lines.append(f"  - {g['name']}: {g['days_delivered']}/{g['days_total']} days ({pct:.0f}%).")
        if not papers["newspapers"]:
            lines.append("  - No newspapers recorded.")
        lines.append("")
        lines.append(
            "Insight: milk is tracked per recorded day; newspaper is expanded per calendar "
            "day. These are the exact figures used for billing.",
        )
        return "\n".join(lines)

    def _missing_deliveries_answer(self, session, text: str) -> str:
        from app.services import delivery as delivery_service

        month = self._resolve_month(text)
        if month is None:
            return self._clarify_month()
        missed = delivery_service.missing_deliveries(session, month)
        if not missed:
            return (
                f"There were no missed milk or newspaper deliveries in {month_name(month)}.\n\n"
                f"Reasoning: I queried the daily delivery records for {month_name(month)} "
                f"via {TOOL_MISSING} and found no day marked as not delivered."
            )
        milk_count = sum(1 for m in missed if m["type"] == "milk")
        paper_count = sum(1 for m in missed if m["type"] == "newspaper")
        by_day: dict[str, set[str]] = {}
        for item in missed:
            by_day.setdefault(item["date"], set()).add(item["type"])
        mixed_days = sorted(d for d, types in by_day.items() if types == {"milk", "newspaper"})
        multi_days = sorted(d for d, types in by_day.items() if len(types) > 1)
        lines = [
            f"There were {len(missed)} missed deliveries in {month_name(month)} "
            f"({milk_count} milk, {paper_count} newspaper).",
            "",
            "Reasoning:",
            f"- I fetched the daily delivery records for {month_name(month)} via {TOOL_MISSING}.",
            "- I kept every day where milk is_delivered = false or a paper has delivery_status = false.",
            "",
            "Missed days:",
        ]
        for item in missed:
            lines.append(f"- {item['date']} ({item['type']}): {item['detail']}")
        if mixed_days:
            lines.append(
                f"- On {len(mixed_days)} day(s) BOTH milk and newspaper were missed "
                f"({', '.join(mixed_days[:5])}{'...' if len(mixed_days) > 5 else ''}) — "
                "worth checking with the suppliers for a shared cause."
            )
        elif multi_days:
            lines.append(
                f"- On {len(multi_days)} day(s) more than one delivery was missed "
                f"({', '.join(multi_days[:5])}{'...' if len(multi_days) > 5 else ''})."
            )
        lines.append("")
        lines.append(
            "Insight: you only pay for delivered days, so these missed deliveries reduce "
            "this month's milk and newspaper bill.",
        )
        return "\n".join(lines)

    def _daily_answer(self, session, text: str) -> str:
        from sqlmodel import select

        from app.models.milk import MilkDelivery
        from app.models.newspaper import NewspaperDelivery

        day = self._resolve_day(text)
        if day is None:
            return (
                "I don't have enough data to answer that precisely. "
                "Please tell me the exact date (e.g. 'August 5' or '2026-08-05')."
            )
        milk_rows = session.exec(select(MilkDelivery).where(MilkDelivery.date == day)).all()
        paper_rows = session.exec(
            select(NewspaperDelivery).where(NewspaperDelivery.date == day)
        ).all()
        if not milk_rows and not paper_rows:
            return self._no_data(day.isoformat())
        lines = [
            f"Deliveries on {day.isoformat()} ({day.strftime('%A')}):",
            "",
            "Reasoning:",
            f"- I queried the milk_deliveries and newspaper_deliveries tables for {day.isoformat()} "
            f"(via {TOOL_SQL}).",
            "",
        ]
        if milk_rows:
            for r in milk_rows:
                status = "delivered" if r.is_delivered else "NOT delivered"
                lines.append(
                    f"- Milk ({r.supplier}): {r.quantity:g}L x {format_money(r.rate)} = "
                    f"{format_money(r.quantity * r.rate)} — {status}."
                )
        else:
            lines.append("- Milk: no record for this day.")
        if paper_rows:
            for r in paper_rows:
                status = "delivered" if r.delivery_status else "NOT delivered"
                lines.append(
                    f"- {r.name}: {status} (daily cost {format_money(r.monthly_cost)})."
                )
        else:
            lines.append("- Newspaper: no record for this day.")
        return "\n".join(lines)

    # ------------------------------------------------------ spend & payroll
    def _spend_answer(self, session, text: str) -> str:
        from sqlmodel import select

        from app.models.expense import Expense

        month = self._resolve_month(text)
        if month is None:
            return self._clarify_month()
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
        delta_pct = (delta / prev_total * 100) if prev_total else 0.0
        top: dict[str, float] = {}
        for e in rows:
            top[e.category] = top.get(e.category, 0.0) + e.amount
        top_items = sorted(top.items(), key=lambda x: x[1], reverse=True)[:3]
        lines = [
            f"You spent {format_money(total)} in {month_name(month)} across {len(rows)} expenses.",
            "",
            "Reasoning:",
            f"- I fetched all expense rows with dates in {month_name(month)} (via {TOOL_SQL}).",
            "- I summed their amounts to get the total.",
            "- I also summed the previous month ({format_money(prev_total)}) for comparison.",
            "",
        ]
        if prev_total:
            if delta > 0:
                lines.append(
                    f"Insight: spending is {delta_pct:.0f}% ({format_money(delta)}) higher than "
                    "last month — the main change to watch."
                )
            elif delta < 0:
                lines.append(
                    f"Insight: spending is {delta_pct:.0f}% ({format_money(abs(delta))}) lower than "
                    "last month — trending down."
                )
            else:
                lines.append("Insight: spending is level with last month.")
        else:
            lines.append("Insight: no previous-month expenses to compare against.")
        lines.append("Top categories and their share:")
        for cat, amt in top_items:
            lines.append(f"- {cat}: {format_money(amt)} ({self._pct(amt, total)} of spending).")
        if not top_items:
            lines.append("- No expenses recorded this month.")
        return "\n".join(lines)

    def _servant_answer(self, session, text: str) -> str:
        from sqlmodel import select

        from app.models.servant import Servant

        all_s = session.exec(select(Servant)).all()
        if not all_s:
            return "No servants are registered yet."
        pending = [s for s in all_s if s.payment_status == "pending"]
        if "pending" in text or pending:
            if not pending:
                return (
                    "All servant salaries are paid.\n\n"
                    "Reasoning: I checked the servants table (via run_sql_query(query)) and no "
                    f"servant has payment_status = 'pending' ({len(all_s)} on record)."
                )
            pending_total = sum(s.monthly_salary for s in pending)
            lines = [
                f"{len(pending)} servant salary(ies) are pending, totalling {format_money(pending_total)}.",
                "",
                "Reasoning:",
                "- I fetched the servants table (via run_sql_query(query)).",
                "- I kept rows where payment_status = 'pending'.",
                "- I summed their monthly_salary values.",
                "",
                "Pending:",
            ]
            for s in pending:
                lines.append(f"- {s.name} ({s.role}): {format_money(s.monthly_salary)} pending.")
            return "\n".join(lines)
        total = sum(s.monthly_salary for s in all_s)
        lines = [
            f"Servant payroll has {len(all_s)} servant(s) at {format_money(total)}/month in total.",
            "",
            "Reasoning: I fetched the servants table (via run_sql_query(query)) and summed the "
            "monthly_salary values.",
            "",
        ]
        for s in all_s:
            lines.append(f"- {s.name} ({s.role}): {format_money(s.monthly_salary)}/month — {s.payment_status}.")
        return "\n".join(lines)

    # ------------------------------------------------------- milk & newspaper
    def _milk_answer(self, session, text: str) -> str:
        from sqlmodel import select

        from app.models.milk import MilkDelivery

        month = self._resolve_month(text)
        if month is None:
            return self._clarify_month()
        rows = session.exec(select(MilkDelivery).where(MilkDelivery.month == month)).all()
        if not rows:
            return self._no_data(month_name(month))
        delivered = sum(1 for r in rows if r.is_delivered)
        missed = len(rows) - delivered
        total = sum(r.quantity * r.rate for r in rows)
        liters = sum(r.quantity for r in rows)
        pending = sum(r.quantity * r.rate for r in rows if r.payment_status == "pending")
        paid = total - pending
        by_supplier: dict[str, list[MilkDelivery]] = {}
        for r in rows:
            by_supplier.setdefault(r.supplier, []).append(r)
        lines = [
            f"Milk summary for {month_name(month)}: {len(rows)} record(s), "
            f"{delivered} delivered, {missed} missed, {liters:.2f}L, {format_money(total)}.",
            "",
            "Reasoning:",
            f"- I fetched all milk deliveries for {month_name(month)} (via {TOOL_SQL}).",
            "- I counted delivered vs missed days (is_delivered).",
            "- Cost = SUM(quantity x rate); only delivered days are billed.",
            "",
            "Per-supplier breakdown:",
        ]
        for supplier, supplier_rows in sorted(by_supplier.items()):
            sub = sum(r.quantity * r.rate for r in supplier_rows)
            sub_delivered = sum(1 for r in supplier_rows if r.is_delivered)
            lines.append(
                f"- {supplier}: {sub_delivered} delivered / {len(supplier_rows) - sub_delivered} missed, "
                f"{format_money(sub)}."
            )
        lines.append("")
        lines.append(f"Payment status: {format_money(paid)} paid, {format_money(pending)} pending.")
        if missed:
            lines.append(
                f"Insight: {missed} day(s) were marked not delivered, which reduced the bill."
            )
        return "\n".join(lines)

    def _newspaper_answer(self, session, text: str) -> str:
        from sqlmodel import select

        from app.models.newspaper import NewspaperDelivery

        month = self._resolve_month(text)
        if month is None:
            return self._clarify_month()
        rows = session.exec(select(NewspaperDelivery).where(NewspaperDelivery.month == month)).all()
        if not rows:
            return self._no_data(month_name(month))
        by_name: dict[str, list[NewspaperDelivery]] = {}
        for r in rows:
            by_name.setdefault(r.name, []).append(r)
        total = sum(r.monthly_cost for r in rows)
        pending = sorted({r.name for r in rows if r.payment_status == "pending"})
        lines = [
            f"Newspaper subscriptions for {month_name(month)}: {format_money(total)} total "
            f"across {len(by_name)} paper(s).",
            "",
            "Reasoning:",
            f"- I fetched all newspaper deliveries for {month_name(month)} (via {TOOL_SQL}).",
            "- I grouped by paper name and summed monthly_cost.",
            "- Billing is prorated per delivered day (monthly_cost x days_delivered).",
            "",
            "Per-paper breakdown:",
        ]
        for name, name_rows in sorted(by_name.items()):
            delivered = sum(1 for r in name_rows if r.delivery_status)
            lines.append(f"- {name}: {delivered} delivered days, {format_money(name_rows[0].monthly_cost)}.")
        lines.append("")
        lines.append(
            f"Payment status: " + ("pending for " + ", ".join(pending) + "." if pending else "all paid.")
        )
        return "\n".join(lines)

    # ------------------------------------------------------- insights & report
    def _insight_answer(self, session, text: str) -> str:
        data = insight_service.compute_insights(session)
        total = data["current_month_total"]
        prev = data["previous_month_total"]
        delta_pct = (data["delta"] / prev * 100) if prev else 0.0
        lines = [
            f"Financial insights for {data['month_label']}:",
            f"- You spent {format_money(total)} this month "
            f"({'up' if data['delta'] > 0 else 'down'} {format_money(abs(data['delta']))} "
            f"({delta_pct:+.0f}%) vs last month).",
            "",
            "Reasoning:",
            "- I aggregated all expenses for this month and the previous month from the database.",
            "- I summed totals by month and grouped them by category.",
            "- I compared this month against last month to compute the change.",
            "",
            "Observations (based only on the data):",
        ]
        if data["top_category"] and data["category_totals"]:
            top_amt = data["category_totals"][0]["total"]
            lines.append(
                f"- Top category: {data['top_category']} at {format_money(top_amt)} "
                f"({self._pct(top_amt, total)} of spending)."
            )
        for cat in data["category_totals"][:3]:
            lines.append(f"  - {cat['category']}: {format_money(cat['total'])} ({self._pct(cat['total'], total)}).")
        if data["overspending"]:
            lines.append(
                f"- Overspending detected: {format_money(data['over_spent_by'])} above last month "
                f"({delta_pct:+.0f}%)."
            )
        lines.append(f"- Pending payments: {format_money(data['pending']['total'])}.")
        if data["savings_hints"]:
            lines.append("Suggestions:")
            lines.extend(f"  - {h}" for h in data["savings_hints"])
        else:
            lines.append("- No category exceeds 20% of spending; the mix looks balanced.")
        return "\n".join(lines)

    def _report_answer(self, session, text: str) -> str:
        month = self._resolve_month(text)
        if month is None:
            return self._clarify_month()
        data = insight_service.compute_insights(session, month)
        total = data["current_month_total"]
        prev = data["previous_month_total"]
        delta_pct = (data["delta"] / prev * 100) if prev else 0.0
        lines = [
            f"MONTHLY REPORT — {data['month_label']}",
            "",
            f"Total expenses: {format_money(total)} ({data['expense_count']} transactions).",
            f"Previous month: {format_money(prev)} "
            f"({'+' if data['delta'] >= 0 else ''}{format_money(data['delta'])}, {delta_pct:+.0f}%).",
            "",
            "Reasoning:",
            "- I aggregated expenses for this month and the previous month from the database.",
            "- I summed totals by month and grouped by category to build the breakdown.",
            "",
            "Category breakdown (share of spending):",
        ]
        for cat in data["category_totals"]:
            lines.append(f"  - {cat['category']}: {format_money(cat['total'])} ({self._pct(cat['total'], total)}).")
        if not data["category_totals"]:
            lines.append("  - No expenses recorded this month.")
        lines.append("")
        lines.append(
            f"Pending payments: {format_money(data['pending']['total'])} "
            f"(servants {format_money(data['pending']['servant'])}, "
            f"milk {format_money(data['pending']['milk'])}, newspaper {format_money(data['pending']['newspaper'])}).",
        )
        if data["overspending"]:
            lines.append(
                f"Overspending flag: you spent {format_money(data['over_spent_by'])} more than last month."
            )
        lines.append("Suggestions (from the data):")
        lines.extend(f"  - {h}" for h in data["savings_hints"] or ["No category exceeds 20% of spending — the mix looks balanced."])
        return "\n".join(lines)

    # ---------------------------------------------------------------- misc
    def _help_answer(self, session) -> str:
        data = insight_service.compute_insights(session)
        return (
            "I'm your household finance assistant. I answer from the actual records in your "
            "database — I never guess numbers.\n\n"
            "Try asking things like:\n"
            "  - How much did I spend last month?\n"
            "  - Which servant salary is pending?\n"
            "  - What is my milk bill for July?\n"
            "  - What is my newspaper bill for August?\n"
            "  - How many milk deliveries happened this month?\n"
            "  - Which days did newspaper not arrive?\n"
            "  - What happened on August 5 for deliveries?\n"
            "  - Why is my bill higher this month?\n"
            "  - Generate my monthly bill summary.\n"
            "  - Give me financial insights.\n\n"
            f"Quick status for {data['month_label']}: spent {format_money(data['current_month_total'])}, "
            f"pending payments {format_money(data['pending']['total'])}.\n\n"
            f"(Note: local LLM via Ollama is {'connected' if ollama_available() else 'not detected'} — "
            "running on the deterministic data-grounded engine.)"
        )


agent = AIAgent()
