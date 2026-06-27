#!/usr/bin/env python3
"""
ClipForge AI — Pack Assembler
Takes generated prompts from generator.py output and creates
organized, delivery-ready clip art packs with PDF guides,
README files, and metadata.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable, Image as RLImage
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
except ImportError:
    print("ERROR: reportlab library not installed. Run: pip install reportlab")
    sys.exit(1)

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
CONFIG_PATH = PROJECT_DIR / "config.json"
PACKS_DIR = PROJECT_DIR / "packs"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"ERROR: config.json not found at {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_pack_data(pack_json_path: str) -> dict:
    path = Path(pack_json_path)
    if not path.exists():
        print(f"ERROR: Pack JSON not found at {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def sanitize_name(name: str) -> str:
    safe = name.lower().strip()
    safe = safe.replace(" ", "_")
    safe = "".join(c for c in safe if c.isalnum() or c == "_")
    return safe[:80]


def create_pack_directories(pack_dir: Path) -> dict:
    dirs = {
        "root": pack_dir,
        "prompts": pack_dir / "prompts",
        "guide": pack_dir / "guide",
        "images": pack_dir / "images",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def save_prompts(pack_data: dict, prompts_dir: Path) -> Path:
    prompts_file = prompts_dir / "prompts.json"
    with open(prompts_file, "w", encoding="utf-8") as f:
        json.dump(pack_data["prompts"], f, indent=2, ensure_ascii=False)

    txt_file = prompts_dir / "playground_ai_prompts.txt"
    lines = []
    for i, p in enumerate(pack_data["prompts"], 1):
        lines.append(f"=== Prompt {i}: {p.get('title', 'Untitled')} ===")
        lines.append(f"Price: ${p.get('price', 0):.2f}")
        lines.append("")
        lines.append(p.get("prompt", ""))
        lines.append("")
        lines.append(f"Etsy Tags: {', '.join(p.get('tags', []))}")
        lines.append("")
        lines.append(f"Etsy Description:")
        lines.append(p.get("description", ""))
        lines.append("")
        lines.append(f"Gumroad Title: {p.get('gumroad_title', '')}")
        lines.append(f"Gumroad Description:")
        lines.append(p.get("gumroad_desc", ""))
        lines.append("")
        lines.append("-" * 60)
        lines.append("")

    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return prompts_file


def create_delivery_guide(pack_data: dict, guide_dir: Path, config: dict) -> Path:
    pdf_path = guide_dir / "delivery_guide.pdf"
    owner = config.get("owner", {})
    website = config.get("platforms", {}).get("cloudflare_pages", {}).get("custom_domain")
    if not website:
        site_name = config.get("platforms", {}).get("cloudflare_pages", {}).get("site_name", "clipforge-ai")
        website = f"https://{site_name}.pages.dev"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PackTitle",
        parent=styles["Title"],
        fontSize=26,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
        alignment=TA_CENTER,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=13,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=20,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=16,
        textColor=colors.HexColor("#0f3460"),
        spaceBefore=18,
        spaceAfter=8,
        borderWidth=0,
        borderPadding=0,
    )

    body_style = ParagraphStyle(
        "BodyText2",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#333333"),
        spaceAfter=8,
    )

    bullet_style = ParagraphStyle(
        "Bullet",
        parent=body_style,
        leftIndent=20,
        bulletIndent=8,
        spaceAfter=4,
    )

    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#999999"),
        alignment=TA_CENTER,
    )

    story = []

    story.append(Paragraph(pack_data.get("pack_name", "Clip Art Pack"), title_style))
    story.append(Paragraph(pack_data.get("category_name", "General"), subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0f3460"), spaceAfter=16))

    story.append(Paragraph("Pack Overview", heading_style))
    overview_data = [
        ["Pack Name", pack_data.get("pack_name", "N/A")],
        ["Category", pack_data.get("category_name", "N/A")],
        ["Niche", pack_data.get("niche", "N/A")],
        ["Total Images", str(pack_data.get("count_generated", 0))],
        ["Created", pack_data.get("created_at", "N/A")[:10]],
    ]
    overview_table = Table(overview_data, colWidths=[2 * inch, 4.5 * inch])
    overview_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8eaf6")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1a1a2e")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Usage Rights & License", heading_style))
    story.append(Paragraph(
        "You have purchased a <b>commercial use license</b> for this clip art pack. "
        "You are free to use these images in personal and commercial projects, "
        "including products for sale on Etsy, Amazon, Shopify, and other marketplaces.",
        body_style
    ))
    story.append(Paragraph("What you CAN do:", body_style))
    can_items = [
        "Use in physical and digital products for sale",
        "Use in social media posts, ads, and marketing materials",
        "Use in print-on-demand products (mugs, t-shirts, stickers)",
        "Use in website design and branding",
        "Modify, resize, and combine with other elements",
    ]
    for item in can_items:
        story.append(Paragraph(f"\u2022  {item}", bullet_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("What you CANNOT do:", body_style))
    cannot_items = [
        "Redistribute or resell the clip art files as-is",
        "Include in other clip art packs or design asset bundles",
        "Claim authorship of the original artwork",
        "Use in any way that is offensive, illegal, or hateful",
    ]
    for item in cannot_items:
        story.append(Paragraph(f"\u2022  {item}", bullet_style))

    story.append(Spacer(1, 16))
    story.append(Paragraph("How to Use in Playground AI", heading_style))
    steps = [
        "Log in to Playground AI at <b>playground.com</b>",
        "Click <b>Create</b> to start a new image generation",
        "Paste the prompt from the included <b>playground_ai_prompts.txt</b> file",
        "Set image size to <b>1024x1024</b> or <b>1536x1024</b> for best results",
        "Use <b>stable-diffusion-xl</b> or <b>playground-v2.5</b> model",
        "Set guidance scale to <b>7-12</b> for balanced results",
        "Generate and download your PNG files",
        "Organize your downloads in the provided <b>images/</b> folder",
    ]
    for i, step in enumerate(steps, 1):
        story.append(Paragraph(f"<b>{i}.</b>  {step}", bullet_style))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Included Files", heading_style))
    files_data = [
        ["File/Folder", "Description"],
        ["prompts/", "Contains prompts.json and playground_ai_prompts.txt"],
        ["prompts/prompts.json", "Machine-readable prompt data"],
        ["prompts/playground_ai_prompts.txt", "Copy-paste ready prompts for Playground AI"],
        ["guide/", "This delivery guide (PDF)"],
        ["guide/delivery_guide.pdf", "Usage rights, instructions, and pack info"],
        ["images/", "Drop your generated PNG images here"],
        ["metadata.json", "Pack metadata for your records"],
        ["README.txt", "Quick reference for pack contents"],
    ]
    files_table = Table(files_data, colWidths=[2.8 * inch, 3.7 * inch])
    files_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(files_table)

    story.append(Spacer(1, 20))
    story.append(Paragraph("Prompt List Preview", heading_style))
    preview_data = [["#", "Title", "Price"]]
    for i, p in enumerate(pack_data.get("prompts", [])[:10], 1):
        title = p.get("title", "Untitled")
        if len(title) > 50:
            title = title[:47] + "..."
        price = f"${p.get('price', 0):.2f}"
        preview_data.append([str(i), title, price])

    if len(pack_data.get("prompts", [])) > 10:
        remaining = len(pack_data["prompts"]) - 10
        preview_data.append(["...", f"+{remaining} more prompts in prompts/ folder", ""])

    preview_table = Table(preview_data, colWidths=[0.5 * inch, 4.5 * inch, 1 * inch])
    preview_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3460")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
    ]))
    story.append(preview_table)

    story.append(Spacer(1, 24))

    if HAS_QRCODE:
        story.append(Paragraph("Visit Our Store", heading_style))
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(website)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#0f3460", back_color="white")
        qr_path = guide_dir / "_qr_temp.png"
        qr_img.save(str(qr_path))
        story.append(RLImage(str(qr_path), width=1.5 * inch, height=1.5 * inch))
        story.append(Paragraph(f"Scan to visit: {website}", body_style))
    else:
        story.append(Paragraph("Visit Our Store", heading_style))
        story.append(Paragraph(f"Website: <b>{website}</b>", body_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc"), spaceAfter=12))

    support_email = owner.get("email", "support@clipforge.ai")
    bot_name = config.get("bot_name", "ClipForge AI")
    story.append(Paragraph(
        f"Thank you for purchasing from <b>{bot_name}</b>!",
        ParagraphStyle("Thanks", parent=body_style, alignment=TA_CENTER, fontSize=12)
    ))
    story.append(Paragraph(
        f"Questions? Contact us at <b>{support_email}</b>",
        ParagraphStyle("Contact", parent=footer_style, fontSize=10, textColor=colors.HexColor("#555555"))
    ))
    story.append(Paragraph(
        f"Generated by {bot_name} \u2014 {datetime.now().strftime('%Y-%m-%d')}",
        footer_style
    ))

    doc.build(story)

    if HAS_QRCODE and qr_path.exists():
        qr_path.unlink()

    print(f"  Delivery guide created: {pdf_path}")
    return pdf_path


def create_readme(pack_data: dict, pack_dir: Path, config: dict) -> Path:
    readme_path = pack_dir / "README.txt"
    owner = config.get("owner", {})
    bot_name = config.get("bot_name", "ClipForge AI")
    support_email = owner.get("email", "support@clipforge.ai")

    lines = [
        "=" * 60,
        f"  {pack_data.get('pack_name', 'Clip Art Pack')}",
        f"  {pack_data.get('category_name', 'General')}",
        "=" * 60,
        "",
        "PACK CONTENTS",
        "-" * 40,
        f"  Pack Name:       {pack_data.get('pack_name', 'N/A')}",
        f"  Category:        {pack_data.get('category_name', 'N/A')}",
        f"  Niche:           {pack_data.get('niche', 'N/A')}",
        f"  Total Prompts:   {pack_data.get('count_generated', 0)}",
        f"  Created:         {pack_data.get('created_at', 'N/A')[:10]}",
        f"  Generation Model:{pack_data.get('model', 'N/A')}",
        "",
        "FILE STRUCTURE",
        "-" * 40,
        f"  prompts/",
        f"    prompts.json              - Machine-readable prompt data",
        f"    playground_ai_prompts.txt - Copy-paste prompts for Playground AI",
        f"  guide/",
        f"    delivery_guide.pdf        - Full usage rights and instructions",
        f"  images/",
        f"    (drop your generated PNGs here)",
        f"  metadata.json               - Pack metadata",
        f"  README.txt                  - This file",
        "",
        "FILE NAMING CONVENTION",
        "-" * 40,
        "  When you generate images from these prompts, we recommend",
        "  naming files using this pattern:",
        "",
        "    {category}_{pack_number}_{image_number}.png",
        "",
        "  Example: boho_florals_01_001.png",
        "           kawaii_cute_02_015.png",
        "",
        "  Keep files in lowercase with underscores. This helps with",
        "  organization and makes bulk operations easier.",
        "",
        "ATTRIBUTION",
        "-" * 40,
        "  Attribution is NOT required. You are free to sell products",
        "  using these clip art designs without crediting ClipForge AI.",
        "",
        "  However, if you'd like to show support, a simple mention",
        "  like 'Made with ClipForge AI clip art' is always appreciated!",
        "",
        "LICENSE",
        "-" * 40,
        "  Commercial Use:     ALLOWED",
        "  Personal Use:       ALLOWED",
        "  Redistribution:     NOT ALLOWED",
        "  Resale as Assets:   NOT ALLOWED",
        "",
        "  You CAN use these designs in products for sale.",
        "  You CANNOT resell the clip art files themselves.",
        "",
        "SUPPORT",
        "-" * 40,
        f"  Email:    {support_email}",
        f"  Website:  https://{config.get('platforms', {}).get('cloudflare_pages', {}).get('site_name', 'clipforge-ai')}.pages.dev",
        f"  Bot:      {bot_name}",
        "",
        "  If you have any issues or questions, please reach out.",
        "  We typically respond within 24 hours.",
        "",
        "=" * 60,
        f"  Thank you for choosing {bot_name}!",
        f"  We hope these designs help your creative projects shine.",
        "=" * 60,
    ]

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  README created: {readme_path}")
    return readme_path


def create_metadata(pack_data: dict, pack_dir: Path, config: dict) -> Path:
    metadata_path = pack_dir / "metadata.json"
    prompts_meta = []
    for p in pack_data.get("prompts", []):
        prompts_meta.append({
            "title": p.get("title", "Untitled"),
            "price": p.get("price", 0),
            "tags": p.get("tags", []),
            "gumroad_title": p.get("gumroad_title", ""),
        })

    site_name = config.get("platforms", {}).get("cloudflare_pages", {}).get("site_name", "clipforge-ai")

    metadata = {
        "pack_name": pack_data.get("pack_name", "Clip Art Pack"),
        "category": pack_data.get("category", "general"),
        "category_name": pack_data.get("category_name", "General"),
        "niche": pack_data.get("niche", ""),
        "price": config.get("generation", {}).get("pricing", {}).get("starter_pack", 2.99),
        "total_images": pack_data.get("count_generated", 0),
        "created_date": pack_data.get("created_at", datetime.now(timezone.utc).isoformat())[:10],
        "license": "commercial_use",
        "license_terms": {
            "commercial_use": True,
            "personal_use": True,
            "redistribution": False,
            "resale_as_assets": False,
        },
        "format": config.get("delivery", {}).get("format", "PNG + PDF guide"),
        "prompts": prompts_meta,
        "bot_name": config.get("bot_name", "ClipForge AI"),
        "owner": {
            "name": config.get("owner", {}).get("name", ""),
            "email": config.get("owner", {}).get("email", ""),
        },
        "website": f"https://{site_name}.pages.dev",
        "generation_model": pack_data.get("model", "unknown"),
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"  Metadata created: {metadata_path}")
    return metadata_path


def assemble_pack(pack_json_path: str, output_dir: str = None) -> Path:
    print(f"\nAssembling pack from: {pack_json_path}")
    config = load_config()
    pack_data = load_pack_data(pack_json_path)

    pack_name = sanitize_name(pack_data.get("pack_name", "clip_art_pack"))
    if output_dir:
        pack_root = Path(output_dir) / pack_name
    else:
        pack_root = PACKS_DIR / pack_name

    dirs = create_pack_directories(pack_root)

    print(f"\n  Pack: {pack_data.get('pack_name', 'N/A')}")
    print(f"  Output: {dirs['root']}")

    save_prompts(pack_data, dirs["prompts"])
    create_delivery_guide(pack_data, dirs["guide"], config)
    create_readme(pack_data, dirs["root"], config)
    create_metadata(pack_data, dirs["root"], config)

    print(f"\nPack assembly complete: {dirs['root']}")
    print(f"  Contents:")
    for item in sorted(dirs["root"].iterdir()):
        if item.is_file():
            print(f"    {item.name}")
        elif item.is_dir():
            sub_count = sum(1 for _ in item.iterdir())
            print(f"    {item.name}/ ({sub_count} files)")

    return dirs["root"]


def main():
    parser = argparse.ArgumentParser(
        description="ClipForge AI — Pack Assembler: Create delivery-ready clip art packs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pack_assembler.py data/boho_florals_pack1_20250101_120000.json
  python pack_assembler.py data/boho_florals_pack1_20250101_120000.json --output ./my_packs
  python pack_assembler.py --all
        """
    )
    parser.add_argument(
        "pack_json",
        nargs="?",
        type=str,
        default=None,
        help="Path to the pack JSON file from generator.py"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory for assembled packs (default: ./packs/)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Assemble all pack JSON files in the data/ directory"
    )
    args = parser.parse_args()

    if not args.pack_json and not args.all:
        parser.print_help()
        sys.exit(1)

    if args.all:
        data_dir = PROJECT_DIR / "data"
        if not data_dir.exists():
            print(f"ERROR: data/ directory not found at {data_dir}")
            sys.exit(1)
        json_files = sorted(data_dir.glob("*.json"))
        if not json_files:
            print(f"No pack JSON files found in {data_dir}")
            sys.exit(1)
        print(f"Found {len(json_files)} pack files to assemble:")
        for jf in json_files:
            print(f"  - {jf.name}")
        for jf in json_files:
            assemble_pack(str(jf), args.output)
    else:
        assemble_pack(args.pack_json, args.output)


if __name__ == "__main__":
    main()
