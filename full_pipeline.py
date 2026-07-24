"""
Full Pipeline — Groq → AI Horde → ZIP → Email Report
"""
import os
import sys
import json
import random
import smtplib
import time
import functools
import io
import zipfile
import requests
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from PIL import Image


GMAIL_MAX_MB = 25

NICHES = [
    "AI and human collaboration in workplace",
    "Sustainable living and eco-friendly lifestyle",
    "Mental wellness and mindfulness"
]

USED_PROMPTS_PATH = Path(__file__).parent / "data" / "used_prompts.json"


def _load_used_prompts() -> list[str]:
    """Load list of previously used prompts to avoid duplicates."""
    if USED_PROMPTS_PATH.exists():
        with open(USED_PROMPTS_PATH, "r") as f:
            return json.load(f)
    return []


def _save_used_prompts(prompts: list[str]) -> None:
    """Save used prompts to file."""
    USED_PROMPTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(USED_PROMPTS_PATH, "w") as f:
        json.dump(prompts, f, indent=2)


def _generate_prompts_with_groq(niche: str, count: int, used_prompts: list[str]) -> list[dict]:
    """Generate unique prompts using Groq API."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("ERROR: GROQ_API_KEY not set")
        return []
    
    used_text = "\n".join(f"- {p}" for p in used_prompts[-50:]) if used_prompts else "None yet"
    
    system_prompt = f"""You are a clip art prompt generator. Generate {count} unique, detailed prompts for AI clip art generation.

NICHE: {niche}

REQUIREMENTS:
- Each prompt must describe a single clip art illustration
- Include style details: flat design, minimal, colorful, clean lines
- NO duplicates with previously used prompts
- Images must be commercial-ready (businesses would buy these)
- Include diverse subjects and compositions

PREVIOUSLY USED PROMPTS (DO NOT DUPLICATE):
{used_text}

OUTPUT FORMAT (JSON array):
[
  {{"title": "Short title", "prompt": "Detailed prompt", "niche": "{niche}"}},
  ...
]

