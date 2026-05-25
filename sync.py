#!/usr/bin/env python3
"""
Sage sync script.

Run this from your Sage files folder. It pushes:
  - Sage.md
  - Sage_Processes.md
  - Sage_Appendix_A_Capital_Engineering.md
  - Sage_Appendix_B_Working_Notes.md
  - Sage_README.md
  - Sage_Reentry_Prompt.md
to your Supabase backend so the phone app has the latest.

It also parses Sage_Processes.md and pushes the routing map.

Usage:
  python3 sync.py

First-time setup:
  1. pip install supabase python-dotenv
  2. Create a .env file in the same folder with:
       SUPABASE_URL=your-url
       SUPABASE_KEY=your-anon-key
       SAGE_EMAIL=you@example.com
       SAGE_PASSWORD=any-password-you-choose
  3. Sign in once via the web app with that email/password,
     or sign in with the magic link and the password you set.
"""

import os
import sys
import json
from pathlib import Path

try:
    from supabase import create_client
    from dotenv import load_dotenv
except ImportError:
    print("Missing packages. Run: pip install supabase python-dotenv")
    sys.exit(1)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SAGE_EMAIL = os.getenv("SAGE_EMAIL")
SAGE_PASSWORD = os.getenv("SAGE_PASSWORD")

if not all([SUPABASE_URL, SUPABASE_KEY, SAGE_EMAIL, SAGE_PASSWORD]):
    print("Missing config. Check .env file.")
    sys.exit(1)

FILES_TO_SYNC = [
    "Sage.md",
    "Sage_Processes.md",
    "Sage_Appendix_A_Capital_Engineering.md",
    "Sage_Appendix_B_Working_Notes.md",
    "Sage_README.md",
    "Sage_Reentry_Prompt.md",
]


def sign_in(client):
    """Sign in. If user does not exist yet, sign up."""
    try:
        res = client.auth.sign_in_with_password({
            "email": SAGE_EMAIL,
            "password": SAGE_PASSWORD,
        })
        return res.user
    except Exception:
        # Try signup
        try:
            res = client.auth.sign_up({
                "email": SAGE_EMAIL,
                "password": SAGE_PASSWORD,
            })
            return res.user
        except Exception as e:
            print(f"Sign in failed: {e}")
            sys.exit(1)


def sync_files(client, user_id, folder):
    folder = Path(folder)
    synced = []
    for filename in FILES_TO_SYNC:
        path = folder / filename
        if not path.exists():
            print(f"  skipped {filename} (not found)")
            continue
        content = path.read_text()
        client.table("sage_files").upsert({
            "user_id": user_id,
            "filename": filename,
            "content": content,
        }, on_conflict="user_id,filename").execute()
        synced.append(filename)
        print(f"  synced {filename}")
    return synced


def parse_routing_from_processes(content):
    """Best-effort: extract the routing map from Sage_Processes.md.
    Looks for sections like '### 1. The Work' and the table rows under it."""
    # For now, we keep this simple: the routing in the app's FALLBACK_ROUTING
    # is the source of truth until you want to override it from the file.
    # When you're ready to make the file truly the source, expand this.
    return None


def sync_routing(client, user_id, folder):
    processes_path = Path(folder) / "Sage_Processes.md"
    if not processes_path.exists():
        return
    content = processes_path.read_text()
    routing = parse_routing_from_processes(content)
    if routing:
        client.table("sage_routing").upsert({
            "user_id": user_id,
            "data": routing,
        }, on_conflict="user_id").execute()
        print("  synced routing map")


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"Syncing from {folder}...")

    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    user = sign_in(client)
    print(f"Signed in as {user.email}")

    synced = sync_files(client, user.id, folder)
    sync_routing(client, user.id, folder)

    print(f"\nDone. {len(synced)} files synced.")


if __name__ == "__main__":
    main()
