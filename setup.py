#!/usr/bin/env python3
"""
ClipForge AI - One-Command Setup Script
Interactive setup for the automated clip art business bot.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path
from typing import Optional

# ─── Constants ───────────────────────────────────────────────────────────────
REQUIRED_PYTHON = (3, 9)
PROJECT_DIR = Path(__file__).parent
VENV_DIR = PROJECT_DIR / "venv"
ENV_FILE = PROJECT_DIR / ".env"
ENV_EXAMPLE = PROJECT_DIR / ".env.example"
DIRS_TO_CREATE = ["output", "output/optimized", "output/originals", "logs"]


# ─── Helpers ─────────────────────────────────────────────────────────────────
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_banner():
    print(f"""
{Colors.CYAN}{Colors.BOLD}
  ╔══════════════════════════════════════════════════╗
  ║         ClipForge AI - Setup Wizard             ║
  ║         Automated Clip Art Business             ║
  ╚══════════════════════════════════════════════════╝
{Colors.END}""")


def print_step(step: int, total: int, message: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}[{step}/{total}]{Colors.END} {Colors.BOLD}{message}{Colors.END}")


def print_success(message: str):
    print(f"  {Colors.GREEN}✓{Colors.END} {message}")


def print_warning(message: str):
    print(f"  {Colors.YELLOW}⚠{Colors.END} {message}")


def print_error(message: str):
    print(f"  {Colors.RED}✗{Colors.END} {message}")


def print_info(message: str):
    print(f"  {Colors.CYAN}→{Colors.END} {message}")


def prompt_input(message: str, default: str = "") -> str:
    if default:
        user_input = input(f"  {Colors.YELLOW}?{Colors.END} {message} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"  {Colors.YELLOW}?{Colors.END} {message}: ").strip()


def prompt_yes_no(message: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    response = input(f"  {Colors.YELLOW}?{Colors.END} {message} [{hint}]: ").strip().lower()
    if not response:
        return default
    return response in ("y", "yes")


# ─── Step Functions ──────────────────────────────────────────────────────────
def check_python_version() -> bool:
    print_step(1, 7, "Checking Python version...")
    major, minor = sys.version_info[:2]
    if (major, minor) >= REQUIRED_PYTHON:
        print_success(f"Python {major}.{minor}.{sys.version_info[2]} detected")
        return True
    else:
        print_error(f"Python {major}.{minor} detected, but {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ is required")
        print_info("Download Python from https://www.python.org/downloads/")
        return False


def create_virtual_environment() -> bool:
    print_step(2, 7, "Creating virtual environment...")
    if VENV_DIR.exists():
        print_warning("Virtual environment already exists")
        if not prompt_yes_no("Recreate it?", default=False):
            print_info("Keeping existing venv")
            return True
        import shutil
        shutil.rmtree(VENV_DIR)

    try:
        venv.create(VENV_DIR, with_pip=True)
        print_success("Virtual environment created")
        return True
    except Exception as e:
        print_error(f"Failed to create venv: {e}")
        return False


def install_dependencies() -> bool:
    print_step(3, 7, "Installing dependencies...")

    # Determine pip path
    if sys.platform == "win32":
        pip_path = VENV_DIR / "Scripts" / "pip.exe"
        python_path = VENV_DIR / "Scripts" / "python.exe"
    else:
        pip_path = VENV_DIR / "bin" / "pip"
        python_path = VENV_DIR / "bin" / "python"

    requirements = [
        "groq>=0.4.0",
        "Pillow>=10.0.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "schedule>=1.2.0",
        "jinja2>=3.1.0",
    ]

    # Upgrade pip first
    print_info("Upgrading pip...")
    subprocess.run(
        [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
        capture_output=True,
    )

    # Install requirements
    print_info("Installing packages...")
    for package in requirements:
        print_info(f"Installing {package}...")
        result = subprocess.run(
            [str(pip_path), "install", package],
            capture_output=True,
        )
        if result.returncode != 0:
            print_error(f"Failed to install {package}")
            return False

    print_success("All dependencies installed")
    return True


def create_directories() -> bool:
    print_step(4, 7, "Creating project directories...")
    for dir_name in DIRS_TO_CREATE:
        dir_path = PROJECT_DIR / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print_success(f"Created {dir_name}/")
    return True


def create_env_file() -> bool:
    print_step(5, 7, "Configuring environment variables...")

    if ENV_FILE.exists():
        print_warning(".env file already exists")
        if not prompt_yes_no("Overwrite it?", default=False):
            print_info("Keeping existing .env file")
            return True

    print_info("Please enter your API keys (you can skip for now and edit .env later)\n")

    groq_key = prompt_input("Groq API key", default="your_groq_api_key_here")
    gmail_password = prompt_input("Gmail app password", default="your_gmail_app_password_here")
    sender_email = prompt_input("Sender email address", default="your_email@gmail.com")
    paypal_client_id = prompt_input("PayPal client ID", default="your_paypal_client_id_here")

    env_content = f"""# Groq API (free) - Get key at https://console.groq.com/keys
