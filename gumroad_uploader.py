"""
Gumroad Uploader — Auto-creates products on Gumroad using their API
Uses presigned URLs for file uploads
"""
import os
import json
import math
import requests
from pathlib import Path


class GumroadUploader:
    API_BASE = "https://api.gumroad.com/v2"

    def __init__(self, access_token=None):
        self.access_token = access_token or os.environ.get("GUMROAD_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("GUMROAD_ACCESS_TOKEN not set")
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

    def get_products(self):
        """List all existing products"""
        resp = requests.get(f"{self.API_BASE}/products", headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("products", [])

    def create_product(self, name, price_cents, description="", url=None,
                       tags=None):
        """Create a new product on Gumroad"""
        data = {
            "name": name,
            "price": price_cents,
            "description": description,
            "url": url or name.lower().replace(" ", "-"),
            "currency": "usd",
            "quantity": 0,
        }

        if tags:
            data["tags"] = ",".join(tags)

        resp = requests.post(f"{self.API_BASE}/products",
                             headers=self.headers, data=data)
        resp.raise_for_status()
        return resp.json().get("product", {})

    def presign_upload(self, filename, file_size):
        """Start a multipart upload, returns presigned URLs"""
        data = {
            "filename": filename,
            "file_size": str(file_size),
        }
        resp = requests.post(f"{self.API_BASE}/files/presign",
                             headers=self.headers, data=data)
        resp.raise_for_status()
        return resp.json()

    def upload_parts(self, file_path, presign_data):
        """Upload file parts to presigned URLs"""
        upload_id = presign_data["upload_id"]
        key = presign_data["key"]
        parts = presign_data["parts"]
        file_url = presign_data["file_url"]

        file_size = os.path.getsize(file_path)
        part_size = math.ceil(file_size / len(parts)) if parts else file_size

        etags = []
        with open(file_path, 'rb') as f:
            for i, part in enumerate(parts):
                part_data = f.read(part_size)
                presigned_url = part["presigned_url"]
                part_number = part["part_number"]

                resp = requests.put(presigned_url, data=part_data)
                resp.raise_for_status()
                etag = resp.headers.get("ETag", "")
                etags.append({"part_number": part_number, "etag": etag})

        return upload_id, key, file_url, etags

    def complete_upload(self, upload_id, key, etags):
        """Finalize the multipart upload"""
        data = {
            "upload_id": upload_id,
            "key": key,
        }
        for i, etag_info in enumerate(etags):
            data[f"parts[{i}][part_number]"] = str(etag_info["part_number"])
            data[f"parts[{i}][etag]"] = etag_info["etag"]

        resp = requests.post(f"{self.API_BASE}/files/complete",
                             headers=self.headers, data=data)
        resp.raise_for_status()
        return resp.json()

    def attach_file_to_product(self, product_id, file_url):
        """Attach uploaded file to a product"""
        data = {"file_url": file_url}
        resp = requests.put(f"{self.API_BASE}/products/{product_id}",
                            headers=self.headers, data=data)
        resp.raise_for_status()
        return resp.json()

    def upload_file(self, product_id, file_path):
        """Upload a file to a product using presigned URLs"""
        file_path = Path(file_path)
        file_size = file_path.stat().st_size
        filename = file_path.name

        print(f"  Presigning upload for {filename} ({file_size} bytes)...")
        presign_data = self.presign_upload(filename, file_size)

        print(f"  Uploading {len(presign_data.get('parts', []))} parts...")
        upload_id, key, file_url, etags = self.upload_parts(file_path, presign_data)

        print(f"  Completing upload...")
        self.complete_upload(upload_id, key, etags)

        print(f"  Attaching file to product...")
        self.attach_file_to_product(product_id, file_url)

        return file_url

    def update_product(self, product_id, **kwargs):
        """Update an existing product"""
        resp = requests.put(f"{self.API_BASE}/products/{product_id}",
                            headers=self.headers, data=kwargs)
        resp.raise_for_status()
        return resp.json()

    def delete_product(self, product_id):
        """Delete a product"""
        resp = requests.delete(f"{self.API_BASE}/products/{product_id}",
                               headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def upload_clip_art_pack(self, pack_data, pdf_path):
        """Upload a complete clip art pack to Gumroad as PDF"""
        pack_name = pack_data.get("pack_name", "Untitled Pack")
        category = pack_data.get("category", "general")
        price = pack_data.get("price", 499)
        description = pack_data.get("gumroad_description", "")
        tags = pack_data.get("tags", [])

        print(f"Uploading to Gumroad: {pack_name}")

        product = self.create_product(
            name=pack_name,
            price_cents=price,
            description=description,
            tags=tags
        )

        if product.get("id"):
            print(f"  Product created: {product['id']}")
            self.upload_file(product["id"], pdf_path)
            print(f"  PDF uploaded: {pdf_path}")

        return product


def load_gumroad_config():
    """Load Gumroad settings from config.json"""
    config_path = Path(__file__).parent.parent / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        return config.get("platforms", {}).get("gumroad", {})
    return {}


if __name__ == "__main__":
    uploader = GumroadUploader()

    print("Fetching existing products...")
    products = uploader.get_products()
    print(f"Found {len(products)} products")

    for p in products:
        print(f"  - {p.get('name')} (${p.get('price')/100:.2f})")
