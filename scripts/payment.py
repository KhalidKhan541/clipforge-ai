"""
PayPal payment handler for ClipForge AI clip art store.

Provides payment link generation, order tracking, confirmation emails,
and product delivery via download URLs.
"""

import json
import os
import uuid
import smtplib
import hashlib
import hmac
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
CONFIG_PATH = PROJECT_DIR / "config.json"
ORDERS_PATH = DATA_DIR / "orders.json"
DOWNLOAD_SECRET = os.environ.get("DOWNLOAD_SECRET", "clipforge-download-secret-key")

PAYPAL_SANDBOX_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"
PAYPAL_LIVE_URL = "https://www.paypal.com/cgi-bin/webscr"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

PAYPAL_SMART_BUTTONS_JS = """
<script src="https://www.paypal.com/sdk/client?client-id={client_id}&currency={currency}"></script>

<div id="paypal-button-container"></div>

<script>
  paypal.Buttons({{
    style: {{
      layout: 'vertical',
      color: 'blue',
      shape: 'rect',
      label: 'paypal'
    }},
    createOrder: function(data, actions) {{
      return actions.order.create({{
        purchase_units: [{{
          description: '{description}',
          amount: {{
            currency_code: '{currency}',
            value: '{price}'
          }}
        }}]
      }});
    }},
    onApprove: function(data, actions) {{
      return actions.order.capture().then(function(details) {{
        fetch('/api/payment/confirm', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{
            order_id: '{order_id}',
            paypal_order_id: data.orderID,
            payer_email: details.payer.email_address,
            payer_name: details.payer.name.given_name + ' ' + details.payer.name.surname,
            amount: details.purchase_units[0].amount.value
          }})
        }})
        .then(response => response.json())
        .then(result => {{
          if (result.download_url) {{
            window.location.href = '/thank-you?download=' + result.download_url;
          }}
        }});
      }});
    }},
    onError: function(err) {{
      console.error('PayPal payment error:', err);
      alert('Payment failed. Please try again.');
    }}
  }}).render('#paypal-button-container');
</script>
"""


def _load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class OrderTracker:
    """Manages orders persisted in data/orders.json."""

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._orders: dict = self._load()

    def _load(self) -> dict:
        if ORDERS_PATH.exists():
            with open(ORDERS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"orders": []}

    def _save(self):
        with open(ORDERS_PATH, "w", encoding="utf-8") as f:
            json.dump(self._orders, f, indent=2, ensure_ascii=False)

    def add_order(self, order: dict) -> dict:
        self._orders["orders"].append(order)
        self._save()
        return order

    def get_order(self, order_id: str) -> Optional[dict]:
        for order in self._orders["orders"]:
            if order["order_id"] == order_id:
                return order
        return None

    def update_order(self, order_id: str, updates: dict) -> Optional[dict]:
        order = self.get_order(order_id)
        if order is None:
            return None
        order.update(updates)
        self._save()
        return order

    def list_orders(self) -> list:
        return self._orders["orders"]

    def get_order_by_paypal_id(self, paypal_order_id: str) -> Optional[dict]:
        for order in self._orders["orders"]:
            if order.get("paypal_order_id") == paypal_order_id:
                return order
        return None


class DeliveryManager:
    """Handles product delivery: generates download URLs and serves files."""

    def __init__(self, order_tracker: OrderTracker):
        self.tracker = order_tracker
        self.downloads_dir = PROJECT_DIR / "website" / "downloads"
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    def generate_download_token(self, order_id: str) -> str:
        payload = f"{order_id}:{DOWNLOAD_SECRET}:{int(time.time())}"
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    def generate_download_url(self, order_id: str) -> Optional[str]:
        order = self.tracker.get_order(order_id)
        if order is None or order.get("status") != "paid":
            return None

        token = self.generate_download_token(order_id)
        download_url = f"/downloads/{token}/{order['product_id']}.zip"
        self.tracker.update_order(order_id, {
            "download_token": token,
            "download_url": download_url,
            "downloads_generated_at": datetime.utcnow().isoformat(),
        })
        return download_url

    def verify_download_token(self, token: str, order_id: str) -> bool:
        order = self.tracker.get_order(order_id)
        if order is None:
            return False
        return order.get("download_token") == token

    def get_product_path(self, product_id: str) -> Optional[Path]:
        for ext in (".zip", ".png", ".pdf"):
            candidate = self.downloads_dir / f"{product_id}{ext}"
            if candidate.exists():
                return candidate
        return None


