"""
Gumroad Uploader — Auto-creates products on Gumroad using their API
"""
import os
import json
import requests
import time
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
                       preview_url=None, tags=None, file_path=None):
        """Create a new product on Gumroad"""
        data = {
            "name": name,
            "price": price_cents,
            "description": description,
            "url": url or name.lower().replace(" ", "-"),
            "currency": "usd",
            "quantity": 0,
            "variants": [],
        }

        if tags:
            data["tags"] = ",".join(tags)

        resp = requests.post(f"{self.API_BASE}/products",
                             headers=self.headers, data=data)
        resp.raise_for_status()
        product = resp.json().get("product", {})

        if file_path and product.get("id"):
            self.upload_file(product["id"], file_path)

        return product

    def upload_file(self, product_id, file_path):
        """Upload a file to an existing product"""
        url = f"{self.API_BASE}/products/{product_id}/upload"
        with open(file_path, "rb") as f:
            resp = requests.post(url, headers=self.headers,
                                 files={"file": f},
                                 data={"product_id": product_id})
        resp.raise_for_status()
        return resp.json()

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

    def upload_clip_art_pack(self, pack_data, zip_path):
        """Upload a complete clip art pack to Gumroad"""
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
            tags=tags,
            file_path=str(zip_path)
        )

        print(f"  Product created: {product.get('id')}")
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
