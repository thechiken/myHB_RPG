#!/usr/bin/env python3
"""
convert_wikilinks.py

Converts Obsidian-style image embeds:
    ![[image.png]]
    ![[image.png|300]]
    ![[subfolder/image.png|Some alt text]]

into standard Markdown image syntax that Jekyll/kramdown understands:
    ![](assets/image.png)
    ![](assets/image.png)
    ![Some alt text](assets/image.png)

Usage:
    python3 convert_wikilinks.py <path-to-folder-or-file> [--assets-dir assets] [--dry-run]

Examples:
    # Preview changes without touching files
    python3 convert_wikilinks.py docs/history --dry-run

    # Actually rewrite the files
    python3 convert_wikilinks.py docs/history --assets-dir assets
"""

import argparse
import os
import re
import sys

# Matches ![[ ... ]] where ... is "path" optionally followed by "|alias"
WIKILINK_IMAGE_RE = re.compile(r'!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')

# If the alias looks purely numeric (e.g. "300" or "300x200"), Obsidian
# treats it as a resize hint, not alt text — we drop it rather than
# stuffing "300" into the alt attribute.
SIZE_HINT_RE = re.compile(r'^\d+(x\d+)?$')


def convert_line(match: re.Match, assets_dir: str) -> str:
    raw_path, alias = match.group(1), match.group(2)
    filename = os.path.basename(raw_path.strip())

    alt_text = ""
    if alias and not SIZE_HINT_RE.match(alias.strip()):
        alt_text = alias.strip()

    new_path = f"{assets_dir}/{filename}" if assets_dir else filename
    return f"![{alt_text}]({new_path})"


def convert_file(path: str, assets_dir: str, dry_run: bool) -> int:
    with open(path, "r", encoding="utf-8") as f:
        original = f.read()

    matches = list(WIKILINK_IMAGE_RE.finditer(original))
    if not matches:
        return 0

    updated = WIKILINK_IMAGE_RE.sub(lambda m: convert_line(m, assets_dir), original)

    print(f"\n[{path}] — {len(matches)} replacement(s):")
    for m in matches:
        print(f"  {m.group(0)}  ->  {convert_line(m, assets_dir)}")

    if not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            f.write(updated)

    return len(matches)


def collect_md_files(target: str):
    if os.path.isfile(target):
        return [target]
    result = []
    for root, _, files in os.walk(target):
        for name in files:
            if name.lower().endswith(".md"):
                result.append(os.path.join(root, name))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", help="File or folder to process")
    parser.add_argument("--assets-dir", default="assets",
                         help="Folder prefix to insert before image filenames (default: 'assets'). Use '' for none.")
    parser.add_argument("--dry-run", action="store_true",
                         help="Show what would change without writing files")
    args = parser.parse_args()

    if not os.path.exists(args.target):
        print(f"Error: path not found: {args.target}", file=sys.stderr)
        sys.exit(1)

    files = collect_md_files(args.target)
    if not files:
        print("No .md files found.")
        return

    total = 0
    changed_files = 0
    for path in files:
        n = convert_file(path, args.assets_dir, args.dry_run)
        if n:
            total += n
            changed_files += 1

    mode = "would be changed (dry run)" if args.dry_run else "changed"
    print(f"\nDone. {total} embed(s) in {changed_files} file(s) {mode}.")


if __name__ == "__main__":
    main()
