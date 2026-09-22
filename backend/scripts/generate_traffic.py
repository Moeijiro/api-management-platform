"""Send real traffic to a running instance, for demos and screenshots.

This does not insert rows into the database: it signs in, creates an API key
and actually calls the public API, so everything the dashboard then shows is a
genuine request that went through the middleware.

    python scripts/generate_traffic.py --requests 120

Options let you include failures and rate-limited calls, because a dashboard
that only ever shows 200s is not much of a demo.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import urllib.error
import urllib.request
from http.cookiejar import CookieJar

DEFAULT_BASE = "http://localhost:8000"


class Client:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(CookieJar())
        )

    def call(self, path: str, data: dict | None = None, headers: dict | None = None):
        body = json.dumps(data).encode() if data is not None else None
        request = urllib.request.Request(
            f"{self.base}{path}",
            data=body,
            headers={"Content-Type": "application/json", **(headers or {})},
        )
        try:
            with self.opener.open(request) as response:
                raw = response.read()
                return response.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as error:
            return error.code, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--email", default="demo@example.com")
    parser.add_argument("--password", default="demo-password-1234")
    parser.add_argument("--requests", type=int, default=120)
    parser.add_argument("--key-name", default="Demo traffic")
    parser.add_argument(
        "--burst",
        type=int,
        default=8,
        help="Extra calls through a 3/min key, to produce genuine 429s.",
    )
    args = parser.parse_args()

    client = Client(args.base)
    status, _ = client.call(
        "/auth/register", {"email": args.email, "password": args.password}
    )
    if status not in (201, 409):
        print(f"Could not register ({status}); is the API running on {args.base}?")
        return 1
    if status == 409:
        client.call("/auth/login", {"email": args.email, "password": args.password})

    # The key's own quota is raised above the run size: the point of this
    # script is a populated dashboard, not a wall of 429s. Rate limiting gets
    # its own small key below.
    status, created = client.call(
        "/api/keys",
        {"name": args.key_name, "rate_limit_per_minute": max(args.requests * 2, 120)},
    )
    if status != 201 or not created:
        print(f"Could not create an API key ({status}).")
        return 1

    key = created["key"]
    headers = {"X-API-Key": key}
    counts: dict[int, int] = {}

    for index in range(args.requests):
        roll = random.random()
        if roll < 0.55:
            code, _ = client.call("/v1/status", headers=headers)
        elif roll < 0.75:
            code, _ = client.call("/v1/profile", headers=headers)
        elif roll < 0.9:
            code, _ = client.call(
                "/v1/process",
                {"text": random.choice(["hello world", "api platform", "rate limits"]),
                 "operation": random.choice(["upper", "reverse", "word_count"])},
                headers=headers,
            )
        elif roll < 0.96:
            code, _ = client.call("/v1/random?minimum=1&maximum=100", headers=headers)
        else:
            # A deliberate 400, so the dashboard shows a realistic error rate.
            code, _ = client.call("/v1/random?minimum=10&maximum=1", headers=headers)
        counts[code] = counts.get(code, 0) + 1

    if args.burst:
        status, throttled = client.call(
            "/api/keys", {"name": "Burst test", "rate_limit_per_minute": 3}
        )
        if status == 201 and throttled:
            burst_headers = {"X-API-Key": throttled["key"]}
            for _ in range(args.burst):
                code, _ = client.call("/v1/status", headers=burst_headers)
                counts[code] = counts.get(code, 0) + 1

    print(f"Sent {args.requests + args.burst} requests with key {created['prefix']}…")
    for code in sorted(counts):
        print(f"  {code}: {counts[code]}")
    print("\nThe raw key is shown once by the API; this run used:")
    print(f"  {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
