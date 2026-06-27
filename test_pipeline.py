import os
import smtplib
import requests
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout


def get_env(name):
    val = os.environ.get(name, "")
    if not val:
        print(f"  [SKIP] {name} not set")
    return val


def test_aihorde():
    api_key = get_env("AIHORDE_API_KEY")
    if not api_key:
        return False

    try:
        resp = requests.post(
            "https://stablehorde.net/api/v2/generate/async",
            headers={
                "apikey": api_key,
                "Content-Type": "application/json",
            },
            json={
                "prompt": "a test image, simple",
                "params": {
                    "width": 512,
                    "height": 512,
                    "steps": 1,
                    "cfg_scale": 7,
                    "sampler_name": "k_euler",
                },
                "nsfw": False,
                "models": ["stable_diffusion"],
            },
            timeout=30,
        )
        if resp.status_code in (200, 202):
            job_id = resp.json().get("id", "unknown")
            print(f"  OK - queued job {job_id}")
            return True
        print(f"  FAIL - HTTP {resp.status_code}: {resp.text[:200]}")
        return False
    except requests.Timeout:
        print("  FAIL - request timed out after 30s")
        return False
    except Exception as e:
        print(f"  FAIL - {e}")
        return False


def test_gumroad():
    token = get_env("GUMROAD_ACCESS_TOKEN")
    if not token:
        return False

    try:
        resp = requests.post(
            "https://api.gumroad.com/v2/user",
            data={"access_token": token},
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json().get("user", {})
            print(f"  OK - authenticated as {data.get('email', 'unknown')}")
            return True
        print(f"  FAIL - HTTP {resp.status_code}: {resp.text[:200]}")
        return False
    except requests.Timeout:
        print("  FAIL - request timed out after 30s")
        return False
    except Exception as e:
        print(f"  FAIL - {e}")
        return False


def test_gmail():
    app_password = get_env("GMAIL_APP_PASSWORD")
    sender = get_env("SENDER_EMAIL")
    if not app_password or not sender:
        return False

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(sender, app_password)
        print(f"  OK - logged in as {sender}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"  FAIL - auth rejected: {e}")
        return False
    except Exception as e:
        print(f"  FAIL - {e}")
        return False


def run_test(name, fn):
    print(f"\n[{name}]")
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(fn)
            return future.result(timeout=35)
    except FutureTimeout:
        print("  FAIL - test timed out")
        return False
    except Exception as e:
        print(f"  FAIL - {e}")
        return False


def main():
    print("=" * 40)
    print("  Clip-Art Bot - Connection Tests")
    print("=" * 40)

    results = {}
    for name, fn in [
        ("AI Horde", test_aihorde),
        ("Gumroad", test_gumroad),
        ("Gmail SMTP", test_gmail),
    ]:
        results[name] = run_test(name, fn)

    print("\n" + "=" * 40)
    print("  Results")
    print("=" * 40)
    all_pass = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_pass = False

    print("=" * 40)
    if all_pass:
        print("  All tests passed!")
    else:
        print("  Some tests failed - check above for details")
    print()


if __name__ == "__main__":
    main()
