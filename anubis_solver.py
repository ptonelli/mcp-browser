import json
import re
import hashlib
import urllib.request
import urllib.parse
from urllib.parse import urlparse
from http.cookiejar import CookieJar
from typing import Optional, Tuple

# Public API of this module
__all__ = (
    "is_anubis_page",
    "extract_challenge_from_html",
    "solve_anubis_pow",
    "solve_anubis_challenge_sync",
)

# Simple heuristic markers used by Anubis challenge pages
ANUBIS_MARKERS = ("Making sure you", "bot", "Anubis")


def is_anubis_page(html: str) -> bool:
    """Return True if the HTML looks like an Anubis challenge page."""
    if not html:
        return False
    return all(marker in html for marker in ANUBIS_MARKERS)



def solve_anubis_pow(challenge: str, difficulty: int = 4) -> Tuple[int, str]:
    """Solve Anubis proof-of-work challenge.

    Returns a tuple of (nonce, hash_hex) that satisfies the difficulty.
    """
    nonce = 0
    target_prefix = "0" * difficulty

    while True:
        hash_input = f"{challenge}{nonce}"
        hash_result = hashlib.sha256(hash_input.encode()).hexdigest()
        if hash_result.startswith(target_prefix):
            return nonce, hash_result
        nonce += 1


def extract_challenge_from_html(html: str) -> Tuple[Optional[str], Optional[int]]:
    """Extract challenge data from Anubis HTML.

    Returns (challenge, difficulty) if found, otherwise (None, None).
    """
    script_match = re.search(
        r'<script id="anubis_challenge" type="application/json">([^<]+)</script>',
        html,
    )
    if script_match:
        try:
            challenge_data = json.loads(script_match.group(1))
            challenge = challenge_data["challenge"]
            difficulty = challenge_data["rules"]["difficulty"]
            return challenge, difficulty
        except (json.JSONDecodeError, KeyError):
            pass
    return None, None


def solve_anubis_challenge_sync(
    url: str,
    *,
    user_agent: str,
    request_timeout: int,
) -> Optional[str]:
    """Bypass Anubis protection synchronously using urllib.

    Args:
        url: Target URL.
        user_agent: HTTP User-Agent header to use.
        request_timeout: Timeout in seconds for HTTP requests.

    Returns:
        HTML content after bypassing Anubis protection, or None if failed
        or if the page is not Anubis-protected.
    """
    try:
        # Create a cookie jar to handle cookies automatically
        cookie_jar = CookieJar()
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cookie_jar)
        )

        # First request to get the challenge
        req = urllib.request.Request(url, headers={"User-Agent": user_agent})
        with opener.open(req, timeout=request_timeout) as response:
            html = response.read().decode("utf-8", errors="replace")

            # Not an Anubis page
            if not is_anubis_page(html):
                return None

            challenge, difficulty = extract_challenge_from_html(html)

        if not challenge or not difficulty:
            return None

        # Solve the proof-of-work
        nonce, full_hash = solve_anubis_pow(challenge, difficulty)

        # Submit solution to get auth cookie
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        pass_challenge_url = (
            f"{base_url}/.within.website/x/cmd/anubis/api/pass-challenge"
        )
        params = {
            "response": full_hash,
            "nonce": str(nonce),
            "redir": parsed_url.path or "/",
            "elapsedTime": "100",
        }

        verification_url = f"{pass_challenge_url}?{urllib.parse.urlencode(params)}"
        verify_req = urllib.request.Request(
            verification_url, headers={"User-Agent": user_agent}
        )

        # Submit the solution and get the result
        with opener.open(verify_req, timeout=request_timeout) as verify_response:
            verify_content = verify_response.read().decode("utf-8", errors="replace")

            # If still getting Anubis, try original URL with cookies
            if is_anubis_page(verify_content):
                final_req = urllib.request.Request(
                    url, headers={"User-Agent": user_agent}
                )
                with opener.open(final_req, timeout=request_timeout) as final_response:
                    content = final_response.read().decode("utf-8", errors="replace")
                    if is_anubis_page(content):
                        return None
                    return content
            return verify_content

    except Exception:
        return None
