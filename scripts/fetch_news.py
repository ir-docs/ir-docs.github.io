import re
import datetime as dt
from pathlib import Path
import feedparser
import yaml

ROOT = Path(__file__).resolve().parents[1]
NEWS_DIR = ROOT / "news"

def clean(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def match_keywords(text, keywords):
    t = text.lower()
    return any(k.lower() in t for k in keywords)

def collect(feeds, keywords, limit=12):
    items = []
    for f in feeds:
        src = f.get("name", "Source")
        d = feedparser.parse(f.get("url"))
        for e in d.entries[:40]:
            title = clean(getattr(e, "title", ""))
            summary = clean(getattr(e, "summary", ""))
            link = getattr(e, "link", "")
            blob = f"{title} {summary}"
            if match_keywords(blob, keywords):
                items.append((title, summary, link, src))
    seen = set()
    unique = []
    for i in items:
        if i[2] not in seen:
            seen.add(i[2])
            unique.append(i)
    return unique[:limit]

def main():
    cfg = yaml.safe_load((ROOT / "sources.yml").read_text(encoding="utf-8"))

    iran_items = collect(
        cfg["iran_news_sources"],
        cfg["keywords_iran"]
    )

    world_items = collect(
        cfg["world_news_sources"],
        cfg["keywords_world"]
    )

    NEWS_DIR.mkdir(exist_ok=True)

    now = dt.datetime.utcnow()
    fname = NEWS_DIR / f"auto-{now.strftime('%Y-%m-%d-%H%M')}.md"

    lines = [
        "---",
        "layout: news",
        f"title: Auto News – {now.strftime('%Y-%m-%d %H:%M')} UTC",
        f"date: {now.strftime('%Y-%m-%d')}",
        "---",
        "",
        "## 🇮🇷 Iran — Important headlines",
        ""
    ]

    for t, s, l, src in iran_items:
        lines += [
            f"### {t}",
            f"*Source:* {src}",
            s,
            f"[Open source link]({l})",
            ""
        ]

    lines += ["---", "", "## 🌍 World — Important headlines", ""]

    for t, s, l, src in world_items:
        lines += [
            f"### {t}",
            f"*Source:* {src}",
            s,
            f"[Open source link]({l})",
            ""
        ]

    fname.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {fname}")

if __name__ == "__main__":
    main()
