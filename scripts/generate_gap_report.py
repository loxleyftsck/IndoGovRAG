#!/usr/bin/env python3
"""
Weekly Gap Report Generator for IndoGovRAG.

Scans the current week's search logs to build a list of queries
that returned 0 results, then saves a formatted report to the
reports/ directory.

Usage:
    python scripts/generate_gap_report.py [--weeks 1]

Email integration is stubbed — swap send_gap_report() with your
SMTP / SendGrid / Postmark integration when ready.
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

#  Paths 
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "logs"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

#  Helpers 

def get_week_log_paths(weeks_ago: int = 0) -> list[Path]:
    """Return JSONL log paths for the given number of weeks ago (0 = current)."""
    base = datetime.utcnow() - timedelta(weeks=weeks_ago)
    year, week = base.isocalendar()
    log_file = DATA_DIR / f"searches_{year}_W{week:02d}.jsonl"
    return [log_file] if log_file.exists() else []


def load_events(log_paths: list[Path]) -> list[dict]:
    """Parse all JSONL lines from the given paths."""
    events = []
    for path in log_paths:
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return events


def build_gap_report(events: list[dict], top_n: int = 50) -> dict:
    """
    Aggregate events into a structured gap report.
    Returns a dict ready to be serialised.
    """
    zero_events = [e for e in events if e.get("results_count", 0) == 0]

    # Count occurrences
    counter = Counter(e["query"] for e in zero_events)

    # Unique queries ranked by frequency
    ranked = counter.most_common(top_n)

    # Find last-seen timestamp per query
    last_seen = {}
    for e in zero_events:
        q = e["query"]
        ts = e.get("timestamp", "")
        if q not in last_seen or ts > last_seen[q]:
            last_seen[q] = ts

    gap_entries = []
    for rank, (query, count) in enumerate(ranked, 1):
        gap_entries.append({
            "rank": rank,
            "query": query,
            "occurrences": count,
            "last_seen": last_seen.get(query, "unknown"),
            "suggested_action": _suggest_action(query),
        })

    # Summary stats
    all_response_times = [e.get("response_time_ms", 0) for e in events if e.get("response_time_ms")]
    all_confidences  = [e.get("confidence_score", 0) for e in events if e.get("confidence_score")]

    total_queries    = len(events)
    zero_result_pct   = (len(zero_events) / total_queries * 100) if total_queries else 0

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": {
            "weeks_ago": 0,
            "log_files": [str(p) for p in get_week_log_paths(0)],
        },
        "summary": {
            "total_queries":   total_queries,
            "zero_result_queries": len(zero_events),
            "zero_result_percentage": round(zero_result_pct, 2),
            "unique_gap_queries": len(counter),
            "avg_confidence":  round(sum(all_confidences) / len(all_confidences), 4) if all_confidences else 0,
            "avg_response_ms": round(sum(all_response_times) / len(all_response_times), 2) if all_response_times else 0,
        },
        "top_gaps": gap_entries,
    }
    return report


def _suggest_action(query: str) -> str:
    """
    Simple heuristic to suggest a remediation for a zero-result query.
    Swap with a classifier / LLM call in production.
    """
    q = query.lower()
    if any(k in q for k in ["syarat", "persyaratan", "dokumen", "cara", "bagaimana"]):
        return "Add relevant policy documents covering this topic"
    if any(k in q for k in ["umur", "usia", "berkas", "biaya", "harga", "tarif"]):
        return "Add specific regulation documents with numerical thresholds"
    if any(k in q for k in ["kapan", "tanggal", "deadline", "batas"]):
        return "Add procedural timelines from official handbooks"
    return "Review knowledge base — no documents match this query"


def save_report(report: dict, output_path: Path) -> None:
    """Write the report as both JSON and a plain-text summary."""
    # JSON
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # Plain-text summary
    lines = [
        "=" * 60,
        "  IndoGovRAG — Weekly Gap Report",
        f"  Generated: {report['generated_at']}",
        "=" * 60,
        "",
        f"Total queries analysed : {report['summary']['total_queries']}",
        f"Zero-result queries    : {report['summary']['zero_result_queries']} "
        f"({report['summary']['zero_result_percentage']}%)",
        f"Unique gap queries     : {report['summary']['unique_gap_queries']}",
        f"Avg confidence score   : {report['summary']['avg_confidence']:.4f}",
        f"Avg response time     : {report['summary']['avg_response_ms']:.2f} ms",
        "",
        "-" * 60,
        "  TOP 50 GAP QUERIES",
        "-" * 60,
    ]
    for entry in report["top_gaps"]:
        lines.append(
            f"  #{entry['rank']:3} | {entry['occurrences']:3}× | {entry['query']}"
        )
        lines.append(f"         action: {entry['suggested_action']}")
        lines.append(f"         last seen: {entry['last_seen']}")
        lines.append("")

    txt_path = output_path.with_suffix(".txt")
    txt_path.write_text("\n".join(lines), encoding="utf-8")


#  Email stub 

def send_gap_report(report_path: Path) -> None:
    """
    Email the gap report to configured recipients.
    Replace this stub with your SMTP/SendGrid/Postmark integration.
    """
    import os

    recipients = os.getenv("GAP_REPORT_EMAIL", "").split(",")
    if not recipients or not recipients[0]:
        print("[WARN] GAP_REPORT_EMAIL not set — skipping email delivery.")
        print(f"[OK]  Report saved to: {report_path}")
        return

    #  PLACEHOLDER: integrate your email provider here 
    #
    # Example (SMTP):
    #
    #   import smtplib, ssl
    #   from email.mime.text import MIMEText
    #   from email.mime.multipart import MIMEMultipart
    #
    #   msg = MIMEMultipart()
    #   msg["Subject"] = "[IndoGovRAG] Weekly Gap Report"
    #   msg["From"]    = os.getenv("SMTP_FROM", "noreply@indogov.ai")
    #   msg["To"]      = ", ".join(r.strip() for r in recipients if r.strip())
    #
    #   body = f"See attached report: {report_path.name}"
    #   msg.attach(MIMEText(body, "plain"))
    #
    #   with open(report_path) as f:
    #       msg.attach(MIMEText(f.read(), "json"))
    #
    #   ctx = ssl.create_default_context()
    #   with smtplib.SMTP(os.getenv("SMTP_HOST", ""), int(os.getenv("SMTP_PORT", 587))) as server:
    #       server.starttls(context=ctx)
    #       server.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASS", ""))
    #       server.send_message(msg)
    #
    # 

    print(f"[STUB] Would email {report_path} to: {recipients}")
    print(f"[OK]  Report saved to: {report_path}")


#  CLI 

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate weekly gap report")
    parser.add_argument(
        "--weeks", type=int, default=0,
        help="Weeks ago to analyse (0 = current week, 1 = last week, ...)"
    )
    parser.add_argument(
        "--top", type=int, default=50,
        help="Number of gap queries to include (default 50)"
    )
    args = parser.parse_args()

    log_paths = get_week_log_paths(args.weeks)
    if not log_paths:
        year, week = datetime.utcnow().isocalendar()
        print(f"[WARN] No log file found for year={year}, week={week:02d}")
        print(f"[INFO] Log path expected at: {DATA_DIR / f'searches_{year}_W{week:02d}.jsonl'}")
        print("[INFO] Search logs are created automatically when queries hit /query.")
        return

    events = load_events(log_paths)
    if not events:
        print("[INFO] Log file exists but contains no events yet.")
        return

    report = build_gap_report(events, top_n=args.top)

    timestamp = datetime.utcnow().strftime("%Y%m%d")
    output_path = REPORTS_DIR / f"gap_report_{timestamp}.json"
    save_report(report, output_path)

    print(f"[OK] Report generated: {output_path}")
    print(f"[OK] Text summary   : {output_path.with_suffix('.txt')}")

    send_gap_report(output_path)


if __name__ == "__main__":
    main()