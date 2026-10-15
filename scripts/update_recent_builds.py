#!/usr/bin/env python3
"""Refresh the recent public repositories panel in the profile README."""

import json
from pathlib import Path
from urllib.request import Request, urlopen

README = Path(__file__).resolve().parents[1] / "README.md"
START = "<!-- RECENT_BUILDS_START -->"
END = "<!-- RECENT_BUILDS_END -->"
API = "https://api.github.com/users/HardikKari/repos?per_page=100&type=owner"


def clean(value):
    return " ".join(str(value or "").replace("|", " ").split())


def main():
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "HardikKari-profile"}
    with urlopen(Request(API, headers=headers), timeout=20) as response:
        repos = json.load(response)
    featured = sorted(
        (repo for repo in repos if not repo["fork"] and repo["name"].lower() not in {"hardikkari", "test"}),
        key=lambda repo: repo["pushed_at"],
        reverse=True,
    )[:3]
    lines = []
    for repo in featured:
        description = clean(repo.get("description")) or "Explore the source code."
        lines.append(f"- [{repo['name']}]({repo['html_url']}) — {description}")
    content = README.read_text()
    if content.count(START) != 1 or content.count(END) != 1:
        raise ValueError("README must contain one pair of recent-build markers")
    before, rest = content.split(START, 1)
    _, after = rest.split(END, 1)
    updated = before + START + "\n" + "\n".join(lines) + "\n" + END + after
    if updated != content:
        README.write_text(updated)


if __name__ == "__main__":
    main()
