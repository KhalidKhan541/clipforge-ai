"""
Full Pipeline — Groq → Pollinations → ZIP → Gumroad → Email Report
Runs the entire clip art business on autopilot
"""
import os
import sys
import json
import random
import smtplib
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, str(Path(__file__).parent))

from prompt_library import CATEGORIES, get_prompts_for_category
from generator import generate_pack
from image_generator import ImageGenerator
from gumroad_uploader import GumroadUploader


DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "output"
REPORTS_DIR = Path(__file__).parent / "reports"


def send_email(subject, body):
    """Send email report via Gmail SMTP"""
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = sender

    if not sender or not password:
        print("Email credentials not set, skipping email")
        return False

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print(f"Email sent: {subject}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def generate_daily_report(packs_created, gumroad_results):
    """Generate and send daily report"""
    now = datetime.now()
    report_lines = [
        f"=== ClipForge AI Daily Report ===",
        f"Date: {now.strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"--- Packs Created Today ---",
    ]

    total_revenue_potential = 0
    for pack in packs_created:
        price = pack.get("price", 499) / 100
        total_revenue_potential += price * 100
        report_lines.append(f"  {pack['pack_name']} - ${price:.2f} - {pack['category']}")

    report_lines.extend([
        f"",
        f"--- Gumroad Upload Status ---",
    ])

    for result in gumroad_results:
        status = "SUCCESS" if result.get("product_id") else "FAILED"
        report_lines.append(f"  {result['name']}: {status}")

    report_lines.extend([
        f"",
        f"--- Revenue Projection ---",
        f"Total packs: {len(packs_created)}",
        f"If each sells 100 copies: ${total_revenue_potential:.2f}",
        f"",
        f"--- Next Actions ---",
        f"1. Share Gumroad links on Twitter/Reddit/Pinterest",
        f"2. Post sample images on social media",
        f"3. Check email for tomorrow's report",
    ])

    report = "\n".join(report_lines)

    REPORTS_DIR.mkdir(exist_ok=True)
    report_path = REPORTS_DIR / f"report_{now.strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_path, "w") as f:
        f.write(report)

    print(report)
    send_email(f"ClipForge Report - {now.strftime('%Y-%m-%d')}", report)

    return report


def run_pipeline(count=3):
    """Run the full pipeline"""
    print("=" * 50)
    print("ClipForge AI - Full Pipeline")
    print("=" * 50)

    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    category_keys = list(CATEGORIES.keys())
    selected = random.sample(category_keys, min(count, len(category_keys)))

    packs_created = []
    gumroad_results = []

    uploader = None
    if os.environ.get("GUMROAD_ACCESS_TOKEN"):
        try:
            uploader = GumroadUploader()
            print("Gumroad connected")
        except Exception as e:
            print(f"Gumroad error: {e}")

    for cat_key in selected:
        cat = CATEGORIES[cat_key]
        print(f"\n--- {cat['name']} ---")

        print("1. Generating prompts with Groq...")
        pack_data = generate_pack(category=cat_key, count=1)
        if not pack_data:
            print(f"  Failed to generate prompts for {cat['name']}")
            continue

        pack = pack_data[0]
        pack_name = pack.get("pack_name", f"{cat_key}_pack")

        print("2. Generating images with Pollinations.ai...")
        generator = ImageGenerator(str(OUTPUT_DIR))
        prompts = pack.get("prompts", [])

        if prompts:
            results = generator.generate_pack(
                [p.get("prompt", "") for p in prompts[:50]],
                pack_name,
                cat_key
            )
            print(f"  Generated {len(results)} images")

            print("3. Creating ZIP file...")
            zip_path = generator.create_zip(
                str(OUTPUT_DIR / pack_name),
                pack_name
            )
            print(f"  ZIP: {zip_path}")

            if uploader:
                print("4. Uploading to Gumroad...")
                try:
                    product = uploader.upload_clip_art_pack(pack, zip_path)
                    gumroad_results.append({
                        "name": pack_name,
                        "product_id": product.get("id"),
                        "url": product.get("url")
                    })
                except Exception as e:
                    print(f"  Upload error: {e}")
                    gumroad_results.append({
                        "name": pack_name,
                        "product_id": None,
                        "error": str(e)
                    })

        packs_created.append(pack)

        pack_file = DATA_DIR / f"{pack_name}.json"
        with open(pack_file, "w") as f:
            json.dump(pack, f, indent=2)

    print("\n" + "=" * 50)
    print("Generating daily report...")
    generate_daily_report(packs_created, gumroad_results)

    print("\nPipeline complete!")
    return packs_created, gumroad_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ClipForge AI Pipeline")
    parser.add_argument("--count", type=int, default=3, help="Number of packs")
    args = parser.parse_args()

    run_pipeline(count=args.count)
