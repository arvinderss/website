#!/usr/bin/env python3
# build_nav.py
# Purpose: Generate a site-wide navigation menu from the repo's folder/file
#          layout and inject it into every HTML page between NAV markers.
#          Top-level folders become menu groups; .html files become links.
# Author:  <arvinderss>
# Created: <set on first commit>
# Assumes: Run from repo root. Pages opt in by including the marker pair:
#              <!-- NAV:START --> ... <!-- NAV:END -->
#          Files without both markers are skipped untouched. No external deps.

import html
import re
import sys
from pathlib import Path

# Why constants, not literals scattered below: the marker contract is the
# single integration point with the user's hand-written HTML — keep it in one place.
NAV_START = "<!-- NAV:START -->"
NAV_END = "<!-- NAV:END -->"
MARKER_RE = re.compile(
    re.escape(NAV_START) + r".*?" + re.escape(NAV_END),
    re.DOTALL,
)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

REPO_ROOT = Path(__file__).resolve().parent.parent
# Folders that are never content groups, even if they contain .html.
IGNORE_DIRS = {"node_modules", "assets", ".git", ".github", "scripts"}


def derive_label(file_path):
    """Return a human-readable menu label for an HTML file.

    Prefers the page's <title>; falls back to a prettified filename so a
    missing or empty title never produces a blank menu entry.
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        text = ""
    match = TITLE_RE.search(text)
    if match:
        title = html.unescape(match.group(1)).strip()
        if title:
            return title
    stem = file_path.stem.replace("-", " ").replace("_", " ").strip()
    return stem.title() if stem else file_path.name


def collect_pages():
    """Walk the repo and group HTML files by their top-level folder.

    Returns (groups, root_pages):
      groups     -> dict {folder_name: [(label, relpath), ...]}, sorted.
      root_pages -> list of (label, relpath) for top-level .html files.
    """
    groups = {}
    root_pages = []
    for path in sorted(REPO_ROOT.rglob("*.html")):
        rel = path.relative_to(REPO_ROOT)
        parts = rel.parts
        if any(part in IGNORE_DIRS for part in parts):
            continue
        label = derive_label(path)
        href = "/" + rel.as_posix()
        if len(parts) == 1:
            root_pages.append((label, href))
        else:
            group = parts[0]
            groups.setdefault(group, []).append((label, href))
    for items in groups.values():
        items.sort(key=lambda pair: pair[0].lower())
    root_pages.sort(key=lambda pair: pair[0].lower())
    return dict(sorted(groups.items())), root_pages


def render_menu(groups, root_pages):
    """Render the menu as semantic HTML. Escapes all dynamic text.

    Why <nav> + <details>: native disclosure groups need no JS and stay
    accessible; the user can style .site-nav freely without the script
    caring about presentation.
    """
    lines = ['<nav class="site-nav" aria-label="Site navigation">', "  <ul>"]
    for label, href in root_pages:
        lines.append(
            f'    <li><a href="{html.escape(href)}">{html.escape(label)}</a></li>'
        )
    for group, items in groups.items():
        group_label = html.escape(group.replace("-", " ").replace("_", " ").title())
        lines.append("    <li>")
        lines.append(f"      <details><summary>{group_label}</summary>")
        lines.append("        <ul>")
        for label, href in items:
            lines.append(
                f'          <li><a href="{html.escape(href)}">'
                f"{html.escape(label)}</a></li>"
            )
        lines.append("        </ul>")
        lines.append("      </details>")
        lines.append("    </li>")
    lines.append("  </ul>")
    lines.append("</nav>")
    return "\n".join(lines)


def inject(menu_html):
    """Replace marked nav region in every opted-in page. Returns count changed."""
    block = f"{NAV_START}\n{menu_html}\n{NAV_END}"
    changed = 0
    for path in sorted(REPO_ROOT.rglob("*.html")):
        if any(part in IGNORE_DIRS for part in path.relative_to(REPO_ROOT).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            print(f"skip (unreadable): {path}", file=sys.stderr)
            continue
        if NAV_START not in text or NAV_END not in text:
            continue
        new_text = MARKER_RE.sub(lambda _: block, text, count=1)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed += 1
            print(f"updated: {path.relative_to(REPO_ROOT)}")
    return changed


def main():
    groups, root_pages = collect_pages()
    menu_html = render_menu(groups, root_pages)
    changed = inject(menu_html)
    print(f"done: {changed} file(s) updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# What it does: builds a folder-grouped nav menu from the repo's .html layout
#   and rewrites the region between NAV:START/NAV:END markers in every page
#   that contains them.
# Security limits: trusts repo contents (not external input); writes only
#   inside the repo tree; escapes all label/href text to prevent broken markup
#   from filenames. Not a sanitizer for untrusted third-party HTML.
# Before production: add the marker pair to each page where the menu should
#   appear, and style .site-nav in your existing CSS/theme system.