Generate exactly {count} prompts. Output ONLY valid JSON, no other text."""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate {count} unique clip art prompts for: {niche}"}
                ],
                "temperature": 0.9,
                "max_tokens": 4000
            },
            timeout=60
        )
        response.raise_for_status()
        
        content = response.json()["choices"][0]["message"]["content"]
        
        import re
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            prompts = json.loads(json_match.group())
            print(f"Generated {len(prompts)} prompts for niche: {niche}")
            return prompts
        else:
            print("ERROR: No JSON array found in Groq response")
            return []
            
    except Exception as e:
        print(f"ERROR: Failed to generate prompts: {e}")
        return []


def _generate_all_prompts(count_per_niche: int = 50) -> list[dict]:
    """Generate prompts for all niches, avoiding duplicates."""
    used_prompts = _load_used_prompts()
    all_prompts = []
    
    for niche in NICHES:
        prompts = _generate_prompts_with_groq(niche, count_per_niche, used_prompts)
        all_prompts.extend(prompts)
        for p in prompts:
            used_prompts.append(p.get("prompt", ""))
    
    _save_used_prompts(used_prompts)
    
    print(f"Total prompts generated: {len(all_prompts)}")
    return all_prompts


def retry_with_backoff(max_retries=3, base_delay=2, max_delay=30):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    print(f"  Attempt {attempt + 1}/{max_retries} failed: {e}")
                    if attempt < max_retries - 1:
                        print(f"  Retrying in {delay}s...")
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from prompt_library import CATEGORIES, get_prompts_for_category
from generator import generate_category_pack, get_groq_client, load_config
from image_generator import ImageGenerator

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "output"
REPORTS_DIR = Path(__file__).parent / "reports"
ZIP_DIR = Path(__file__).parent / "zips"

IMAGES_PER_PACK = None  # Will be read from config


def send_email(subject, body, attachment_path=None):
    """Send email with optional ZIP attachment (must be under 25 MB for Gmail)."""
    sender = os.environ.get("SENDER_EMAIL")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = sender

    if not sender or not password:
        print("ERROR: Email credentials not set. Skipping email.")
        return False

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    if attachment_path and Path(attachment_path).exists():
        size_mb = Path(attachment_path).stat().st_size / (1024 * 1024)
        if size_mb > GMAIL_MAX_MB:
            print(f"  ZIP is {size_mb:.1f} MB, exceeds {GMAIL_MAX_MB} MB limit.")
            print("  Attempting to recompress at quality 60...")
            attachment_path = _recompress_zip(attachment_path, quality=60)
            if attachment_path is None:
                print("  ERROR: Could not reduce ZIP under limit. Skipping email.")
                return False
            size_mb = Path(attachment_path).stat().st_size / (1024 * 1024)
            if size_mb > GMAIL_MAX_MB:
                print(f"  Still {size_mb:.1f} MB after recompress. Skipping email.")
                return False

        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "zip")
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


def _recompress_zip(zip_path, quality=60):
    """Recompress every image inside the ZIP at lower quality. Returns new path or None."""
    original = Path(zip_path)
    recompressed = original.with_name(original.stem + "_compressed.zip")
    try:
        with zipfile.ZipFile(original, "r") as zf_in, \
             zipfile.ZipFile(recompressed, "w", zipfile.ZIP_DEFLATED) as zf_out:
            for item in zf_in.infolist():
                data = zf_in.read(item.filename)
                if item.filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    try:
                        img = Image.open(io.BytesIO(data))
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=quality, optimize=True)
                        data = buf.getvalue()
                        out_name = Path(item.filename).stem + ".jpg"
                    except Exception:
                        out_name = item.filename
                else:
                    out_name = item.filename
                zf_out.writestr(out_name, data)
        return recompressed
    except Exception as e:
        print(f"  Recompress failed: {e}")
        return None


def compress_image(src_path, quality=85):
    """Compress an image to JPEG at the given quality, returning bytes."""
    img = Image.open(src_path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def create_zip(pack_dir, pack_name, zip_path):
    """Create ZIP from pack images, compressing to JPEG quality 85."""
    images_dir = Path(pack_dir) / "images"
    if not images_dir.exists():
        print(f"  No images directory found at {images_dir}")
        return None

    image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg"))
    if not image_files:
        print(f"  No images found in {images_dir}")
        return None

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for img_file in sorted(image_files):
            jpeg_data = compress_image(img_file, quality=85)
            jpeg_name = img_file.stem + ".jpg"
            zf.writestr(jpeg_name, jpeg_data)
            print(f"    Added: {jpeg_name} ({len(jpeg_data) / 1024:.0f} KB)")

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"  ZIP created: {zip_path.name} ({size_mb:.1f} MB, {len(image_files)} images)")
    return zip_path


def generate_daily_report(packs_created, zip_files):
    """Generate and send daily report with ZIP attachments"""
    now = datetime.now()
    report_lines = [
        "=== ClipForge AI Daily Report ===",
        f"Date: {now.strftime('%Y-%m-%d %H:%M')}",
        "",
        "--- Packs Created Today ---",
    ]

    for pack in packs_created:
        price = pack.get("price", 400) / 100
        report_lines.append(f"  {pack['pack_name']} - ${price:.2f} - {pack['category']}")

    report_lines.extend([
        "",
        "--- ZIP Files ---",
    ])

    for zip_file in zip_files:
        report_lines.append(f"  {zip_file}")

    report_lines.extend([
        "",
        "--- Next Actions ---",
        "1. Upload ZIPs to Wirestock (distributes to Shutterstock, Adobe Stock, Getty, etc.)",
        "2. Or sell directly on Gumroad/Etsy",
        "3. Share sample images on Twitter/Reddit/Pinterest",
    ])

    report = "\n".join(report_lines)
    REPORTS_DIR.mkdir(exist_ok=True)
    report_path = REPORTS_DIR / f"report_{now.strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_path, "w") as f:
        f.write(report)

    print(report)

    for zip_file in zip_files:
        if Path(zip_file).exists():
            send_email(
                f"ClipForge ZIP - {now.strftime('%Y-%m-%d')}",
                f"{report}\n\nUpload this ZIP to Wirestock or sell on Gumroad.",
                attachment_path=zip_file
            )

    if not zip_files:
        send_email(f"ClipForge Report - {now.strftime('%Y-%m-%d')}", report)

    return report


def run_pipeline(count=3):
    """Run the full pipeline"""
    import time as _time
    PIPELINE_START = _time.time()
    DEADLINE = PIPELINE_START + 5 * 3600

    print("=" * 50)
    print("ClipForge AI - Full Pipeline")
    print("=" * 50)

    DATA_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    ZIP_DIR.mkdir(exist_ok=True)

    config = load_config()
    client = get_groq_client()

    global IMAGES_PER_PACK
    IMAGES_PER_PACK = config.get("generation", {}).get("images_per_pack", 20)

    try:
        all_prompts = _generate_all_prompts(count_per_niche=50)
        if not all_prompts:
            print("ERROR: No prompts generated, falling back to static library")
            from prompt_library import get_all_prompts
            all_prompts = get_all_prompts()
    except Exception as e:
        print(f"Dynamic generation failed: {e}, falling back to static library")
        from prompt_library import get_all_prompts
        all_prompts = get_all_prompts()

    random.shuffle(all_prompts)
    selected_prompts = all_prompts[:IMAGES_PER_PACK]

    packs_created = []
    zip_files = []

    try:
        pack_name = f"clipforge_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"\n--- Generating {len(selected_prompts)} images ---")

        generator = ImageGenerator(str(OUTPUT_DIR))
        try:
            results = generator.generate_pack(
                [p.get("prompt", "") for p in selected_prompts],
                pack_name,
                "mixed",
                deadline=DEADLINE
            )
            print(f"  Generated {len(results)} images")
        except Exception as e:
            print(f"  Image generation failed: {e}")

        try:
            print("Creating ZIP file...")
            zip_path = ZIP_DIR / f"{pack_name}.zip"
            pack_dir = OUTPUT_DIR / pack_name
            create_zip(pack_dir, pack_name, zip_path)
            zip_files.append(str(zip_path))
        except Exception as e:
            print(f"  ZIP creation failed: {e}")

        packs_created.append({"pack_name": pack_name, "prompts": selected_prompts})

    except KeyboardInterrupt:
        print("\nPipeline interrupted, generating report...")
    except Exception as e:
        print(f"\nPipeline error: {e}")

    print("\n" + "=" * 50)
    print("Generating daily report...")
    generate_daily_report(packs_created, zip_files)

    elapsed = _time.time() - PIPELINE_START
    print(f"\nPipeline complete! ({elapsed/60:.1f} minutes)")
    return packs_created


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ClipForge AI Pipeline")
    parser.add_argument("--count", type=int, default=1, help="Number of packs")
    args = parser.parse_args()
    run_pipeline(count=args.count)
