"""
Create a simple HTML timeline view for output/simulation_log.csv.

Run:
    python code/visualize_log.py
"""

from __future__ import annotations

import argparse
import csv
import html
from collections import defaultdict
from pathlib import Path

from config import settings


DEFAULT_INPUT = Path(settings.OUTPUT_CSV)
DEFAULT_OUTPUT = settings.OUTPUT_DIR / "simulation_timeline.html"

BEHAVIOR_STYLES = {
    "IDLE": ("idle", "IDL"),
    "OPEN_CLIENT": ("open", "OPN"),
    "OPEN_MESSENGER": ("open", "MSG"),
    "VIEW_INBOX": ("view", "INB"),
    "VIEW_CHATS": ("view", "CHTS"),
    "READ_EMAIL": ("read", "READ"),
    "READ_MESSAGE": ("read", "R-MSG"),
    "COMPOSE": ("compose", "CMP"),
    "SEND_MESSAGE": ("compose", "SEND"),
    "SEARCH": ("search", "SRCH"),
    "SEARCH_MESSAGES": ("search", "M-SR"),
    "DELETE": ("delete", "DEL"),
    "DELETE_MESSAGE": ("delete", "M-DEL"),
    "REPLY": ("reply", "RPLY"),
    "REPLY_MESSAGE": ("reply", "M-RP"),
    "FORWARD": ("forward", "FWD"),
    "CLICK_LINK": ("suspicious", "CLICK"),
    "FWD_EXTERNAL": ("suspicious", "X-FWD"),
    "LEAK_ATTACH": ("suspicious", "LEAK"),
    "SEARCH_SENSITIVE": ("suspicious", "SENS"),
}

BEHAVIOR_PRIORITY = {
    "CLICK_LINK": 100,
    "FWD_EXTERNAL": 100,
    "LEAK_ATTACH": 100,
    "SEARCH_SENSITIVE": 100,
    "COMPOSE": 60,
    "SEND_MESSAGE": 60,
    "REPLY": 55,
    "REPLY_MESSAGE": 55,
    "FORWARD": 50,
    "READ_EMAIL": 45,
    "READ_MESSAGE": 45,
    "SEARCH": 40,
    "SEARCH_MESSAGES": 40,
    "DELETE": 35,
    "DELETE_MESSAGE": 35,
    "VIEW_INBOX": 30,
    "VIEW_CHATS": 30,
    "OPEN_CLIENT": 20,
    "OPEN_MESSENGER": 20,
    "IDLE": 0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to simulation CSV. Default: {DEFAULT_INPUT}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path to HTML output. Default: {DEFAULT_OUTPUT}",
    )
    return parser.parse_args()


def load_rows(csv_path: Path) -> list[dict]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        if "channel" not in row:
            email_id = row.get("email_id", "")
            email_category = row.get("email_category", "")
            row["channel"] = "email" if email_id or email_category else ""
            row["artifact_kind"] = "email" if email_id or email_category else ""
            row["artifact_id"] = email_id
            row["artifact_category"] = email_category
        else:
            row.setdefault("artifact_kind", "")
            row.setdefault("artifact_id", "")
            row.setdefault("artifact_category", "")
        row.setdefault("sender", row.get("sender", ""))
        row.setdefault("recipient", row.get("recipient", ""))

        row["tick"] = int(row["tick"])
        row["day"] = int(row["day"])
        row["hour"] = int(row["hour"])
        row["minute"] = int(row["minute"])
        row["second"] = int(row["second"])
        row["duration_seconds"] = int(row["duration_seconds"])
        row["risk_score"] = float(row["risk_score"])
        row["flagged"] = row["flagged"] == "True"
        row["is_suspicious"] = row["is_suspicious"] == "True"

    return rows


