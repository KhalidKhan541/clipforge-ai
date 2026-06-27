"""
Image Generator — Uses AI Horde (free) to generate clip art images
Creates PDF files for Gumroad delivery
"""
import os
import time
import json
import urllib.request
import urllib.parse
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


class ImageGenerator:
    BASE_URL = "https://stablehorde.net/api/v2"

    def __init__(self, output_dir="output", api_key=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key or os.environ.get("AIHORDE_API_KEY", "0000000000")

    def generate_image(self, prompt, filename, width=512, height=512):
        """Generate a single image using AI Horde"""
        enhanced_prompt = f"{prompt}, flat vector illustration, clean lines, white background, high resolution, clip art style, digital art"

        data = json.dumps({
            "prompt": enhanced_prompt,
            "params": {
                "width": width,
                "height": height,
                "steps": 30,
                "cfg_scale": 7.5,
                "sampler_name": "k_euler_a"
            },
            "nsfw": False,
            "censor_nsfw": True,
            "models": ["Anything Diffusion"]
        }).encode('utf-8')

        req = urllib.request.Request(
            f"{self.BASE_URL}/generate/async",
            data=data,
            headers={
                'Content-Type': 'application/json',
                'apikey': self.api_key,
                'User-Agent': 'ClipForgeAI/1.0'
            },
            method='POST'
        )

        try:
            print(f"  Submitting: {filename}...")
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read())
                job_id = result.get('id')

            if not job_id:
                print(f"  Error: No job ID returned")
                return None

            print(f"  Job {job_id} - waiting...")
            for _ in range(120):
                time.sleep(15)
                check_req = urllib.request.Request(
                    f"{self.BASE_URL}/generate/check/{job_id}",
                    headers={'User-Agent': 'ClipForgeAI/1.0'}
                )
                with urllib.request.urlopen(check_req, timeout=10) as check_response:
                    status = json.loads(check_response.read())

                queue_pos = status.get('queue_position', '?')
                wait_time = status.get('wait_time', '?')
                print(f"    Queue: {queue_pos}, ETA: {wait_time}s", end='\r')

                if status.get('done'):
                    break
                if status.get('faulted'):
                    print(f"\n  Job failed")
                    return None

            print()
            status_req = urllib.request.Request(
                f"{self.BASE_URL}/generate/status/{job_id}",
                headers={'User-Agent': 'ClipForgeAI/1.0'}
            )
            with urllib.request.urlopen(status_req, timeout=10) as status_response:
                final_status = json.loads(status_response.read())

            generations = final_status.get('generations', [])
            if not generations:
                print(f"  No images generated")
                return None

            image_url = generations[0].get('img')
            if not image_url:
                print(f"  No image URL")
                return None

            output_path = self.output_dir / filename
            urllib.request.urlretrieve(image_url, str(output_path))
            print(f"  Saved: {filename}")
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

            result = self.generate_image(prompt, str(pack_dir / filename))
            if result:
                generated.append({
                    "filename": filename,
                    "prompt": prompt,
                    "path": str(result)
                })

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{len(prompts)} images")

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
            price = pack_data.get("price", 400) / 100
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

    print("Testing AI Horde image generation...")
    results = generator.generate_pack(test_prompts, "test_pack", "test")
    print(f"Generated {len(results)} images")

    if results:
        pdf_path = generator.create_pdf("output/test_pack", "test_pack", "test")
        print(f"PDF created: {pdf_path}")
