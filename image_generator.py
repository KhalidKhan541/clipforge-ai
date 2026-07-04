"""
Image Generator — Uses AI Horde (free) to generate clip art images
Generates at 1024x1024 and upscales to meet Wirestock requirements (6MP+)
"""
import os
import time
import json
import io
import urllib.request
import urllib.parse
from pathlib import Path

from PIL import Image


class ImageGenerator:
    BASE_URL = "https://stablehorde.net/api/v2"
    MIN_MP = 6_000_000  # 6 megapixels minimum for Wirestock
    TARGET_SIZE = 3000  # 3000px on longest side

    def __init__(self, output_dir="output", api_key=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key or os.environ.get("AIHORDE_API_KEY", "0000000000")

    def generate_image(self, prompt, output_path, width=1024, height=1024, retries=3, deadline=None):
        """Generate a single image using AI Horde. Generates at 1024x1024 minimum."""
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

        for attempt in range(retries):
            if deadline and time.time() > deadline:
                print(f"  Deadline reached, skipping {Path(output_path).name}")
                return None
            try:
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

                print(f"  Submitting: {Path(output_path).name} (attempt {attempt+1})...")
                with urllib.request.urlopen(req, timeout=60) as response:
                    result = json.loads(response.read())
                    job_id = result.get('id')

                if not job_id:
                    print(f"  Error: No job ID returned")
                    continue

                print(f"  Job {job_id} - waiting...")
                for _ in range(120):
                    if deadline and time.time() > deadline:
                        print(f"\n  Deadline reached during poll")
                        return None
                    time.sleep(15)
                    check_req = urllib.request.Request(
                        f"{self.BASE_URL}/generate/check/{job_id}",
                        headers={'User-Agent': 'ClipForgeAI/1.0'}
                    )
                    with urllib.request.urlopen(check_req, timeout=30) as check_response:
                        status = json.loads(check_response.read())

                    queue_pos = status.get('queue_position', '?')
                    wait_time = status.get('wait_time', '?')
                    print(f"    Queue: {queue_pos}, ETA: {wait_time}s", end='\r')

                    if status.get('done'):
                        break
                    if status.get('faulted'):
                        print(f"\n  Job failed")
                        break

                print()
                status_req = urllib.request.Request(
                    f"{self.BASE_URL}/generate/status/{job_id}",
                    headers={'User-Agent': 'ClipForgeAI/1.0'}
                )
                with urllib.request.urlopen(status_req, timeout=30) as status_response:
                    final_status = json.loads(status_response.read())

                generations = final_status.get('generations', [])
                if not generations:
                    print(f"  No images generated")
                    continue

                image_url = generations[0].get('img')
                if not image_url:
                    print(f"  No image URL")
                    continue

                img_data = urllib.request.urlopen(image_url, timeout=60).read()
                img = Image.open(io.BytesIO(img_data))
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # Upscale to meet Wirestock requirements (6MP+, 3000px+)
                img = self._upscale_for_wirestock(img)

                img.save(output_path, 'PNG', quality=95)
                print(f"  Saved: {Path(output_path).name} ({img.size[0]}x{img.size[1]})")
                return output_path

            except Exception as e:
                print(f"  Error attempt {attempt+1}: {e}")
                if attempt < retries - 1:
                    time.sleep(10 * (attempt + 1))

        return None

    def _upscale_for_wirestock(self, img):
        """Upscale image to meet Wirestock minimum requirements (6MP+, 3000px+)"""
        width, height = img.size
        current_mp = width * height

        # Already meets requirements
        if width >= self.TARGET_SIZE and height >= self.TARGET_SIZE and current_mp >= self.MIN_MP:
            return img

        # Calculate scale factor
        scale_w = self.TARGET_SIZE / width if width < self.TARGET_SIZE else 1
        scale_h = self.TARGET_SIZE / height if height < self.TARGET_SIZE else 1
        scale = max(scale_w, scale_h, 1.0)

        # Ensure minimum megapixels
        new_width = int(width * scale)
        new_height = int(height * scale)
        if new_width * new_height < self.MIN_MP:
            # Increase size to meet minimum
            import math
            scale_mp = math.sqrt(self.MIN_MP / (width * height))
            scale = max(scale, scale_mp)
            new_width = int(width * scale)
            new_height = int(height * scale)

        if scale > 1.0:
            img = img.resize((new_width, new_height), Image.LANCZOS)
            print(f"    Upscaled: {width}x{height} -> {new_width}x{new_height}")

        return img

    def generate_pack(self, prompts, pack_name, category, deadline=None):
        """Generate a full pack of images."""
        pack_dir = self.output_dir / pack_name / "images"
        pack_dir.mkdir(parents=True, exist_ok=True)

        generated = []
        for i, prompt_data in enumerate(prompts):
            if deadline and time.time() > deadline:
                print(f"  Deadline reached, stopping after {len(generated)} images")
                break
            prompt = prompt_data.get("prompt", prompt_data) if isinstance(prompt_data, dict) else prompt_data
            filename = f"{category}_{i+1:03d}.png"
            output_path = pack_dir / filename

            result = self.generate_image(prompt, str(output_path), deadline=deadline)
            if result:
                generated.append({
                    "filename": filename,
                    "prompt": prompt,
                    "path": str(result)
                })

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{len(prompts)} images")

        return generated


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
