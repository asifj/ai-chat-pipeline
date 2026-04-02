#!/usr/bin/env python3
"""
AI Chat -> Obsidian Pipeline (Container/CI Edition)
====================================================
Pulls raw AI chat markdown exports from Dropbox, enriches them with YAML
frontmatter via Gemini, writes enriched files back to Dropbox, and builds
MOC/topic indexes for Obsidian.

Designed to run autonomously via GitHub Actions on a cron schedule.

Required environment variables:
    GEMINI_API_KEY          Google Gemini API key
    DROPBOX_ACCESS_TOKEN    Dropbox OAuth2 access token (long-lived or refreshed)
    DROPBOX_REFRESH_TOKEN   (optional) Dropbox refresh token for auto-renewal
    DROPBOX_APP_KEY         (optional) Dropbox app key for token refresh
    DROPBOX_APP_SECRET      (optional) Dropbox app secret for token refresh

Optional environment variables:
    SOURCE_ROOT             Dropbox path to raw AI chat exports (default: /AI_logs)
    OUTPUT_ROOT             Dropbox path for enriched Obsidian output (default: /Obsidian/AI_Chats)
    MAX_FILES               Max files to process per run (default: 50)
    FORCE_REPROCESS         Set to "true" to reprocess all files
    DRY_RUN                 Set to "true" to show what would be processed
"""

import hashlib
import json
import os
import re
import sys
import time
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

try:
    from google import genai
except ImportError:
    try:
        import google.generativeai as genai_legacy
    except ImportError:
        print("Missing dependency: pip install google-genai pyyaml")
        sys.exit(1)

import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------

SOURCE_ROOT = os.environ.get("SOURCE_ROOT", "/AI_logs")
OUTPUT_ROOT = os.environ.get("OUTPUT_ROOT", "/Obsidian/AI_Chats")
MAX_FILES = int(os.environ.get("MAX_FILES", "50"))
FORCE_REPROCESS = os.environ.get("FORCE_REPROCESS", "").lower() == "true"
DRY_RUN = os.environ.get("DRY_RUN", "").lower() == "true"

SOURCE_DIRS = {
    "ChatGPT": f"{SOURCE_ROOT}/ChatGPT",
    "Claude": f"{SOURCE_ROOT}/Claude",
    "Gemini": f"{SOURCE_ROOT}/Gemini",
}

MANIFEST_PATH = f"{SOURCE_ROOT}/scripts/.pipeline_manifest.json"

GEMINI_MODEL = "gemini-2.5-flash"
REQUESTS_PER_MINUTE = 14
REQUEST_DELAY = 60.0 / REQUESTS_PER_MINUTE
MAX_CONTENT_CHARS = 12000

