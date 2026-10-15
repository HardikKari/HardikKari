#!/usr/bin/env python3
"""Refresh the profile's recent public repositories and self-hosted stats card."""

import html
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
STATS = ROOT / "assets" / "stats.svg"
START = "<!-- RECENT_BUILDS_START -->"
END = "<!-- RECENT_BUILDS_END -->"
USER = "HardikKari"
API = "https://api.github.com"


def fetch(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "HardikKari-profile"}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urlopen(Request(API + path, headers=headers), timeout=20) as response:
        return json.load(response)


def clean(value):
    return " ".join(str(value or "").replace("|", " ").split())


def update_readme(repos):
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


def update_stats(user, repos):
    public = [repo for repo in repos if not repo["fork"]]
    languages = {repo["language"] for repo in public if repo.get("language")}
    projects = [repo for repo in public if repo["name"].lower() not in {"hardikkari", "test"}]
    last_push = max((repo["pushed_at"] for repo in projects if repo.get("pushed_at")), default=None)
    last_push_label = datetime.fromisoformat(last_push.replace("Z", "+00:00")).strftime("%b %d, %Y") if last_push else "No public pushes"
    since_label = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")).strftime("%b %Y")
    metrics = [
        ("PUBLIC REPOS", f"{len(public):02d}"),
        ("LANGUAGES DETECTED", f"{len(languages):02d}"),
        ("LATEST PROJECT PUSH", last_push_label),
        ("ON GITHUB SINCE", since_label),
    ]
    cards = []
    for index, (label, value) in enumerate(metrics):
        x = 30 + index * 245
        cards.append(
            f'<rect x="{x}" y="82" width="225" height="130" rx="14" fill="#172238" stroke="#415b84"/>'
            f'<text x="{x+18}" y="118" fill="#8fb0ce" font-family="monospace" font-size="14">{html.escape(label)}</text>'
            f'<text x="{x+18}" y="170" fill="#f3f7ff" font-family="Arial,Helvetica,sans-serif" font-size="28" font-weight="bold">{html.escape(value)}</text>'
            f'<path d="M{x+18} 188h75" stroke="#69dbc7" stroke-width="4" stroke-linecap="round"/>'
        )
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="240" viewBox="0 0 1000 240" role="img" aria-labelledby="title desc">'
        '<title id="title">Hardik Kari public GitHub stats</title>'
        '<desc id="desc">Public repository count, detected languages, latest project push, and account creation date.</desc>'
        '<rect width="1000" height="240" rx="18" fill="#0d1117"/>'
        '<rect x="10" y="10" width="980" height="220" rx="14" fill="#101a2a" stroke="#6c75ed" stroke-width="2"/>'
        '<circle cx="34" cy="38" r="6" fill="#69dbc7"/>'
        '<text x="50" y="45" fill="#cfd7ff" font-family="monospace" font-size="19" font-weight="bold">PUBLIC REPOSITORY SIGNAL</text>'
        '<text x="760" y="45" fill="#81a1bd" font-family="monospace" font-size="14">AUTO-REFRESHED DAILY</text>'
        + "".join(cards)
        + "</svg>\n"
    )
    if not STATS.exists() or STATS.read_text() != svg:
        STATS.write_text(svg)


def main():
    user = fetch(f"/users/{USER}")
    repos = fetch(f"/users/{USER}/repos?per_page=100&type=owner")
    update_readme(repos)
    update_stats(user, repos)


if __name__ == "__main__":
    main()