GROQ_API_KEY={groq_key}

# Gmail SMTP (free) - Generate app password in Google Account settings
GMAIL_APP_PASSWORD={gmail_password}
SENDER_EMAIL={sender_email}

# PayPal (free) - Get client ID at https://developer.paypal.com
PAYPAL_CLIENT_ID={paypal_client_id}
"""

    ENV_FILE.write_text(env_content)
    print_success("Environment file created")
    return True


def test_groq_connection() -> bool:
    print_step(6, 7, "Testing Groq API connection...")

    # Load env
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)

    api_key = os.getenv("GROQ_API_KEY", "")
    if api_key == "your_groq_api_key_here" or not api_key:
        print_warning("Skipping - no API key configured")
        print_info("Edit .env and run 'python test_connections.py' to test later")
        return True

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'Connection successful' in 3 words or less."}],
            max_tokens=10,
        )
        print_success(f"Groq API: {response.choices[0].message.content.strip()}")
        return True
    except Exception as e:
        print_warning(f"Groq API test failed: {e}")
        print_info("Check your API key in .env")
        return True  # Non-fatal


def test_gmail_connection() -> bool:
    print_step(7, 7, "Testing Gmail SMTP connection...")

    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)

    password = os.getenv("GMAIL_APP_PASSWORD", "")
    email = os.getenv("SENDER_EMAIL", "")

    if password == "your_gmail_app_password_here" or not password:
        print_warning("Skipping - no credentials configured")
        print_info("Edit .env and run 'python test_connections.py' to test later")
        return True

    import smtplib
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
        server.login(email, password)
        server.quit()
        print_success(f"Gmail SMTP: Connected as {email}")
        return True
    except smtplib.SMTPAuthenticationError:
        print_warning("Gmail authentication failed")
        print_info("Make sure you're using an App Password (not your regular password)")
        print_info("Generate one at: https://myaccount.google.com/apppasswords")
        return True  # Non-fatal
    except Exception as e:
        print_warning(f"Gmail SMTP test failed: {e}")
        print_info("Check your credentials in .env")
        return True  # Non-fatal


def print_summary():
    print(f"""
{Colors.GREEN}{Colors.BOLD}
  ╔══════════════════════════════════════════════════╗
  ║           Setup Complete! 🎨                     ║
  ╚══════════════════════════════════════════════════╝
{Colors.END}

  {Colors.BOLD}Project Structure:{Colors.END}
  clip-art-bot/
  ├── .env              ← API keys (edit this)
  ├── output/           ← Generated clip art
  ├── output/optimized/ ← Web-optimized images
  ├── output/originals/ ← High-res originals
  ├── logs/             ← Activity logs
  └── venv/             ← Virtual environment

  {Colors.BOLD}Next Steps:{Colors.END}

  1. {Colors.CYAN}Activate virtual environment:{Colors.END}
     venv\\Scripts\\activate     (Windows)
     source venv/bin/activate   (Mac/Linux)

  2. {Colors.CYAN}Edit .env with your API keys:{Colors.END}
     Get Groq key:  https://console.groq.com/keys
     Get Gmail app password: https://myaccount.google.com/apppasswords
     Get PayPal ID: https://developer.paypal.com

  3. {Colors.CYAN}Test connections:{Colors.END}
     python test_connections.py

  4. {Colors.CYAN}Run the bot:{Colors.END}
     python main.py

  {Colors.BOLD}Cost: $0 upfront (all free APIs){Colors.END}
  {Colors.BOLD}Revenue: $200-2,000/month potential{Colors.END}
""")


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    print_banner()

    steps = [
        check_python_version,
        create_virtual_environment,
        install_dependencies,
        create_directories,
        create_env_file,
        test_groq_connection,
        test_gmail_connection,
    ]

    for step in steps:
        if not step():
            print_error("\nSetup failed. Fix the issue above and try again.")
            sys.exit(1)

    print_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user.{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        sys.exit(1)
