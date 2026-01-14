import os
import re
import datetime as dt
from pathlib import Path

import feedparser
import yaml

ROOT = Path(__file__).resolve().parents[1]
NEWS_DIR = ROOT / "news"

DEFAULT_KEYWORDS = [
    "iran", "tehran", "irgc", "islamic republic", "protest", "human rights"
]

def clean(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)   # strip basic HTML
    text = re.sub(r"\s+", " ", text).strip()
    return text

def match_iran(text: str, keywords) -> bool:
    t = (text or "").lower()
    return any(k.lower() in t for k in keywords)

def main():
    sources_file = ROOT / "sources.yml"
    if not sources_file.exists():
        raise SystemExit("sources.yml not found in repo root")

    cfg = yaml.safe_load(sources_file.read_text(encoding="utf-8")) or {}
    feeds = cfg.get("iran_news_sources", [])
    keywords = cfg.get("keywords", DEFAULT_KEYWORDS)

    NEWS_DIR.mkdir(parents=True, exist_ok=True)

    items = []
    for f in feeds:
        name = f.get("name", "Source")
        url = f.get("url")
        if not url:
            continue

        d = feedparser.parse(url)
        for e in getattr(d, "entries", [])[:50]:
            title = clean(getattr(e, "title", ""))
            link = clean(getattr(e, "link", ""))
            summary = clean(getattr(e, "summary", ""))

            blob = f"{title} {summary} {link}"
            # Reuters world feed is broad -> keyword filter; others are Iran-focused anyway
            if match_iran(blob, keywords) or "reuters" not in name.lower():
                items.append({
                    "source": name,
                    "title": title,
                    "link": link,
                    "summary": summary[:280]  # keep short
                })

    # Deduplicate by link
    seen = set()
    uniq = []
    for it in items:
        if it["link"] and it["link"] not in seen:
            seen.add(it["link"])
            uniq.append(it)

    # Limit output
    uniq = uniq[:25]

    # File name by UTC time to avoid collisions
    now = dt.datetime.utcnow()
    slug = now.strftime("%Y-%m-%d-%H%M")
    out = NEWS_DIR / f"auto-{slug}.md"

    lines = []
    lines += ["---",
              "layout: news",
              f"title: Auto News – {now.strftime('%Y-%m-%d %H:%M')} UTC",
              f"date: {now.strftime('%Y-%m-%d')}",
              "---",
              "",
              "> Auto-generated: headlines + short snippets + source links only.",
              ""]

    if not uniq:
        lines.append("No matching items found.")
    else:
        for it in uniq:
            lines.append(f"## {it['title']}")
            lines.append(f"**Source:** {it['source']}")
            lines.append("")
            if it["summary"]:
                lines.append(it["summary"])
                lines.append("")
            lines.append(f"[Open source link]({it['link']})")
            lines.append("")
            lines.append("---")
            lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote: {out}")

if __name__ == "__main__":
    main()