TOPIC_CATEGORIES = [
    "MY LIFE",
    "GENERAL WORK",
    "MY FINANCIALS",
    "MY GRANTS",
    "MY RESEARCH",
    "HEALTH & MEDICAL",
    "CAR MAINTENANCE",
    "HOME & DIY",
    "COOKING & FOOD",
    "TECHNOLOGY & SOFTWARE",
    "CAREER & JOBS",
    "LEARNING & EDUCATION",
    "RELATIONSHIPS & FAMILY",
    "SHOPPING & PRODUCTS",
    "TRAVEL",
    "HOBBIES & INTERESTS",
    "MISCELLANEOUS",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dropbox client
# ---------------------------------------------------------------------------


def init_dropbox() -> dropbox.Dropbox:
    """Initialize Dropbox client, handling token refresh if configured."""
    access_token = os.environ.get("DROPBOX_ACCESS_TOKEN")
    refresh_token = os.environ.get("DROPBOX_REFRESH_TOKEN")
    app_key = os.environ.get("DROPBOX_APP_KEY")
    app_secret = os.environ.get("DROPBOX_APP_SECRET")

    if refresh_token and app_key and app_secret:
        log.info("Using Dropbox refresh token for authentication")
        dbx = dropbox.Dropbox(
            oauth2_refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret,
        )
    elif access_token:
        log.info("Using Dropbox access token for authentication")
        dbx = dropbox.Dropbox(access_token)
    else:
        log.error("No Dropbox credentials found. Set DROPBOX_ACCESS_TOKEN or refresh token vars.")
        sys.exit(1)

    # Verify connection
    try:
        account = dbx.users_get_current_account()
        log.info(f"Connected to Dropbox as: {account.name.display_name}")
    except Exception as e:
        log.error(f"Dropbox authentication failed: {e}")
        sys.exit(1)

    return dbx


def dbx_read_file(dbx: dropbox.Dropbox, path: str) -> Optional[str]:
    """Read a text file from Dropbox, return contents or None."""
    try:
        _, response = dbx.files_download(path)
        return response.content.decode("utf-8", errors="replace")
    except ApiError as e:
        if e.error.is_path() and e.error.get_path().is_not_found():
            return None
        raise


def dbx_write_file(dbx: dropbox.Dropbox, path: str, content: str):
    """Write a text file to Dropbox, overwriting if it exists."""
    dbx.files_upload(
        content.encode("utf-8"),
        path,
        mode=WriteMode.overwrite,
        mute=True,
    )


def dbx_list_md_files(dbx: dropbox.Dropbox, folder: str) -> list[dict]:
    """List all .md files in a Dropbox folder."""
    files = []
    try:
        result = dbx.files_list_folder(folder)
        while True:
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata) and entry.name.endswith(".md"):
                    files.append({
                        "path": entry.path_display,
                        "name": entry.name,
                        "content_hash": entry.content_hash,
                    })
            if not result.has_more:
                break
            result = dbx.files_list_folder_continue(result.cursor)
    except ApiError as e:
        if e.error.is_path() and e.error.get_path().is_not_found():
            log.warning(f"Folder not found: {folder}")
        else:
            raise
    return files


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def load_manifest(dbx: dropbox.Dropbox) -> dict:
    content = dbx_read_file(dbx, MANIFEST_PATH)
    if content:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            log.warning("Manifest corrupted, starting fresh")
    return {"processed": {}, "last_run": None}


def save_manifest(dbx: dropbox.Dropbox, manifest: dict):
    manifest["last_run"] = datetime.now().isoformat()
    dbx_write_file(dbx, MANIFEST_PATH, json.dumps(manifest, indent=2))


# ---------------------------------------------------------------------------
# Chat parsing
# ---------------------------------------------------------------------------


def parse_existing_metadata(content: str) -> dict:
    meta = {}
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if m:
        meta["title"] = m.group(1).strip()

    m = re.search(r"\*\*Exported:\*\*\s*(.+)", content)
    if m:
        try:
            dt = datetime.strptime(m.group(1).strip(), "%Y-%m-%d %H:%M:%S")
            meta["date"] = dt.strftime("%Y-%m-%d")
        except ValueError:
            meta["date"] = m.group(1).strip()

    m = re.search(r"\*\*Source:\*\*\s*(https?://\S+)", content)
    if m:
        meta["url"] = m.group(1).strip()

    return meta


def extract_chat_text(content: str) -> str:
    idx = content.find("## Human")
    if idx != -1:
        return content[idx:]
    return content


# ---------------------------------------------------------------------------
# Gemini LLM calls
# ---------------------------------------------------------------------------


def init_gemini():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        log.error("No Gemini API key found. Set GEMINI_API_KEY.")
        sys.exit(1)
    return genai.Client(api_key=api_key)


