"""Diagram generators producing ASCII and SVG output.

These are intentionally dependency-free (pure string templates) so the
application never requires graphviz or similar packages.
"""

from __future__ import annotations

import html
from typing import Any


def _svg_doc(boxes: list[tuple[str, str, str, str]], arrows: list[tuple[int, int, str, str]], width=1000, height=360) -> str:
    """Render boxes + arrows as an SVG document.

    box: (id, label, x, y)
    arrow: (from_box_idx, to_box_idx, label, bend)
    """
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<defs>'
        '<marker id="arrow" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">'
        '<polygon points="0 0, 10 3.5, 0 7" fill="#4c7af0"/></marker>'
        '<style>.dbox{fill:#f4f7ff;stroke:#4c7af0;stroke-width:1.5;rx:8}</style>'
        '<style>.dlabel{font-family:monospace;font-size:13px;fill:#1c2536}</style>'
        '<style>.dsub{font-family:monospace;font-size:10px;fill:#6b7488}</style>'
        '<style>.darrow{stroke:#4c7af0;stroke-width:1.5;fill:none;marker-end:url(#arrow)}</style>'
        '<style>.darrowlabel{font-family:monospace;font-size:10px;fill:#8a93a8}</style>'
        '</defs>'
    ]
    for bid, label, sub, (x, y) in boxes:
        parts.append(
            f'<g><rect class="dbox" x="{x}" y="{y}" width="170" height="56"/>'
            f'<text class="dlabel" x="{x + 85}" y="{y + 24}" text-anchor="middle">{html.escape(label)}</text>'
            f'<text class="dsub" x="{x + 85}" y="{y + 43}" text-anchor="middle">{html.escape(sub)}</text></g>'
        )
    for fi, ti, label, bend in arrows:
        fx, fy = boxes[fi][3][0] + 170, boxes[fi][3][1] + 28
        tx, ty = boxes[ti][3][0], boxes[ti][3][1] + 28
        if bend:
            mid = (fx + tx) / 2
            d = f"M {fx} {fy} C {mid} {fy}, {mid} {ty}, {tx} {ty}"
        else:
            d = f"M {fx} {fy} L {tx} {ty}"
        parts.append(f'<path class="darrow" d="{d}"/>')
        if label:
            mx, my = (fx + tx) / 2, (fy + ty) / 2 - 8
            parts.append(
                f'<text class="darrowlabel" x="{mx}" y="{my}" text-anchor="middle">{html.escape(label)}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def _ascii_flow(nodes: list[tuple[str, str]], arrows: list[str]) -> str:
    lines: list[str] = []
    lines.append("  " + "  ".join(n[0] for n in nodes))
    lines.append("  " + "  ".join("|" + " " * (len(n[0]) - 1) for n in nodes))
    lines.append("  " + "  ".join(arrow for arrow in arrows))
    for label, sub in nodes:
        lines.append(f"    {label}")
        lines.append(f"    {sub}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Architecture diagram
# ---------------------------------------------------------------------------
def architecture() -> dict[str, str]:
    ascii_art = """+------------------------+       +-------------------------+       +----------------------+
|   React SPA (frontend)  |       |    FastAPI (backend)    |       |    SQLite Database    |
|  Vite + TS + MUI + AX   |  ---> |  REST API / JWT Auth   |  ---> |   expenses / servants  |
|  /api reverse proxy     |  HTTP |  Pydantic validation   |  SQL  |   milk / newspaper     |
+------------+-----------+       +-----------+------------+       +-----------+----------+
             |                             |                                 ^
             |                             |                                 |
             |                     +-------+--------+                        |
             +---------------------+  AI Agent     +-------------------------+
                                   |  LangChain    |   SQLDatabaseToolkit
                                   |  Ollama/llama3|   custom Python tools
                                   +-------+-------+
                                           |
                                           v
                                  +-----------------+
                                  |  Reports + PDF  |
                                  |  ReportLab      |
                                  |  Diagrams/SVG   |
                                  +-----------------+
"""
    boxes = [
        ("fe", "React SPA", "Vite / TS / MUI", (40, 70)),
        ("api", "FastAPI", "REST + JWT /api", (300, 70)),
        ("db", "SQLite", "tables + indexes", (560, 70)),
        ("ai", "AI Agent", "LangChain + Ollama", (300, 230)),
        ("rep", "Reports", "PDF + SVG / ASCII", (560, 230)),
    ]
    arrows = [
        (0, 1, "HTTP /api", True),
        (1, 2, "SQLAlchemy", False),
        (1, 3, "tools + queries", True),
        (3, 2, "read/write", True),
        (3, 4, "insights", False),
    ]
    return {
        "name": "architecture",
        "ascii": ascii_art,
        "svg": _svg_doc(boxes, arrows),
        "description": "React -> FastAPI -> SQLite -> AI Agent -> Reports",
    }


# ---------------------------------------------------------------------------
# ER diagram
# ---------------------------------------------------------------------------
def er() -> dict[str, str]:
    ascii_art = """+----------------------------+     +----------------------------+
|           users            |     |         expenses            |
|----------------------------|     |-----------------------------|
| PK id                      |     | PK id                       |
|    username   unique       |     |    category      index      |
|    password_hash           |     |    amount                   |
|    role                    |     |    date         index       |
+----------------------------+     |    notes / payment_mode /   |
                                   |    tags                      |
                                   +-----------------------------+
+----------------------------+     +----------------------------+
|         servants           |     |      milk_deliveries       |
|----------------------------|     |-----------------------------|
| PK id                      |     | PK id                       |
|    name        index       |     |    supplier     index       |
|    role                    |     |    quantity / rate          |
|    monthly_salary          |     |    date / month index       |
|    payment_status          |     |    payment_status           |
|    attendance_count        |     +----------------------------+
+----------------------------+
                                   +----------------------------+
+----------------------------+     |   newspaper_deliveries     |
|  (users authorize access)  |     |-----------------------------|
|   expenses/servants/milk/  |     | PK id                       |
|   newspaper -> user owns   |     |    name         index       |
+----------------------------+     |    monthly_cost             |
                                   |    month        index       |
                                   |    payment_status           |
                                   +----------------------------+
"""
    boxes = [
        ("users", "users", "PK id, username, role", (30, 40)),
        ("expenses", "expenses", "PK id, category, amount, date", (300, 40)),
        ("servants", "servants", "PK id, name, role, salary", (30, 170)),
        ("milk", "milk_deliveries", "PK id, supplier, qty, rate", (300, 170)),
        ("newspaper", "newspaper_deliveries", "PK id, name, cost, month", (565, 170)),
    ]
    arrows = [(0, 1, "", True), (0, 2, "", True), (0, 3, "", True), (0, 4, "", True)]
    return {
        "name": "er",
        "ascii": ascii_art,
        "svg": _svg_doc(boxes, arrows, width=900, height=330),
        "description": "users + expenses + servants + milk_deliveries + newspaper_deliveries",
    }


# ---------------------------------------------------------------------------
# AI workflow diagram
# ---------------------------------------------------------------------------
def ai_workflow() -> dict[str, str]:
    ascii_art = """  +--------+      +--------+      +---------+      +----------+      +-----------+
  |  User  | ---> |  Chat  | ---> |  Agent  | ---> |  Tools   | ---> | Database |
  +--------+  msg +--------+  ask +---------+  use +----------+  SQL +-----------+
                 |                    |                       |        |
                 |  +-----------------+                       +--------+
                 |  |  Custom tools:                          |
                 |  |  - SQL query                             |
                 |  |  - financial insights                    |
                 |  |  - monthly summary                       |
                 |  |  - diagrams (SVG/ASCII)                  |
                 |  |  - PDF-ready text                        |
                 |  +-----------------+                       |
                 v                                             |
           +----------+                                       |
           | Response | <-------------------------------------+
           +----------+   streaming tokens via SSE
"""
    boxes = [
        ("user", "User", "message", (30, 40)),
        ("chat", "Chat API", "/ai/chat SSE", (240, 40)),
        ("agent", "Agent", "LangChain memory", (450, 40)),
        ("tools", "Tools", "SQL + Python tools", (660, 40)),
        ("db", "Database", "SQLite", (860, 40)),
        ("resp", "Response", "streamed tokens", (240, 200)),
    ]
    arrows = [
        (0, 1, "POST message", True),
        (1, 2, "invoke", True),
        (2, 3, "tool calls", True),
        (3, 4, "SELECT/exec", True),
        (3, 5, "result", True),
        (2, 5, "final answer", True),
    ]
    return {
        "name": "ai-workflow",
        "ascii": ascii_art,
        "svg": _svg_doc(boxes, arrows, width=1080, height=360),
        "description": "user -> chat -> agent -> tools -> database -> response",
    }


GENERATORS: dict[str, Any] = {
    "architecture": architecture,
    "er": er,
    "ai-workflow": ai_workflow,
}
