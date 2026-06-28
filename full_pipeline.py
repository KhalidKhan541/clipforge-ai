"""
Full Pipeline — Groq → Pollinations → PDF → Gumroad → Email Report
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
from email.mime.base import MIMEBase
from email import encoders

sys.path.insert(0, str(Path(__file__).parent))

from prompt_library import CATEGORIES, get_prompts_for_category
from generator import generate_category_pack, get_groq_client, load_config
from image_generator import ImageGenerator
from gumroad_uploader import GumroadUploader


DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "output"
REPORTS_DIR = Path(__file__).parent / "reports"

IMAGES_PER_PACK = 50
DEFAULT_PRICE_CENTS = 400


def send_email(subject, body, attachment_path=None):
    """Send email report via Gmail SMTP with optional PDF attachment"""
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

    if attachment_path and Path(attachment_path).exists():
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "pdf")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={Path(attachment_path).name}"
            )
            msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print(f"Email sent: {subject}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def generate_daily_report(packs_created, gumroad_results, pdf_files):
    """Generate and send daily report with PDF attachments"""
    now = datetime.now()
    report_lines = [
        f"=== ClipForge AI Daily Report ===",
        f"Date: {now.strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"--- Packs Created Today ---",
    ]

    total_revenue_potential = 0
    for pack in packs_created:
        price = pack.get("price", DEFAULT_PRICE_CENTS) / 100
        total_revenue_potential += price * 100
        report_lines.append(f"  {pack['pack_name']} - ${price:.2f} - {pack['category']}")

    report_lines.extend([
        f"",
        f"--- Gumroad Upload Status ---",
    ])

    for result in gumroad_results:
        status = "SUCCESS" if result.get("product_id") else "FAILED"
        url = result.get("url", "N/A")
        report_lines.append(f"  {result['name']}: {status} - {url}")

    report_lines.extend([
        f"",
        f"--- PDF Files Generated ---",
    ])

    for pdf in pdf_files:
        report_lines.append(f"  {pdf}")

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

    for i, pdf_file in enumerate(pdf_files):
        if Path(pdf_file).exists():
            gumroad_url = gumroad_results[i].get("url", "N/A") if i < len(gumroad_results) else "N/A"
            email_body = f"{report}\n\nGumroad Product URL: {gumroad_url}"
            send_email(
                f"ClipForge Report - {now.strftime('%Y-%m-%d')}",
                email_body,
                attachment_path=pdf_file
            )

    if not pdf_files:
        send_email(f"ClipForge Report - {now.strftime('%Y-%m-%d')}", report)

    return report


def run_pipeline(count=3):
    """Run the full pipeline"""
    print("=" * 50)
    print("ClipForge AI - Full Pipeline")
    print("=" * 50)

    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    config = load_config()
    client = get_groq_client()

    category_keys = list(CATEGORIES.keys())
    selected = random.sample(category_keys, min(count, len(category_keys)))

    packs_created = []
    gumroad_results = []
    pdf_files = []

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
        pack = generate_category_pack(client, config, cat_key, 1, IMAGES_PER_PACK)
        if not pack:
            print(f"  Failed to generate prompts for {cat['name']}")
            continue

        pack["price"] = DEFAULT_PRICE_CENTS
        pack_name = pack.get("pack_name", f"{cat_key}_pack")

        print("2. Generating images with Pollinations.ai...")
        generator = ImageGenerator(str(OUTPUT_DIR))
        prompts = pack.get("prompts", [])

        if prompts:
            results = generator.generate_pack(
                [p.get("prompt", "") for p in prompts[:IMAGES_PER_PACK]],
                pack_name,
                cat_key
            )
            print(f"  Generated {len(results)} images")

            print("3. Creating PDF file...")
            pdf_path = generator.create_pdf(
                str(OUTPUT_DIR / pack_name),
                pack_name,
                cat_key,
                pack
            )
            print(f"  PDF: {pdf_path}")
            pdf_files.append(str(pdf_path))

            if uploader:
                print("4. Uploading to Gumroad and publishing...")
                try:
                    product = uploader.upload_clip_art_pack(pack, pdf_path)
                    gumroad_url = product.get("url", "")
                    gumroad_results.append({
                        "name": pack_name,
                        "product_id": product.get("id"),
                        "url": gumroad_url
                    })
                    print(f"  Published: {gumroad_url}")
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
    generate_daily_report(packs_created, gumroad_results, pdf_files)

    print("\nPipeline complete!")
    return packs_created, gumroad_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ClipForge AI Pipeline")
    parser.add_argument("--count", type=int, default=3, help="Number of packs")
    args = parser.parse_args()

    run_pipeline(count=args.count)