def generate_frontmatter(client, chat_text: str, source: str, existing_meta: dict) -> dict:
    truncated = chat_text[:MAX_CONTENT_CHARS]
    if len(chat_text) > MAX_CONTENT_CHARS:
        truncated += "\n\n[... conversation continues ...]"

    topic_list = "\n".join(f"  - {t}" for t in TOPIC_CATEGORIES)

    prompt = f"""You are a metadata tagger for an Obsidian knowledge base. Analyze this AI chat conversation and return ONLY valid YAML (no markdown fences, no explanation).

The YAML must have exactly these fields:
- summary: A 1-2 sentence summary of what the conversation covered. Write in plain language.
- tags: A list of 3-7 lowercase kebab-case tags describing specific subjects (e.g., eeg-microstates, honda-accord, python-scripting). Be specific, not generic.
- topic: Pick the single best-fitting category from this list:
{topic_list}
  If none fit well, you may create a new one in the same ALL-CAPS style.

Source AI: {source}
Title: {existing_meta.get('title', 'Unknown')}

--- CONVERSATION ---
{truncated}
--- END ---

Return ONLY the YAML. Example format:
summary: Discussion about removing a stripped bolt from a Honda Accord serpentine belt tensioner.
tags:
  - honda-accord
  - bolt-extraction
  - car-repair
  - serpentine-belt
topic: CAR MAINTENANCE
"""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        raw = response.text.strip()
        raw = re.sub(r"^```ya?ml\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        parsed = yaml.safe_load(raw)
        if isinstance(parsed, dict):
            return parsed
        log.warning(f"LLM returned non-dict YAML: {type(parsed)}")
        return {}
    except Exception as e:
        log.error(f"Gemini call failed: {e}")
        return {}


# ---------------------------------------------------------------------------
# File processing
# ---------------------------------------------------------------------------


def process_file(
    gemini_client, dbx: dropbox.Dropbox, file_info: dict, source: str
) -> Optional[str]:
    content = dbx_read_file(dbx, file_info["path"])
    if content is None:
        log.warning(f"  Could not read: {file_info['path']}")
        return None

    # Strip existing YAML frontmatter if present
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end != -1:
            content = content[end + 5:]

    existing_meta = parse_existing_metadata(content)
    chat_text = extract_chat_text(content)

    if len(chat_text.strip()) < 50:
        log.info(f"  Skipping (too short): {file_info['name']}")
        return None

    llm_meta = generate_frontmatter(gemini_client, chat_text, source, existing_meta)
    if not llm_meta:
        log.warning(f"  No metadata returned for: {file_info['name']}")
        return None

    frontmatter = {
        "source": source,
        "title": existing_meta.get("title", file_info["name"].replace(".md", "")),
        "date": existing_meta.get("date", "unknown"),
        "url": existing_meta.get("url", ""),
        "summary": llm_meta.get("summary", ""),
        "tags": llm_meta.get("tags", []),
        "topic": llm_meta.get("topic", "MISCELLANEOUS"),
        "processed_at": datetime.now().isoformat(),
    }

    if not frontmatter["url"]:
        del frontmatter["url"]

    yaml_block = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
    output_content = f"---\n{yaml_block}---\n\n{content}"

    output_path = f"{OUTPUT_ROOT}/{source}/{file_info['name']}"
    dbx_write_file(dbx, output_path, output_content)

    return output_path


# ---------------------------------------------------------------------------
# Index builders
# ---------------------------------------------------------------------------


def build_moc_index(dbx: dropbox.Dropbox):
    log.info("Building MOC index...")
    all_files = _collect_enriched_files(dbx)

    by_topic = {}
    for item in all_files:
        topic = item.get("topic", "MISCELLANEOUS")
        by_topic.setdefault(topic, []).append(item)

    lines = [
        "---",
        "title: AI Chat Index",
        f"updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"total_chats: {len(all_files)}",
        "---",
        "",
        "# AI Chat Knowledge Base",
        "",
        f"**{len(all_files)}** conversations across {len(by_topic)} topics.",
        "",
    ]

    for topic in sorted(by_topic.keys()):
        items = by_topic[topic]
        lines.append(f"## {topic}")
        lines.append("")
        for item in sorted(items, key=lambda x: x.get("date", ""), reverse=True):
            title = item.get("title", item["_filename"])
            source_badge = item.get("_source", "")
            summary = item.get("summary", "")
            link = item["_link"]
            date = item.get("date", "")
            line = f"- {link} `{source_badge}` {date}"
            if summary:
                line += f"\n  {summary}"
            lines.append(line)
        lines.append("")

    dbx_write_file(dbx, f"{OUTPUT_ROOT}/_index.md", "\n".join(lines))
    log.info(f"MOC index written ({len(all_files)} entries)")


def build_topic_indexes(dbx: dropbox.Dropbox):
    log.info("Building per-topic indexes...")
    all_files = _collect_enriched_files(dbx)

    by_topic = {}
    for item in all_files:
        topic = item.get("topic", "MISCELLANEOUS")
        by_topic.setdefault(topic, []).append(item)

    for topic, items in by_topic.items():
        safe_name = re.sub(r"[^\w\s-]", "", topic).strip().replace(" ", "_")
        lines = [
            "---",
            f'title: "{topic}"',
            "type: topic-index",
            f"chat_count: {len(items)}",
            f"updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "---",
            "",
            f"# {topic}",
            "",
            f"{len(items)} conversations in this topic.",
            "",
        ]
        for item in sorted(items, key=lambda x: x.get("date", ""), reverse=True):
            title = item.get("title", item["_filename"])
            source = item.get("_source", "")
            date = item.get("date", "")
            link_name = item["_filename"].replace(".md", "")
            link = f"[[{source}/{link_name}|{title}]]"
            summary = item.get("summary", "")
            tags = item.get("tags", [])
            tag_str = " ".join(f"`{t}`" for t in tags[:5]) if tags else ""
            lines.append(f"- **{link}** `{source}` {date}")
            if summary:
                lines.append(f"  {summary}")
            if tag_str:
                lines.append(f"  {tag_str}")
            lines.append("")

        dbx_write_file(dbx, f"{OUTPUT_ROOT}/Topics/{safe_name}.md", "\n".join(lines))

    log.info(f"Built {len(by_topic)} topic index files")


def _collect_enriched_files(dbx: dropbox.Dropbox) -> list[dict]:
    all_files = []
    for source_name in ["ChatGPT", "Claude", "Gemini"]:
        files = dbx_list_md_files(dbx, f"{OUTPUT_ROOT}/{source_name}")
        for f in files:
            try:
                content = dbx_read_file(dbx, f["path"])
                if not content or not content.startswith("---\n"):
                    continue
                end = content.find("\n---\n", 4)
                if end == -1:
                    continue
                meta = yaml.safe_load(content[4:end])
                if not isinstance(meta, dict):
                    continue
                meta["_filename"] = f["name"]
                meta["_source"] = source_name
                meta["_link"] = f"[[{source_name}/{f['name'].replace('.md', '')}]]"
                all_files.append(meta)
            except Exception:
                continue
    return all_files


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def discover_files(dbx: dropbox.Dropbox) -> list[dict]:
    files = []
    for source, dirpath in SOURCE_DIRS.items():
        for f in dbx_list_md_files(dbx, dirpath):
            if not f["name"].startswith("."):
                files.append({
                    "source": source,
                    "path": f["path"],
                    "name": f["name"],
                    "content_hash": f["content_hash"],
                })
    return files


def run_pipeline():
    dbx = init_dropbox()
    manifest = load_manifest(dbx)
    processed = manifest.get("processed", {})

    all_files = discover_files(dbx)
    log.info(f"Discovered {len(all_files)} total chat files")

    to_process = []
    for f in all_files:
        key = f"{f['source']}/{f['name']}"
        if FORCE_REPROCESS or key not in processed or processed[key].get("hash") != f["content_hash"]:
            f["key"] = key
            to_process.append(f)

    log.info(f"{len(to_process)} files to process ({len(all_files) - len(to_process)} already up to date)")

    if DRY_RUN:
        for f in to_process:
            print(f"  [DRY RUN] Would process: {f['key']}")
        return

    if not to_process:
        log.info("Nothing to process. Rebuilding indexes...")
        build_moc_index(dbx)
        build_topic_indexes(dbx)
        save_manifest(dbx, manifest)
        return

    to_process = to_process[:MAX_FILES]
    if len(to_process) == MAX_FILES:
        log.info(f"Limited to {MAX_FILES} files this run")

    gemini_client = init_gemini()

    success_count = 0
    error_count = 0

    for i, f in enumerate(to_process):
        log.info(f"[{i+1}/{len(to_process)}] Processing: {f['key']}")
        try:
            output_path = process_file(gemini_client, dbx, f, f["source"])
            if output_path:
                processed[f["key"]] = {
                    "hash": f["content_hash"],
                    "output": output_path,
                    "processed_at": datetime.now().isoformat(),
                }
                success_count += 1
                log.info(f"  -> {output_path}")
            else:
                processed[f["key"]] = {
                    "hash": f["content_hash"],
                    "output": None,
                    "processed_at": datetime.now().isoformat(),
                    "skipped": True,
                }
        except Exception as e:
            log.error(f"  Error processing {f['key']}: {e}")
            error_count += 1

        if i < len(to_process) - 1:
            time.sleep(REQUEST_DELAY)

        if (i + 1) % 10 == 0:
            manifest["processed"] = processed
            save_manifest(dbx, manifest)

    manifest["processed"] = processed
    save_manifest(dbx, manifest)

    log.info(f"Done. {success_count} processed, {error_count} errors, "
             f"{len(to_process) - success_count - error_count} skipped")

    build_moc_index(dbx)
    build_topic_indexes(dbx)


if __name__ == "__main__":
    run_pipeline()