def summarize_slots(rows: list[dict]):
    slots = sorted({(row["day"], row["hour"]) for row in rows})
    by_agent = defaultdict(list)
    slot_events = defaultdict(lambda: defaultdict(list))

    for row in rows:
        by_agent[row["agent_id"]].append(row)
        slot_events[row["agent_id"]][(row["day"], row["hour"])].append(row)

    agent_cards = []
    for agent_id in sorted(by_agent):
        agent_rows = sorted(by_agent[agent_id], key=lambda row: row["tick"])
        flagged_count = sum(1 for row in agent_rows if row["flagged"])
        agent_cards.append(
            {
                "agent_id": agent_id,
                "profile": agent_rows[0]["profile"],
                "max_risk": max(row["risk_score"] for row in agent_rows),
                "flagged_count": flagged_count,
                "final_suspicious": agent_rows[-1]["is_suspicious"],
                "rows": agent_rows,
                "slots": slot_events[agent_id],
            }
        )

    return slots, agent_cards


def slot_label(slot: tuple[int, int]) -> str:
    day, hour = slot
    return f"D{day} {hour:02d}:00"


def format_time(row: dict) -> str:
    return f"D{row['day']} {row['hour']:02d}:{row['minute']:02d}:{row['second']:02d}"


def dominant_behavior(rows: list[dict]) -> tuple[str, str]:
    best = max(
        rows,
        key=lambda row: (
            BEHAVIOR_PRIORITY.get(row["behavior"], 10),
            row["duration_seconds"],
            row["tick"],
        ),
    )
    behavior = best["behavior"]
    css_class, label = BEHAVIOR_STYLES.get(behavior, ("other", behavior[:4].upper()))
    return css_class, label


def build_slot_title(rows: list[dict]) -> str:
    lines = []
    for row in sorted(rows, key=lambda item: (item["minute"], item["second"], item["tick"])):
        extra = []
        if row["channel"]:
            extra.append(row["channel"])
        if row["artifact_category"]:
            extra.append(row["artifact_category"])
        if row["artifact_id"]:
            kind = row["artifact_kind"] or "item"
            extra.append(f"{kind} {row['artifact_id']}")
        if row["sender"] or row["recipient"]:
            extra.append(f"{row['sender'] or '?'} -> {row['recipient'] or '?'}")
        if row["flagged"]:
            extra.append("FLAGGED")
        suffix = f" ({', '.join(extra)})" if extra else ""
        lines.append(
            f"{row['hour']:02d}:{row['minute']:02d}:{row['second']:02d} - "
            f"{row['behavior']} [{row['duration_seconds']}s]{suffix}"
        )
    return "&#10;".join(html.escape(line) for line in lines)


def build_slot_details(agent_id: str, slot: tuple[int, int], rows: list[dict]) -> str:
    detail_rows = []
    for row in sorted(rows, key=lambda item: (item["minute"], item["second"], item["tick"])):
        detail_rows.append(
            "<tr>"
            f"<td>{html.escape(format_time(row))}</td>"
            f"<td>{html.escape(row['behavior'])}</td>"
            f"<td>{row['duration_seconds']}</td>"
            f"<td>{html.escape(row['channel'] or '-')}</td>"
            f"<td>{html.escape(row['artifact_category'] or '-')}</td>"
            f"<td>{html.escape(row['artifact_id'] or '-')}</td>"
            f"<td>{html.escape(row['sender'] or '-')}</td>"
            f"<td>{html.escape(row['recipient'] or '-')}</td>"
            f"<td>{'yes' if row['flagged'] else 'no'}</td>"
            "</tr>"
        )

    return (
        f"<h3>{html.escape(agent_id)} - {html.escape(slot_label(slot))}</h3>"
        f"<p>{len(rows)} event(s) in this slot.</p>"
        "<table class='slot-detail-table'>"
        "<thead><tr><th>Time</th><th>Behavior</th><th>Duration(s)</th>"
        "<th>Channel</th><th>Type</th><th>ID</th><th>Sender</th><th>Recipient</th><th>Flagged</th></tr></thead>"
        f"<tbody>{''.join(detail_rows)}</tbody>"
        "</table>"
    )


