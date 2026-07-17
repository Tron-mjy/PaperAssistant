"""
Test OpenAI API connectivity.
Usage: python test_api.py

Checks:
  1. Can establish network connection to OPENAI_BASE_URL
  2. Can authenticate with OPENAI_API_KEY
  3. Can call the chat completions API and get a response
"""
import os
import sys
import time
from pathlib import Path

# Load .env from project root
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / '.env')

API_KEY = os.getenv('OPENAI_API_KEY', '')
BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')

SEPARATOR = '-' * 55


def check_config():
    """Print current configuration."""
    print(SEPARATOR)
    print("  PaperAssistant - OpenAI API Connectivity Test")
    print(SEPARATOR)
    print(f"  BASE_URL    = {BASE_URL}")
    print(f"  MODEL       = {MODEL}")
    if API_KEY:
        masked = API_KEY[:10] + '...' + API_KEY[-4:] if len(API_KEY) > 16 else '***'
        print(f"  API_KEY     = {masked}")
    else:
        print(f"  API_KEY     = (NOT SET)")
    print(SEPARATOR)
    print()


def step(number: int, desc: str):
    """Print a step header."""
    print(f"[Step {number}] {desc}")
    print()


def result(success: bool, msg: str = ''):
    """Print a pass/fail result."""
    if success:
        print(f"  [Result] PASS - {msg}")
    else:
        print(f"  [Result] FAIL - {msg}")
    print()


def test_import():
    """Test that openai package is installed."""
    step(1, "Check openai package installation")
    try:
        import openai
        print(f"  openai version: {openai.__version__}")
        result(True, "Package is installed")
        return True
    except ImportError as e:
        result(False, f"openai package not installed: {e}")
        print(f"  Fix: pip install openai")
        return False


def test_connection():
    """Test basic network connectivity to the API host."""
    step(2, "Test network connection to API server")
    from urllib.parse import urlparse
    import socket

    host = urlparse(BASE_URL).hostname
    port = urlparse(BASE_URL).port or 443

    print(f"  Target: {host}:{port}")
    try:
        sock = socket.create_connection((host, port), timeout=10)
        sock.close()
        result(True, f"TCP connection to {host}:{port} succeeded")
        return True
    except socket.gaierror as e:
        result(False, f"DNS lookup failed: {e}")
        print(f"  HINT: Check OPENAI_BASE_URL is correct in .env")
        print(f"  HINT: Check your DNS / network settings")
        return False
    except socket.timeout:
        result(False, "Connection timed out")
        print(f"  HINT: Server may be unreachable or blocked by firewall")
        return False
    except ConnectionRefusedError:
        result(False, "Connection refused")
        print(f"  HINT: Server is not accepting connections on port {port}")
        return False
    except OSError as e:
        result(False, f"Network error: {e}")
        return False


def test_api_call():
    """Test a real API call."""
    step(3, "Test OpenAI API chat completion")

    if not API_KEY or API_KEY == 'your-api-key-here':
        result(False, "API_KEY is not set")
        print(f"  Fix: set OPENAI_API_KEY in .env file")
        return False

    from openai import OpenAI

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=30.0)

    print(f"  Sending test message to model: {MODEL}")
    print(f"  Request: 'Say hello in one sentence.'")

    start = time.time()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "Say hello in one sentence."}],
            max_tokens=50,
            temperature=0,
        )
        elapsed = time.time() - start
        content = response.choices[0].message.content.strip()
        tokens = response.usage.total_tokens if response.usage else '?'
        print(f"  Response ({elapsed:.1f}s, {tokens} tokens): {content}")
        result(True, "API call succeeded")
        return True
    except Exception as e:
        elapsed = time.time() - start
        print(f"  Elapsed: {elapsed:.1f}s")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error message: {e}")
        print()
        # Give specific hints
        name = type(e).__name__
        if 'AuthenticationError' in name or '401' in str(e) or 'Unauthorized' in str(e):
            print(f"  HINT: Invalid API key. Check OPENAI_API_KEY in .env")
            print(f"  HINT: The API key format is typically 'sk-xxxx...'")
        elif 'PermissionDeniedError' in name or '403' in str(e) or 'blocked' in str(e).lower():
            print(f"  HINT: Request was blocked by the API server (403 / Permission Denied).")
            print(f"  HINT: Possible causes:")
            print(f"        1. API key has expired or been revoked")
            print(f"        2. Account balance is insufficient")
            print(f"        3. The API service has restricted your access")
            print(f"        4. The model '{MODEL}' is not available with your plan")
        elif 'ConnectionError' in name or 'Connection' in name:
            print(f"  HINT: Cannot reach the server. Check:")
            print(f"        1. OPENAI_BASE_URL = {BASE_URL}")
            print(f"        2. Network / VPN / proxy settings")
            print(f"        3. Firewall is not blocking outbound connections")
        elif 'Timeout' in name:
            print(f"  HINT: Request timed out. Server may be overloaded or unreachable.")
            print(f"  HINT: Try a different model or check network speed.")
        elif 'RateLimitError' in name or '429' in str(e):
            print(f"  HINT: Rate limited. Wait and try again or check your API quota.")
        elif 'NotFoundError' in name or '404' in str(e):
            print(f"  HINT: Model '{MODEL}' not found at this endpoint.")
            print(f"  HINT: Check the model name or try 'gpt-4o-mini'")
        else:
            print(f"  HINT: Unexpected error. Check BASE_URL, API_KEY, and MODEL in .env")
        print()
        result(False, f"{type(e).__name__}")
        return False


def main():
    check_config()

    results = []
    results.append(test_import())
    print()
    results.append(test_connection())
    print()
    results.append(test_api_call())
    print()

    print(SEPARATOR)
    passed = sum(results)
    total = len(results)
    if all(results):
        print(f"  ALL CHECKS PASSED ({passed}/{total})")
        print(f"  Your API configuration is working correctly.")
    else:
        failed_count = total - passed
        print(f"  {failed_count}/{total} CHECK(S) FAILED")
        print(f"  Review the hints above for troubleshooting.")
    print(SEPARATOR)


if __name__ == '__main__':
    main()
