#!/usr/bin/env python3
"""
ClipForge AI — Main Content Generation Script
Generates Playground AI prompts, Etsy listings, and Gumroad products
for clip art packs using the Groq API (free tier).
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from groq import Groq, APIStatusError, APIConnectionError, APITimeoutError
except ImportError:
    print("ERROR: groq library not installed. Run: pip install groq")
    sys.exit(1)

from prompt_library import CATEGORIES, get_prompts_for_category

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
DATA_DIR = SCRIPT_DIR / "data"

GROQ_MODEL = "llama-3.3-70b-versatile"
GENERATION_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_DELAY = 2


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"ERROR: config.json not found at {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_groq_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY environment variable not set.")
        print("  Get a free key at: https://console.groq.com/keys")
        sys.exit(1)
    return Groq(api_key=api_key)


def build_system_prompt(config: dict, category_name: str, niche: str) -> str:
    pricing = config.get("generation", {}).get("pricing", {})
    style = config.get("generation", {}).get("image_style", "flat vector illustration")
    audience = config.get("content", {}).get("target_audience", "Etsy sellers")
    brand_voice = config.get("content", {}).get("brand_voice", "friendly, creative, helpful")

    return f"""You are ClipForge AI, an expert clip art content generator for {audience}.
Brand voice: {brand_voice}.

Your job: Generate ONE complete clip art product listing for the "{category_name}" category.
Niche: {niche}.

For each input seed prompt, return a JSON object with exactly these keys:
- "prompt": A detailed Playground AI / Stable Diffusion image generation prompt (80-150 words). Must include: subject description, art style "{style}", color palette, composition notes, and quality tags like "4K, high detail, print ready". Do NOT include quotes inside the prompt string.
- "title": Etsy product title, max 140 characters. Front-load keywords. Use pipe separators. Example: "Boho Floral Clip Art | Wildflower Bouquet PNG | Wedding Invitation Graphics | Commercial Use"
- "tags": Array of exactly 13 Etsy SEO tags. Each tag max 20 characters. Mix broad and specific keywords. No hashtags.
- "description": Etsy product description, 1000-1200 characters. Include: what's included, file format (PNG), use cases, commercial license info, instant download note, and a friendly call to action. Use keywords naturally.
- "price": Recommended Etsy price as a number (e.g. 4.99). Use pricing tiers: starter=${{pricing.get('starter_pack', 2.99)}}, mega=${{pricing.get('mega_pack', 6.99)}}, bundle=${{pricing.get('bundle_pack', 9.99)}}.
- "gumroad_title": Gumroad product title, max 80 characters. More casual than Etsy.
- "gumroad_desc": Gumroad product description, 400-600 characters. Conversational tone, highlight value and instant download.

Return ONLY valid JSON. No markdown, no code fences, no commentary outside the JSON.
The JSON must be a single object (not an array)."""


def build_user_prompt(seed_prompt: str, pack_index: int, image_index: int) -> str:
    return f"""Generate a complete clip art product listing for this seed concept:
"{seed_prompt}"