def render_html(csv_path: Path, slots: list[tuple[int, int]], agent_cards: list[dict]) -> str:
    total_events = sum(len(agent["rows"]) for agent in agent_cards)
    total_flagged = sum(agent["flagged_count"] for agent in agent_cards)

    header_cells = "".join(
        f"<th class='time-col'>{html.escape(slot_label(slot))}</th>" for slot in slots
    )

    table_rows = []
    for agent in agent_cards:
        timeline_cells = []
        for slot in slots:
            rows = agent["slots"].get(slot, [])
            if not rows:
                timeline_cells.append("<td class='empty'></td>")
                continue

            css_class, label = dominant_behavior(rows)
            title = build_slot_title(rows)
            details = html.escape(build_slot_details(agent["agent_id"], slot, rows), quote=True)
            timeline_cells.append(
                "<td class='slot {css}' title='{title}' data-slot-details=\"{details}\" tabindex='0'>"
                "<span>{label}</span>"
                "<small>{count}</small>"
                "</td>".format(
                    css=css_class,
                    title=title,
                    details=details,
                    label=html.escape(label),
                    count=len(rows),
                )
            )

        suspicious_label = "yes" if agent["final_suspicious"] else "no"
        table_rows.append(
            "<tr data-agent='{agent}'>"
            "<th class='agent-col'>{agent}</th>"
            "<td>{profile}</td>"
            "<td>{risk:.1f}</td>"
            "<td>{flagged}</td>"
            "<td>{suspicious}</td>"
            "{cells}"
            "</tr>".format(
                agent=html.escape(agent["agent_id"]),
                profile=html.escape(agent["profile"]),
                risk=agent["max_risk"],
                flagged=agent["flagged_count"],
                suspicious=suspicious_label,
                cells="".join(timeline_cells),
            )
        )

    detail_sections = []
    for agent in agent_cards:
        event_rows = []
        for row in agent["rows"]:
            event_rows.append(
                "<tr>"
                f"<td>{html.escape(format_time(row))}</td>"
                f"<td>{html.escape(row['behavior'])}</td>"
                f"<td>{row['duration_seconds']}</td>"
                f"<td>{html.escape(row['channel'] or '-')}</td>"
                f"<td>{html.escape(row['artifact_category'] or '-')}</td>"
                f"<td>{html.escape(row['artifact_id'] or '-')}</td>"
                f"<td>{html.escape(row['sender'] or '-')}</td>"
                f"<td>{html.escape(row['recipient'] or '-')}</td>"
                f"<td>{row['risk_score']:.1f}</td>"
                f"<td>{'yes' if row['flagged'] else 'no'}</td>"
                "</tr>"
            )

        detail_sections.append(
            "<details>"
            f"<summary>{html.escape(agent['agent_id'])} ({html.escape(agent['profile'])})</summary>"
            "<table class='detail-table'>"
            "<thead><tr><th>Time</th><th>Behavior</th><th>Duration(s)</th>"
            "<th>Channel</th><th>Type</th><th>ID</th><th>Sender</th><th>Recipient</th><th>Risk</th><th>Flagged</th></tr></thead>"
            f"<tbody>{''.join(event_rows)}</tbody>"
            "</table>"
            "</details>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Simulation Timeline</title>
  <style>
    :root {{
      --bg: #f6f4ef;
      --panel: #fffdf8;
      --grid: #d8d1c4;
      --text: #1f2933;
      --muted: #6b7280;
      --idle: #e5e7eb;
      --open: #dbeafe;
      --view: #c7d2fe;
      --read: #bfdbfe;
      --compose: #bbf7d0;
      --search: #fde68a;
      --delete: #fecdd3;
      --reply: #a7f3d0;
      --forward: #99f6e4;
      --suspicious: #fca5a5;
      --other: #ddd6fe;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 24px;
      font-family: "Segoe UI", Tahoma, sans-serif;
      background: linear-gradient(180deg, #faf7ef 0%, #f2efe6 100%);
      color: var(--text);
    }}
    h1, h2 {{ margin: 0 0 12px; }}
    p {{ margin: 0 0 12px; color: var(--muted); }}
    .card {{
      background: var(--panel);
      border: 1px solid rgba(31, 41, 51, 0.08);
      border-radius: 14px;
      padding: 18px;
      box-shadow: 0 10px 24px rgba(31, 41, 51, 0.06);
      margin-bottom: 18px;
    }}
    .stats {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 10px;
    }}
    .stat {{
      padding: 10px 12px;
      border-radius: 10px;
      background: #f7f2e8;
      min-width: 140px;
    }}
    .stat strong {{
      display: block;
      font-size: 1.1rem;
      margin-bottom: 4px;
    }}
    .legend {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 12px;
    }}
    .legend span {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.92rem;
    }}
    .swatch {{
      width: 12px;
      height: 12px;
      border-radius: 3px;
      border: 1px solid rgba(31, 41, 51, 0.1);
    }}
    input {{
      width: min(320px, 100%);
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid var(--grid);
      margin-top: 8px;
    }}
    .timeline-wrap {{
      overflow-x: auto;
      border: 1px solid var(--grid);
      border-radius: 12px;
      background: white;
    }}
    .timeline {{
      border-collapse: collapse;
      min-width: 1100px;
      width: max-content;
    }}
    .timeline th,
    .timeline td {{
      border: 1px solid var(--grid);
      padding: 8px;
      text-align: center;
      vertical-align: middle;
      font-size: 0.85rem;
    }}
    .timeline thead th {{
      position: sticky;
      top: 0;
      background: #f8f6ef;
      z-index: 2;
    }}
    .timeline .agent-col {{
      position: sticky;
      left: 0;
      background: #fffdf8;
      z-index: 1;
      min-width: 140px;
      text-align: left;
    }}
    .timeline .time-col {{
      min-width: 68px;
    }}
    .slot {{
      min-width: 68px;
      font-weight: 700;
      cursor: pointer;
    }}
    .slot span {{
      display: block;
    }}
    .slot small {{
      display: block;
      margin-top: 2px;
      font-size: 0.72rem;
      opacity: 0.75;
    }}
    .empty {{ background: #fbfbf9; }}
    .idle {{ background: var(--idle); }}
    .open {{ background: var(--open); }}
    .view {{ background: var(--view); }}
    .read {{ background: var(--read); }}
    .compose {{ background: var(--compose); }}
    .search {{ background: var(--search); }}
    .delete {{ background: var(--delete); }}
    .reply {{ background: var(--reply); }}
    .forward {{ background: var(--forward); }}
    .suspicious {{ background: var(--suspicious); }}
    .other {{ background: var(--other); }}
    details {{
      margin-bottom: 12px;
      border: 1px solid var(--grid);
      border-radius: 10px;
      padding: 10px 12px;
      background: white;
    }}
    summary {{
      cursor: pointer;
      font-weight: 700;
    }}
    .detail-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: 0.9rem;
    }}
    .detail-table th,
    .detail-table td {{
      border: 1px solid var(--grid);
      padding: 8px;
      text-align: left;
    }}
    .detail-table thead th {{
      background: #f8f6ef;
    }}
    .slot-detail-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: 0.9rem;
    }}
    .slot-detail-table th,
    .slot-detail-table td {{
      border: 1px solid var(--grid);
      padding: 8px;
      text-align: left;
    }}
    .slot-detail-table thead th {{
      background: #f8f6ef;
    }}
    .slot:focus {{
      outline: 3px solid rgba(59, 130, 246, 0.45);
      outline-offset: -3px;
    }}
    .modal {{
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: rgba(15, 23, 42, 0.45);
      z-index: 20;
    }}
    .modal.open {{
      display: flex;
    }}
    .modal-card {{
      width: min(960px, 100%);
      max-height: min(85vh, 900px);
      overflow: auto;
      background: var(--panel);
      border-radius: 14px;
      box-shadow: 0 20px 50px rgba(15, 23, 42, 0.25);
      padding: 18px;
    }}
    .modal-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }}
    .modal-close {{
      border: 1px solid var(--grid);
      background: white;
      border-radius: 10px;
      padding: 8px 12px;
      cursor: pointer;
    }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Simulation Timeline</h1>
    <p>Source: {html.escape(str(csv_path))}</p>
    <p>Each colored cell summarizes one agent's activity in one hour. Hover a cell to see the exact actions logged in that slot.</p>
    <div class="stats">
      <div class="stat"><strong>{len(agent_cards)}</strong>Agents</div>
      <div class="stat"><strong>{len(slots)}</strong>Hourly Slots</div>
      <div class="stat"><strong>{total_events:,}</strong>Events</div>
      <div class="stat"><strong>{total_flagged:,}</strong>Flagged Events</div>
    </div>
    <div class="legend">
      <span><i class="swatch" style="background: var(--idle)"></i> Idle</span>
      <span><i class="swatch" style="background: var(--read)"></i> Reading / inbox</span>
      <span><i class="swatch" style="background: var(--compose)"></i> Writing / replying</span>
      <span><i class="swatch" style="background: var(--search)"></i> Searching</span>
      <span><i class="swatch" style="background: var(--delete)"></i> Delete</span>
      <span><i class="swatch" style="background: var(--suspicious)"></i> Suspicious</span>
    </div>
    <label>
      <input id="agentFilter" type="text" placeholder="Filter agents by name...">
    </label>
  </div>

  <div class="card">
    <h2>Hourly Timeline</h2>
    <div class="timeline-wrap">
      <table class="timeline" id="timelineTable">
        <thead>
          <tr>
            <th class="agent-col">Agent</th>
            <th>Profile</th>
            <th>Max Risk</th>
            <th>Flagged</th>
            <th>Suspicious?</th>
            {header_cells}
          </tr>
        </thead>
        <tbody>
          {''.join(table_rows)}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Per-Agent Event Log</h2>
    <p>Open an agent below for the exact sequence of actions with timestamps.</p>
    {''.join(detail_sections)}
  </div>

  <div class="modal" id="slotModal" aria-hidden="true">
    <div class="modal-card">
      <div class="modal-head">
        <h2>Hourly Slot Details</h2>
        <button class="modal-close" id="slotModalClose" type="button">Close</button>
      </div>
      <div id="slotModalBody"></div>
    </div>
  </div>

  <script>
    const filterInput = document.getElementById("agentFilter");
    const timelineRows = Array.from(document.querySelectorAll("#timelineTable tbody tr"));
    const detailBlocks = Array.from(document.querySelectorAll("details"));
    const slotCells = Array.from(document.querySelectorAll(".slot[data-slot-details]"));
    const slotModal = document.getElementById("slotModal");
    const slotModalBody = document.getElementById("slotModalBody");
    const slotModalClose = document.getElementById("slotModalClose");

    const openSlotModal = (cell) => {{
      slotModalBody.innerHTML = cell.dataset.slotDetails;
      slotModal.classList.add("open");
      slotModal.setAttribute("aria-hidden", "false");
    }};

    const closeSlotModal = () => {{
      slotModal.classList.remove("open");
      slotModal.setAttribute("aria-hidden", "true");
      slotModalBody.innerHTML = "";
    }};

    filterInput.addEventListener("input", () => {{
      const query = filterInput.value.trim().toLowerCase();

      timelineRows.forEach((row) => {{
        const name = row.dataset.agent.toLowerCase();
        row.style.display = !query || name.includes(query) ? "" : "none";
      }});

      detailBlocks.forEach((block) => {{
        const name = block.querySelector("summary").textContent.toLowerCase();
        block.style.display = !query || name.includes(query) ? "" : "none";
      }});
    }});

    slotCells.forEach((cell) => {{
      cell.addEventListener("click", () => openSlotModal(cell));
      cell.addEventListener("keydown", (event) => {{
        if (event.key === "Enter" || event.key === " ") {{
          event.preventDefault();
          openSlotModal(cell);
        }}
      }});
    }});

    slotModalClose.addEventListener("click", closeSlotModal);
    slotModal.addEventListener("click", (event) => {{
      if (event.target === slotModal) {{
        closeSlotModal();
      }}
    }});
    document.addEventListener("keydown", (event) => {{
      if (event.key === "Escape" && slotModal.classList.contains("open")) {{
        closeSlotModal();
      }}
    }});
  </script>
</body>
</html>"""


def main() -> None:
    args = parse_args()
    csv_path = args.input.resolve()
    output_path = args.output.resolve()

    if not csv_path.exists():
        raise FileNotFoundError(f"Simulation log not found: {csv_path}")

    rows = load_rows(csv_path)
    slots, agent_cards = summarize_slots(rows)
    html_doc = render_html(csv_path, slots, agent_cards)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_doc, encoding="utf-8")
    print(f"HTML timeline written to: {output_path}")


if __name__ == "__main__":
    main()