class PaymentManager:
    """Handles PayPal integration and email confirmations."""

    def __init__(self):
        config = _load_config()
        paypal_cfg = config["platforms"]["paypal"]
        owner_cfg = config["owner"]
        pricing_cfg = config["generation"]["pricing"]

        self.business_email: str = paypal_cfg["business_email"]
        self.currency: str = paypal_cfg.get("currency", "USD")
        self.owner_email: str = owner_cfg["email"]
        self.owner_name: str = owner_cfg["name"]
        self.pricing: dict = pricing_cfg
        self.sandbox: bool = paypal_cfg.get("sandbox", True)

        self.tracker = OrderTracker()
        self.delivery = DeliveryManager(self.tracker)

        self.gmail_user = os.environ.get("SENDER_EMAIL", "")
        self.gmail_password = os.environ.get("GMAIL_APP_PASSWORD", "")

    def generate_payment_link(
        self,
        product_id: str,
        price: float,
        description: str,
        buyer_email: Optional[str] = None,
    ) -> str:
        order = self.tracker.create_order(
            product_id=product_id,
            buyer_email=buyer_email or "",
            buyer_name="",
        )
        order_id = order["order_id"]

        custom = f"order_id:{order_id}"

        params = {
            "cmd": "_xclick",
            "business": self.business_email,
            "item_name": description,
            "item_number": product_id,
            "amount": f"{price:.2f}",
            "currency_code": self.currency,
            "custom": custom,
            "no_shipping": "1",
            "return": f"{self._site_url()}/thank-you?order_id={order_id}",
            "cancel_return": f"{self._site_url()}/cancel?order_id={order_id}",
            "notify_url": f"{self._site_url()}/api/paypal/ipn",
            "bn": "ClipForgeAI",
        }

        base_url = PAYPAL_LIVE_URL if not self.sandbox else PAYPAL_SANDBOX_URL
        return f"{base_url}?{urlencode(params)}"

    def create_order(
        self,
        product_id: str,
        buyer_email: str,
        buyer_name: str,
    ) -> dict:
        price = self.pricing.get(product_id, 2.99)
        order_id = f"CF-{uuid.uuid4().hex[:8].upper()}"

        order = {
            "order_id": order_id,
            "product_id": product_id,
            "price": price,
            "currency": self.currency,
            "buyer_email": buyer_email,
            "buyer_name": buyer_name,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "paypal_order_id": None,
            "download_token": None,
            "download_url": None,
            "email_sent": False,
        }

        self.tracker.add_order(order)
        return order

    def send_confirmation_email(self, order: dict) -> bool:
        if not self.gmail_user or not self.gmail_password:
            return False

        download_token = self.delivery.generate_download_token(order["order_id"])
        download_link = f"{self._site_url()}/download/{order['order_id']}/{download_token}"

        subject = f"Your ClipForge AI Purchase - {order['product_id']}"

        body = f"""Hi {order.get('buyer_name', 'there')},

Thank you for your purchase from ClipForge AI!

Order ID: {order['order_id']}
Product: {order['product_id']}
Amount: ${order['price']:.2f} {order['currency']}
Date: {datetime.utcnow().strftime('%B %d, %Y')}

Your download is ready:
{download_link}

This link is valid for 7 days and allows up to 5 downloads.

If you have any issues, reply to this email.

Best regards,
{self.owner_name}
ClipForge AI
{self.owner_email}
"""

        msg = MIMEMultipart()
        msg["From"] = self.gmail_user
        msg["To"] = order["buyer_email"]
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(self.gmail_user, self.gmail_password)
                server.send_message(msg)
            self.tracker.update_order(order["order_id"], {
                "email_sent": True,
                "email_sent_at": datetime.utcnow().isoformat(),
            })
            return True
        except smtplib.SMTPAuthenticationError:
            return False
        except smtplib.SMTPException:
            return False

    def generate_download_url(self, order_id: str) -> Optional[str]:
        return self.delivery.generate_download_url(order_id)

    def verify_payment(self, order_id: str) -> bool:
        order = self.tracker.get_order(order_id)
        if order is None:
            return False
        return order.get("status") == "paid"

    def handle_paypal_notification(self, ipn_data: dict) -> bool:
        if not self._validate_ipn(ipn_data):
            return False

        custom = ipn_data.get("custom", "")
        if not custom.startswith("order_id:"):
            return False
        order_id = custom.split(":", 1)[1]

        payment_status = ipn_data.get("payment_status", "")
        if payment_status == "Completed":
            self.tracker.update_order(order_id, {
                "status": "paid",
                "paypal_order_id": ipn_data.get("txn_id"),
                "paid_at": datetime.utcnow().isoformat(),
            })
            order = self.tracker.get_order(order_id)
            if order:
                self.send_confirmation_email(order)
            return True
        elif payment_status in ("Refunded", "Reversed"):
            self.tracker.update_order(order_id, {
                "status": "refunded",
                "refunded_at": datetime.utcnow().isoformat(),
            })
            return True

        return False

    def get_paypal_smart_buttons(
        self,
        product_id: str,
        price: float,
        description: str,
        order_id: str,
        client_id: Optional[str] = None,
    ) -> str:
        client_id = client_id or os.environ.get("PAYPAL_CLIENT_ID", "sb")
        return PAYPAL_SMART_BUTTONS_JS.format(
            client_id=client_id,
            currency=self.currency,
            description=description,
            price=f"{price:.2f}",
            order_id=order_id,
        )

    def _site_url(self) -> str:
        config = _load_config()
        pages = config["platforms"]["cloudflare_pages"]
        domain = pages.get("custom_domain")
        if domain:
            return f"https://{domain}"
        site_name = pages.get("site_name", "clipforge-ai")
        return f"https://{site_name}.pages.dev"

    def _validate_ipn(self, ipn_data: dict) -> bool:
        raw = b"cmd=_notify-validate&" + urlencode(ipn_data).encode()
        try:
            if self.sandbox:
                url = "https://www.sandbox.paypal.com/cgi-bin/webscr"
            else:
                url = "https://www.paypal.com/cgi-bin/webscr"
            import urllib.request
            req = urllib.request.Request(url, data=raw)
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode() == "VERIFIED"
        except Exception:
            return False
