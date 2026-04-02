#!/usr/bin/env python3
"""
Manifest Migration Tool
========================
Migrates your existing local .pipeline_manifest.json to Dropbox so the
containerized pipeline picks up where your local pipeline left off.

This converts the local file-hash based tracking to Dropbox content-hash
tracking. Files that have already been processed locally will be looked up
in Dropbox, and their Dropbox content hashes will be recorded so the
containerized pipeline skips them.

Usage:
    python migrate_manifest.py

Requires the same Dropbox credentials as the pipeline.
Set DROPBOX_REFRESH_TOKEN, DROPBOX_APP_KEY, DROPBOX_APP_SECRET as env vars,
or DROPBOX_ACCESS_TOKEN for quick testing.
"""

import json
import os
import sys

try:
    import dropbox
    from dropbox.exceptions import ApiError
    from dropbox.files import WriteMode
except ImportError:
    print("Missing dependency: pip install dropbox")
    sys.exit(1)

# Adjust these paths as needed
LOCAL_MANIFEST = os.path.expanduser(
    "~/Library/CloudStorage/Dropbox-Personal/AI_logs/scripts/.pipeline_manifest.json"
)
DROPBOX_MANIFEST_PATH = "/AI_logs/scripts/.pipeline_manifest.json"
SOURCE_ROOT = "/AI_logs"


def init_dropbox() -> dropbox.Dropbox:
    refresh_token = os.environ.get("DROPBOX_REFRESH_TOKEN")
    app_key = os.environ.get("DROPBOX_APP_KEY")
    app_secret = os.environ.get("DROPBOX_APP_SECRET")
    access_token = os.environ.get("DROPBOX_ACCESS_TOKEN")

    if refresh_token and app_key and app_secret:
        return dropbox.Dropbox(
            oauth2_refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret,
        )
    elif access_token:
        return dropbox.Dropbox(access_token)
    else:
        print("Set DROPBOX_REFRESH_TOKEN + APP_KEY + APP_SECRET, or DROPBOX_ACCESS_TOKEN")
        sys.exit(1)


def get_dropbox_content_hash(dbx: dropbox.Dropbox, path: str) -> str | None:
    """Look up a file's content hash in Dropbox."""
    try:
        meta = dbx.files_get_metadata(path)
        if isinstance(meta, dropbox.files.FileMetadata):
            return meta.content_hash
    except ApiError:
        pass
    return None


def main():
    if not os.path.exists(LOCAL_MANIFEST):
        print(f"Local manifest not found: {LOCAL_MANIFEST}")
        print("Nothing to migrate.")
        sys.exit(0)

    with open(LOCAL_MANIFEST) as f:
        local = json.load(f)

    processed = local.get("processed", {})
    print(f"Found {len(processed)} entries in local manifest")

    dbx = init_dropbox()
    account = dbx.users_get_current_account()
    print(f"Connected to Dropbox as: {account.name.display_name}")

    migrated = {}
    skipped = 0
    found = 0

    for key, info in processed.items():
        # key is like "ChatGPT/20260401_Some_Title_abc123.md"
        source_path = f"{SOURCE_ROOT}/{key}"

        content_hash = get_dropbox_content_hash(dbx, source_path)
        if content_hash:
            migrated[key] = {
                "hash": content_hash,
                "output": info.get("output", "").replace(
                    "/Users/asif/Library/CloudStorage/Dropbox-Personal/",
                    "/"
                ) if info.get("output") else None,
                "processed_at": info.get("processed_at", ""),
                "skipped": info.get("skipped", False),
            }
            found += 1
        else:
            # File doesn't exist in Dropbox (maybe deleted); carry forward anyway
            migrated[key] = {
                "hash": info.get("hash", ""),
                "output": None,
                "processed_at": info.get("processed_at", ""),
                "skipped": True,
            }
            skipped += 1

        if (found + skipped) % 50 == 0:
            print(f"  Progress: {found} found, {skipped} missing ({found + skipped}/{len(processed)})")

    new_manifest = {
        "processed": migrated,
        "last_run": local.get("last_run"),
        "migrated_from_local": True,
        "migration_date": __import__("datetime").datetime.now().isoformat(),
    }

    # Upload to Dropbox
    content = json.dumps(new_manifest, indent=2)
    dbx.files_upload(
        content.encode("utf-8"),
        DROPBOX_MANIFEST_PATH,
        mode=WriteMode.overwrite,
        mute=True,
    )

    print()
    print(f"Migration complete:")
    print(f"  {found} files matched in Dropbox (will be skipped by pipeline)")
    print(f"  {skipped} files not found in Dropbox (marked as skipped)")
    print(f"  Manifest uploaded to: {DROPBOX_MANIFEST_PATH}")
    print()


if __name__ == "__main__":
    main()
