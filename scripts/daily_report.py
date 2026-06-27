#!/usr/bin/env python3
"""
ClipForge AI — Daily Report Generator & Email Sender
Scans data/ for today's generated packs, creates a summary report,
and emails it via Gmail SMTP.
"""

import json
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 465

PRICING_TIERS = {
    "starter_pack": 2.99,
    "mega_pack": 6.99,
    "bundle_pack": 9.99,
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"ERROR: config.json not found at {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_pack_timestamp(filename: str) -> datetime | None:
    """Extract the datetime from a pack filename like 'boho_florals_pack1_20260627_143000.json'."""
    parts = filename.rsplit("_", 2)
    if len(parts) < 3:
        return None
    ts_part = f"{parts[-2]}_{parts[-1].replace('.json', '')}"
    try:
        return datetime.strptime(ts_part, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def get_today_packs() -> list[dict]:
    """Load all pack JSON files created today (UTC)."""
    if not DATA_DIR.exists():
        return []

    today = datetime.now(timezone.utc).date()
    packs = []

    for filepath in sorted(DATA_DIR.glob("*.json")):
        ts = _parse_pack_timestamp(filepath.name)
        if ts is None:
            continue
        if ts.date() != today:
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "prompts" not in data:
                continue
            packs.append(data)
        except (json.JSONDecodeError, KeyError):
            continue

    return packs


def get_today_stats() -> dict:
    """Compute aggregated stats for today's generated packs."""
    packs = get_today_packs()
    if not packs:
        return {
            "packs_created": 0,
            "categories": [],
            "total_prompts": 0,
            "prices": [],
            "price_min": 0.0,
            "price_max": 0.0,
            "price_avg": 0.0,
            "revenue_potential": 0.0,
            "top_prompts": [],
            "categories_breakdown": {},
            "total_failed": 0,
            "pack_details": [],
        }

    all_prices: list[float] = []
    all_prompts: list[dict] = []
    categories_seen: dict[str, dict] = {}
    total_failed = 0
    pack_details: list[dict] = []

    for pack in packs:
        cat_key = pack.get("category", "unknown")
        cat_name = pack.get("category_name", cat_key)
        count_gen = pack.get("count_generated", len(pack.get("prompts", [])))
        count_failed = pack.get("count_failed", 0)
        total_failed += count_failed

        if cat_key not in categories_seen:
            categories_seen[cat_key] = {
                "name": cat_name,
                "packs": 0,
                "prompts": 0,
            }
        categories_seen[cat_key]["packs"] += 1
        categories_seen[cat_key]["prompts"] += count_gen

        pack_prices = []
        for prompt_data in pack.get("prompts", []):
            price = prompt_data.get("price", 0.0)
            if isinstance(price, str):
                try:
                    price = float(price.replace("$", ""))
                except ValueError:
                    price = 0.0
            all_prices.append(price)
            pack_prices.append(price)
            all_prompts.append({
                "prompt": prompt_data.get("prompt", "")[:120],
                "title": prompt_data.get("title", ""),
                "price": price,
                "category": cat_name,
            })

        pack_details.append({
            "name": pack.get("pack_name", "Unknown Pack"),
            "category": cat_name,
            "count_generated": count_gen,
            "count_failed": count_failed,
            "total_price": sum(pack_prices),
        })

    price_min = min(all_prices) if all_prices else 0.0
    price_max = max(all_prices) if all_prices else 0.0
    price_avg = sum(all_prices) / len(all_prices) if all_prices else 0.0

    top_prompts = sorted(all_prompts, key=lambda x: x["price"], reverse=True)[:5]

    return {
        "packs_created": len(packs),
        "categories": sorted(categories_seen.keys()),
        "total_prompts": len(all_prices),
        "prices": all_prices,
        "price_min": price_min,
        "price_max": price_max,
        "price_avg": price_avg,
        "revenue_potential": sum(all_prices),
        "top_prompts": top_prompts,
        "categories_breakdown": categories_seen,
        "total_failed": total_failed,
        "pack_details": pack_details,
    }


def generate_report() -> str:
    """Build the full daily report text."""
    config = load_config()
    owner = config.get("owner", {})
    stats = get_today_stats()
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%A, %B %d, %Y")
    bot_name = config.get("bot_name", "ClipForge AI")

    lines: list[str] = []

    lines.append("=" * 60)
    lines.append(f"  {bot_name} — Daily Report")
    lines.append(f"  {date_str}")
    lines.append("=" * 60)
    lines.append("")

    if stats["packs_created"] == 0:
        lines.append("  No packs were generated today.")
        lines.append("")
        lines.append("  Next day suggestion: Run the generator to keep the pipeline moving.")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"  Packs Created:        {stats['packs_created']}")
    lines.append(f"  Total Prompts:        {stats['total_prompts']}")
    lines.append(f"  Failed Generations:   {stats['total_failed']}")
    lines.append(f"  Categories Covered:   {len(stats['categories'])}")
    lines.append(f"    {', '.join(stats['categories'])}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("  Pack Details")
    lines.append("-" * 60)
    for pd in stats["pack_details"]:
        status = f"{pd['count_generated']} OK"
        if pd["count_failed"] > 0:
            status += f", {pd['count_failed']} failed"
        lines.append(f"  {pd['name']}")
        lines.append(f"    Category: {pd['category']}  |  {status}  |  Subtotal: ${pd['total_price']:.2f}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("  Pricing Summary")
    lines.append("-" * 60)
    lines.append(f"  Price Range:  ${stats['price_min']:.2f} — ${stats['price_max']:.2f}")
    lines.append(f"  Average:      ${stats['price_avg']:.2f}")
    lines.append(f"  Revenue If All Sell:  ${stats['revenue_potential']:.2f}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("  Top 5 Prompts by Price")
    lines.append("-" * 60)
    for i, p in enumerate(stats["top_prompts"], 1):
        lines.append(f"  {i}. ${p['price']:.2f}  [{p['category']}]")
        lines.append(f"     {p['title']}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("  Categories Breakdown")
    lines.append("-" * 60)
    for cat_key in sorted(stats["categories_breakdown"].keys()):
        info = stats["categories_breakdown"][cat_key]
        lines.append(f"  {info['name']:30s}  {info['packs']} pack(s)  {info['prompts']} prompts")
    lines.append("")

    lines.append("-" * 60)
    lines.append("  Next Day Suggestions")
    lines.append("-" * 60)

    all_categories = config.get("generation", {}).get("categories", [])
    uncategorized = [c for c in all_categories if c not in stats["categories"]]
    if uncategorized:
        lines.append(f"  Categories not yet created today:")
        for c in uncategorized[:5]:
            lines.append(f"    - {c}")
    else:
        lines.append("  All categories have been covered today.")

    pricing_tiers = config.get("generation", {}).get("pricing", {})
    under_priced = [
        p for p in stats["top_prompts"]
        if p["price"] < pricing_tiers.get("mega_pack", 6.99)
    ]
    if under_priced:
        lines.append(f"  {len(under_priced)} top prompt(s) priced below mega-pack tier — consider raising.")

    lines.append("")
    lines.append("=" * 60)
    lines.append(f"  Generated by {bot_name} at {now.strftime('%H:%M UTC')}")
    lines.append(f"  Owner: {owner.get('name', 'N/A')} ({owner.get('email', 'N/A')})")
    lines.append("=" * 60)
    lines.append("")

    return "\n".join(lines)


def save_report(report_text: str) -> Path:
    """Save the report to reports/ directory. Returns the file path."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"daily_report_{date_str}.txt"
    filepath = REPORTS_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"Report saved: {filepath}")
    return filepath


def send_report(report_text: str) -> bool:
    """Email the report via Gmail SMTP. Returns True on success."""
    sender_email = os.environ.get("SENDER_EMAIL")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not sender_email:
        print("ERROR: SENDER_EMAIL environment variable not set.")
        return False
    if not app_password:
        print("ERROR: GMAIL_APP_PASSWORD environment variable not set.")
        return False

    config = load_config()
    owner = config.get("owner", {})
    recipient_email = owner.get("email")
    recipient_name = owner.get("name", "there")

    if not recipient_email:
        print("ERROR: owner.email not found in config.json.")
        return False

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%B %d, %Y")
    bot_name = config.get("bot_name", "ClipForge AI")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{bot_name} — Daily Report for {date_str}"
    msg["From"] = f"{bot_name} <{sender_email}>"
    msg["To"] = f"{recipient_name} <{recipient_email}>"

    plain_part = MIMEText(report_text, "plain", "utf-8")
    msg.attach(plain_part)

    html_body = _report_to_html(report_text, bot_name)
    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(html_part)

    try:
        with smtplib.SMTP_SSL(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, [recipient_email], msg.as_string())
        print(f"Report emailed to {recipient_email}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("ERROR: Gmail authentication failed. Check SENDER_EMAIL and GMAIL_APP_PASSWORD.")
        return False
    except smtplib.SMTPException as e:
        print(f"ERROR: SMTP error — {e}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to send email — {e}")
        return False


def _report_to_html(report_text: str, bot_name: str) -> str:
    """Convert the plain-text report into a simple styled HTML email."""
    escaped = report_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:'Courier New',monospace;">
<div style="max-width:640px;margin:20px auto;background:#ffffff;border:1px solid #e0e0e0;">
  <div style="background:#1a1a2e;color:#00d4aa;padding:16px 20px;font-size:18px;font-weight:bold;">
    {bot_name}
  </div>
  <pre style="padding:20px;font-size:13px;line-height:1.5;white-space:pre-wrap;word-wrap:break-word;color:#333;">{escaped}</pre>
</div>
</body>
</html>"""


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="ClipForge AI — Generate and send daily report"
    )
    parser.add_argument(
        "--send", "-s",
        action="store_true",
        help="Send the report via email (Gmail SMTP)",
    )
    parser.add_argument(
        "--save-only",
        action="store_true",
        help="Save report to reports/ without printing or sending",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report to stdout without saving or sending",
    )
    args = parser.parse_args()

    report = generate_report()

    if args.dry_run:
        print(report)
        return

    if args.save_only:
        save_report(report)
        return

    print(report)
    save_report(report)

    if args.send:
        success = send_report(report)
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
