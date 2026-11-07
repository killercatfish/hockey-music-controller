#!/usr/bin/env python3
"""Make a MusicKit developer token for the Phase 0 spike page.

    pip3 install pyjwt cryptography
    python3 docs/spike/make_musickit_token.py --key ~/Downloads/AuthKey_ABC123DEFG.p8 \
        --key-id ABC123DEFG --team-id XYZ987TEAM

Prints the token. Paste it into the spike page on the iPhone; the page keeps it
in that browser only. Never commit the .p8 key or the token (CLAUDE.md
invariant 7). The token is locked to the GitHub Pages origin and expires.
"""
import argparse
import time

DEFAULT_ORIGIN = "https://killercatfish.github.io"
MAX_LIFETIME = 15777000  # Apple's limit: about 6 months


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--key", required=True, help="path to the AuthKey_XXXX.p8 file")
    ap.add_argument("--key-id", required=True, help="10-char Key ID shown next to the key")
    ap.add_argument("--team-id", required=True, help="10-char Team ID (top right of the developer site)")
    ap.add_argument("--days", type=int, default=30, help="lifetime in days (default 30)")
    ap.add_argument("--origin", action="append",
                    help=f"allowed web origin (default {DEFAULT_ORIGIN}); repeatable")
    args = ap.parse_args()

    import jwt  # pyjwt; imported here so --help works without it

    with open(args.key) as fh:
        private_key = fh.read()
    now = int(time.time())
    claims = {
        "iss": args.team_id,
        "iat": now,
        "exp": now + min(args.days * 86400, MAX_LIFETIME),
        "origin": args.origin or [DEFAULT_ORIGIN],
    }
    print(jwt.encode(claims, private_key, algorithm="ES256", headers={"kid": args.key_id}))


if __name__ == "__main__":
    main()
