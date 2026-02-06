#!/usr/bin/env python3
import argparse
import json
import os
import shlex
import sys
from urllib.parse import urlparse, parse_qs

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from xhs_utils.common_util import load_env
    from xhs_utils.xhs_util import generate_request_params
except ModuleNotFoundError as exc:
    print("Missing Python deps. Run: pip install -r requirements.txt", file=sys.stderr)
    raise


API_PATH = "/api/sns/web/v1/feed"
API_URL = f"https://edith.xiaohongshu.com{API_PATH}"


def parse_note_url(note_url: str):
    parsed = urlparse(note_url)
    note_id = parsed.path.rstrip("/").split("/")[-1]
    qs = parse_qs(parsed.query)
    xsec_token = (qs.get("xsec_token") or [""])[0]
    xsec_source = (qs.get("xsec_source") or ["pc_search"])[0]
    return note_id, xsec_token, xsec_source


def build_payload(note_id: str, xsec_token: str, xsec_source: str):
    return {
        "source_note_id": note_id,
        "image_formats": ["jpg", "webp", "avif"],
        "extra": {"need_body_topic": "1"},
        "xsec_source": xsec_source or "pc_search",
        "xsec_token": xsec_token,
    }


def to_curl(headers: dict, data_str: str, cookies_str: str):
    lines = [f"curl {shlex.quote(API_URL)} \\"]
    for key, value in headers.items():
        lines.append(f"  -H {shlex.quote(f'{key}: {value}')} \\")
    lines.append(f"  -H {shlex.quote(f'cookie: {cookies_str}')} \\")
    lines.append(f"  --data-raw {shlex.quote(data_str)}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate curl for XHS note detail API.")
    parser.add_argument("--note-url", help="Full note URL with xsec_token")
    parser.add_argument("--note-id", help="Note ID (if not using --note-url)")
    parser.add_argument("--xsec-token", help="xsec_token (if not using --note-url)")
    parser.add_argument("--xsec-source", default="pc_search", help="xsec_source (default: pc_search)")
    parser.add_argument("--cookies", help="Cookie string (defaults to .env COOKIES)")
    args = parser.parse_args()

    if args.note_url:
        note_id, xsec_token, xsec_source = parse_note_url(args.note_url)
    else:
        if not args.note_id or not args.xsec_token:
            print("Error: provide --note-url or both --note-id and --xsec-token.", file=sys.stderr)
            return 2
        note_id = args.note_id
        xsec_token = args.xsec_token
        xsec_source = args.xsec_source

    cookies_str = args.cookies or load_env()
    if not cookies_str:
        print("Error: COOKIES not found. Set .env COOKIES or pass --cookies.", file=sys.stderr)
        return 2

    payload = build_payload(note_id, xsec_token, xsec_source)
    headers, _, data = generate_request_params(cookies_str, API_PATH, payload, "POST")
    data_str = data if isinstance(data, str) else json.dumps(data, separators=(",", ":"), ensure_ascii=False)

    print(to_curl(headers, data_str, cookies_str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
