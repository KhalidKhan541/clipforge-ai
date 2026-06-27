# ClipForge AI

**Automated clip art business with zero upfront cost.**

ClipForge AI generates trending clip art using free AI APIs, automatically optimizes images for web, and can integrate with PayPal for instant digital delivery. Run it daily with a single command and build a passive income stream.

---

## Quick Start

```bash
# Clone or download the project
cd clip-art-bot

# One-command setup
python setup.py

# Activate virtual environment
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# Run the bot
python main.py
```

## How It Works

1. **Trend Research** — Scrapes trending topics, holidays, and niche keywords
2. **Image Generation** — Uses Groq API (free tier: 30 req/min) to generate clip art prompts, then renders images via free image APIs or local generation
3. **Optimization** — Resizes and compresses images for web use (PNG/SVG)
4. **Delivery** — Sends completed clip art via email or integrates with PayPal for instant digital download
5. **Scheduling** — Runs daily on a cron job or manual trigger

## Setup Instructions

### Prerequisites

- Python 3.9+
- A Gmail account (for SMTP)
- A Groq API key (free)
- Optional: PayPal developer account

### API Keys

| Service | Purpose | Cost | Get Key |
|---------|---------|------|---------|
| Groq | AI text generation | Free (30 req/min) | [console.groq.com](https://console.groq.com/keys) |
| Gmail SMTP | Email delivery | Free | [App Passwords](https://myaccount.google.com/apppasswords) |
| PayPal | Payment processing | Free | [developer.paypal.com](https://developer.paypal.com) |

### Configuration

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Or run `python setup.py` for guided configuration.

## Revenue Projections

| Tier | Monthly Downloads | Price/Download | Monthly Revenue |
|------|-------------------|----------------|-----------------|
| Starter | 50 | $2 | $100 |
| Growth | 200 | $3 | $600 |
| Scaled | 1,000+ | $5 | $2,000+ |

**Break-even: Day 1** (all tools are free)

## Project Structure

```
clip-art-bot/
├── .env                  # API keys (gitignored)
├── .env.example          # Template for .env
├── setup.py              # One-command setup
├── main.py               # Entry point
├── generators/           # Image generation modules
├── optimizers/           # Image processing
├── emailer/              # Email delivery
├── output/               # Generated images
│   ├── originals/        # High-res originals
│   └── optimized/        # Web-ready versions
└── logs/                 # Activity logs
```

## Tech Stack

- **Python 3.9+**
- **Groq API** — Fast, free LLM inference
- **Pillow** — Image processing
- **Jinja2** — Email templates
- **schedule** — Task scheduling
- **python-dotenv** — Environment management

## License

MIT — use freely, modify freely, profit freely.

---

Built for side-hustlers who want passive income without upfront costs.
