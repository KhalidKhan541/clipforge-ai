"""
Image Generator — Uses Pollinations.ai to generate clip art images
Updated for new API (2026): gen.pollinations.ai/image/
"""
import os
import time
import urllib.request
import urllib.parse
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


class ImageGenerator:
    BASE_URL = "https://gen.pollinations.ai/image"

    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_image(self, prompt, filename, width=1024, height=1024, seed=None):
        """Generate a single image using Pollinations.ai"""
        enhanced_prompt = f"{prompt}, flat vector illustration, clean lines, white background, high resolution PNG, transparent background, clip art style"

        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        url = f"{self.BASE_URL}/{encoded_prompt}?width={width}&height={height}&nologo=true"

        if seed:
            url += f"&seed={seed}"

        output_path = self.output_dir / filename

        try:
            print(f"  Generating: {filename}...")
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=60) as response:
                with open(output_path, 'wb') as f:
                    f.write(response.read())
            time.sleep(3)
            return output_path
        except Exception as e:
            print(f"  Error generating {filename}: {e}")
            return None

    def generate_pack(self, prompts, pack_name, category):
        """Generate a full pack of images"""
        pack_dir = self.output_dir / pack_name / "images"
        pack_dir.mkdir(parents=True, exist_ok=True)

        generated = []
        for i, prompt_data in enumerate(prompts):
            prompt = prompt_data.get("prompt", prompt_data) if isinstance(prompt_data, dict) else prompt_data
            filename = f"{category}_{i+1:03d}.png"

            result = self.generate_image(prompt, str(pack_dir / filename), seed=i)
            if result:
                generated.append({
                    "filename": filename,
                    "prompt": prompt,
                    "path": str(result)
                })

            if (i + 1) % 10 == 0:
                print(f"  Generated {i+1}/{len(prompts)} images")

        return generated

    def create_pdf(self, pack_dir, pack_name, category, pack_data=None):
        """Create a PDF file from the pack images"""
        pdf_path = self.output_dir / f"{pack_name}.pdf"

        c = canvas.Canvas(str(pdf_path), pagesize=A4)
        width, height = A4

        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height - 50, pack_name.replace("_", " ").title())

        c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, height - 80, f"Category: {category}")

        if pack_data:
            price = pack_data.get("price", 4.99)
            c.drawCentredString(width/2, height - 100, f"Price: ${price:.2f}")

        c.showPage()

        images_dir = Path(pack_dir) / "images"
        if images_dir.exists():
            for img_file in sorted(images_dir.glob("*.png")):
                try:
                    img = ImageReader(str(img_file))
                    img_width = width - 100
                    img_height = img_width
                    x = 50
                    y = height - 50 - img_height

                    c.drawImage(img, x, y, width=img_width, height=img_height)
                    c.showPage()
                except Exception as e:
                    print(f"  Error adding {img_file.name} to PDF: {e}")

        c.save()
        return pdf_path


if __name__ == "__main__":
    generator = ImageGenerator()

    test_prompts = [
        "cute kawaii cat face",
        "boho floral bouquet",
        "retro sunset gradient"
    ]

    print("Testing Pollinations.ai image generation...")
    results = generator.generate_pack(test_prompts, "test_pack", "test")
    print(f"Generated {len(results)} images")

    if results:
        pdf_path = generator.create_pdf("output/test_pack", "test_pack", "test")
        print(f"PDF created: {pdf_path}")
