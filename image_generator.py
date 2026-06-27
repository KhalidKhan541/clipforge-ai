"""
Image Generator — Uses Pollinations.ai (free, no API key) to generate clip art images
"""
import os
import time
import urllib.request
import urllib.parse
import json
from pathlib import Path


class ImageGenerator:
    BASE_URL = "https://image.pollinations.ai/prompt"

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
            urllib.request.urlretrieve(url, output_path)
            time.sleep(2)
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

    def create_zip(self, pack_dir, pack_name):
        """Create a ZIP file from the pack directory"""
        import zipfile
        zip_path = self.output_dir / f"{pack_name}.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(pack_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, pack_dir)
                    zipf.write(file_path, arcname)

        return zip_path


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
        zip_path = generator.create_zip("output/test_pack", "test_pack")
        print(f"ZIP created: {zip_path}")