This will be image #{image_index + 1} in pack #{pack_index + 1}.
Remember: return ONLY a single JSON object with keys: prompt, title, tags, description, price, gumroad_title, gumroad_desc"""


def parse_json_response(raw: str) -> Optional[dict]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
    return None


def generate_single_listing(
    client: Groq,
    system_prompt: str,
    user_prompt: str,
    retry: int = 0
) -> Optional[dict]:
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=2000,
            timeout=GENERATION_TIMEOUT,
        )
        raw = response.choices[0].message.content
        parsed = parse_json_response(raw)
        if parsed is None:
            print(f"    [WARN] Failed to parse JSON response, retrying...")
            if retry < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                return generate_single_listing(client, system_prompt, user_prompt, retry + 1)
            return None

        required_keys = {"prompt", "title", "tags", "description", "price", "gumroad_title", "gumroad_desc"}
        if not required_keys.issubset(parsed.keys()):
            missing = required_keys - set(parsed.keys())
            print(f"    [WARN] Missing keys: {missing}, retrying...")
            if retry < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                return generate_single_listing(client, system_prompt, user_prompt, retry + 1)
            return None

        if isinstance(parsed["tags"], str):
            parsed["tags"] = [t.strip() for t in parsed["tags"].split(",") if t.strip()]
        parsed["tags"] = parsed["tags"][:13]

        if isinstance(parsed["price"], str):
            try:
                parsed["price"] = float(parsed["price"].replace("$", ""))
            except ValueError:
                parsed["price"] = 4.99

        return parsed

    except APITimeoutError:
        print(f"    [WARN] API timeout, retrying... (attempt {retry + 1}/{MAX_RETRIES})")
        if retry < MAX_RETRIES:
            time.sleep(RETRY_DELAY * (retry + 1))
            return generate_single_listing(client, system_prompt, user_prompt, retry + 1)
        return None
    except APIConnectionError as e:
        print(f"    [WARN] Connection error: {e}, retrying...")
        if retry < MAX_RETRIES:
            time.sleep(RETRY_DELAY * (retry + 1))
            return generate_single_listing(client, system_prompt, user_prompt, retry + 1)
        return None
    except APIStatusError as e:
        if e.status_code == 429:
            wait = RETRY_DELAY * (retry + 1) * 2
            print(f"    [WARN] Rate limited, waiting {wait}s...")
            if retry < MAX_RETRIES:
                time.sleep(wait)
                return generate_single_listing(client, system_prompt, user_prompt, retry + 1)
        print(f"    [ERROR] API status {e.status_code}: {e.message}")
        return None
    except Exception as e:
        print(f"    [ERROR] Unexpected error: {e}")
        return None


def generate_category_pack(
    client: Groq,
    config: dict,
    category_key: str,
    pack_number: int,
    count: int
) -> Optional[dict]:
    cat = CATEGORIES.get(category_key)
    if cat is None:
        print(f"ERROR: Unknown category '{category_key}'")
        print(f"  Available: {', '.join(CATEGORIES.keys())}")
        return None

    category_name = cat["name"]
    niche = cat["niche"]
    prompts = get_prompts_for_category(category_key, count)

    if not prompts:
        print(f"  [WARN] No prompts found for '{category_key}', skipping.")
        return None

    print(f"\n{'='*60}")
    print(f"  Category:  {category_name} ({category_key})")
    print(f"  Niche:     {niche}")
    print(f"  Pack:      #{pack_number}")
    print(f"  Images:    {len(prompts)}")
    print(f"{'='*60}")

    system_prompt = build_system_prompt(config, category_name, niche)
    generated = []
    failed = 0

    for idx, seed in enumerate(prompts):
        print(f"  [{idx + 1:3d}/{len(prompts)}] Generating: {seed[:50]}...", end=" ", flush=True)
        user_prompt = build_user_prompt(seed, pack_number - 1, idx)
        listing = generate_single_listing(client, system_prompt, user_prompt)
        if listing is None:
            print("FAILED")
            failed += 1
            continue
        generated.append(listing)
        print(f"OK  (${listing.get('price', 0):.2f})")

    if not generated:
        print(f"\n  [ERROR] All generations failed for {category_key}. Skipping save.")
        return None

    timestamp = datetime.now(timezone.utc).isoformat()
    pack_data = {
        "category": category_key,
        "category_name": category_name,
        "niche": niche,
        "pack_name": f"{category_name} Clip Art Pack #{pack_number}",
        "pack_number": pack_number,
        "count_requested": len(prompts),
        "count_generated": len(generated),
        "count_failed": failed,
        "prompts": generated,
        "created_at": timestamp,
        "model": GROQ_MODEL,
    }

    print(f"\n  Summary: {len(generated)}/{len(prompts)} generated, {failed} failed")

    return pack_data


def save_pack(pack_data: dict) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    cat = pack_data["category"]
    pack_num = pack_data["pack_number"]
    filename = f"{cat}_pack{pack_num}_{ts}.json"
    filepath = DATA_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(pack_data, f, indent=2, ensure_ascii=False)

    print(f"  Saved: {filepath}")
    return filepath


def validate_args(args: argparse.Namespace) -> None:
    if args.category and args.all:
        print("ERROR: Use --category OR --all, not both.")
        sys.exit(1)

    if not args.category and not args.all:
        print("ERROR: Specify --category <name> or --all.")
        print(f"  Available categories: {', '.join(CATEGORIES.keys())}")
        sys.exit(1)

    if args.category and args.category not in CATEGORIES:
        print(f"ERROR: Unknown category '{args.category}'")
        print(f"  Available: {', '.join(CATEGORIES.keys())}")
        sys.exit(1)

    if args.count < 1:
        print("ERROR: --count must be at least 1.")
        sys.exit(1)

    if args.category:
        max_prompts = len(CATEGORIES[args.category].get("prompts", []))
        if args.count > max_prompts:
            print(f"WARNING: --count {args.count} exceeds available prompts ({max_prompts}) for '{args.category}'.")
            print(f"  Will use all {max_prompts} prompts instead.")
            args.count = min(args.count, max_prompts)


def main():
    parser = argparse.ArgumentParser(
        description="ClipForge AI — Generate clip art content packs for Etsy & Gumroad",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generator.py --category boho_florals
  python generator.py --all
  python generator.py --category kawaii_cute --count 2
  python generator.py --all --count 1
        """
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        default=None,
        help=f"Generate a pack for a specific category. Options: {', '.join(CATEGORIES.keys())}"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Generate packs for all categories"
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=1,
        help="Number of packs to generate per category (default: 1)"
    )
    args = parser.parse_args()
    validate_args(args)

    config = load_config()
    client = get_groq_client()

    print(f"\nClipForge AI — Content Generator")
    print(f"Model: {GROQ_MODEL}")
    print(f"Config: {CONFIG_PATH}")

    categories_to_process = []
    if args.all:
        categories_to_process = list(CATEGORIES.keys())
    else:
        categories_to_process = [args.category]

    total_packs = len(categories_to_process) * args.count
    total_expected = 0
    for cat_key in categories_to_process:
        total_expected += min(len(CATEGORIES[cat_key].get("prompts", [])), 50) * args.count

    print(f"Categories: {len(categories_to_process)}")
    print(f"Packs per category: {args.count}")
    print(f"Total packs to generate: {total_packs}")
    print(f"Estimated listings: ~{total_expected}")

    start_time = time.time()
    all_saved = []
    total_generated = 0
    total_failed = 0

    for cat_idx, cat_key in enumerate(categories_to_process):
        for pack_num in range(1, args.count + 1):
            print(f"\n[Pack {cat_idx * args.count + pack_num}/{total_packs}]")
            pack_data = generate_category_pack(client, config, cat_key, pack_num, 50)
            if pack_data:
                filepath = save_pack(pack_data)
                all_saved.append(str(filepath))
                total_generated += pack_data["count_generated"]
                total_failed += pack_data["count_failed"]

            if cat_idx < len(categories_to_process) - 1 or pack_num < args.count:
                print("  Cooling down (2s) to avoid rate limits...")
                time.sleep(2)

    elapsed = time.time() - start_time

    print(f"\n{'='*60}")
    print(f"  GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Time elapsed:   {elapsed:.1f}s")
    print(f"  Packs saved:    {len(all_saved)}")
    print(f"  Listings generated: {total_generated}")
    print(f"  Failed:         {total_failed}")
    print(f"  Output dir:     {DATA_DIR}")

    if all_saved:
        print(f"\n  Files created:")
        for f in all_saved:
            print(f"    {f}")


if __name__ == "__main__":
    main()
