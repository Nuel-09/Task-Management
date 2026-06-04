#!/usr/bin/env python3
"""Wait for deployed app health and home page (used by Jenkins smoke stage)."""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request


def wait_for_status(url: str, timeout_seconds: int, interval_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                if response.status == 200:
                    return
                last_error = RuntimeError(f"unexpected status {response.status}")
        except Exception as exc:  # noqa: BLE001 - retry until timeout
            last_error = exc
        time.sleep(interval_seconds)

    raise SystemExit(f"Timed out waiting for {url}. Last error: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test deployed todo app.")
    parser.add_argument("port", help="Host port mapped by docker compose (e.g. 8000)")
    parser.add_argument("--timeout", type=int, default=120, help="Max seconds to wait")
    parser.add_argument("--interval", type=int, default=3, help="Seconds between retries")
    args = parser.parse_args()

    base = f"http://localhost:{args.port}"
    wait_for_status(f"{base}/health", args.timeout, args.interval)
    wait_for_status(f"{base}/", args.timeout, args.interval)
    print(f"smoke ok for {args.port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
