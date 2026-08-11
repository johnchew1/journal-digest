#!/usr/bin/env python3
"""Fetch latest articles from NC, EST, JHM and translate to Chinese."""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path

import requests
from deep_translator import GoogleTranslator

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "public" / "data" / "articles.json"

JOURNALS = {
    "NC": {
        "name": "Nature Communications",
        "issn": "2041-1723",
        "color": "#c0392b",
    },
    "EST": {
        "name": "Environmental Science & Technology",
        "issn": "0013-936X",
        "color": "#2980b9",
    },
    "JHM": {
        "name": "Journal of Hazardous Materials",
        "issn": "0304-3894",
        "color": "#27ae60",
    },
}

CROSSREF_URL = "https://api.crossref.org/journals/{issn}/works"
USER_AGENT = "JournalDigest/1.0 (mailto:example@example.com)"
DAYS_BACK = 7
ARTICLES_PER_JOURNAL = 20


def parse_abstract(raw: str | None) -> str:
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_date(item: dict) -> str | None:
    for key in ("published-print", "published-online", "created", "issued"):
        parts = item.get(key, {}).get("date-parts", [[]])
        if parts and parts[0]:
            p = parts[0]
            if len(p) >= 3:
                return f"{p[0]:04d}-{p[1]:02d}-{p[2]:02d}"
            if len(p) >= 2:
                return f"{p[0]:04d}-{p[1]:02d}-01"
            if len(p) >= 1:
                return f"{p[0]:04d}-01-01"
    return None


def get_doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}"


def fetch_journal_articles(journal_id: str, config: dict) -> list[dict]:
    params = {
        "rows": ARTICLES_PER_JOURNAL,
        "sort": "published",
        "order": "desc",
        "filter": f"from-pub-date:{(datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)).strftime('%Y-%m-%d')}",
    }
    url = CROSSREF_URL.format(issn=config["issn"])
    resp = requests.get(
        url,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()
    items = resp.json()["message"]["items"]

    articles = []
    for item in items:
        title_list = item.get("title", [])
        if not title_list:
            continue
        title = title_list[0].strip()
        abstract = parse_abstract(item.get("abstract"))
        pub_date = parse_date(item)
        doi = item.get("DOI", "")

        articles.append(
            {
                "journal": journal_id,
                "journal_name": config["name"],
                "title": title,
                "abstract": abstract,
                "published": pub_date,
                "doi": doi,
                "url": get_doi_url(doi) if doi else "",
            }
        )
    return articles


def translate_text(text: str, translator: GoogleTranslator) -> str:
    if not text or not text.strip():
        return ""
    # Google Translate has a ~5000 char limit; chunk if needed
    max_len = 4500
    if len(text) <= max_len:
        try:
            return translator.translate(text)
        except Exception as e:
            print(f"  Translation warning: {e}", file=sys.stderr)
            return ""

    chunks = []
    for i in range(0, len(text), max_len):
        chunk = text[i : i + max_len]
        try:
            chunks.append(translator.translate(chunk))
            time.sleep(0.3)
        except Exception as e:
            print(f"  Translation chunk warning: {e}", file=sys.stderr)
    return " ".join(chunks)


def translate_articles(articles: list[dict]) -> list[dict]:
    translator = GoogleTranslator(source="en", target="zh-CN")
    for i, article in enumerate(articles):
        print(f"  Translating [{i + 1}/{len(articles)}]: {article['title'][:60]}...")
        article["title_zh"] = translate_text(article["title"], translator)
        time.sleep(0.5)
        if article["abstract"]:
            article["abstract_zh"] = translate_text(article["abstract"], translator)
            time.sleep(0.5)
        else:
            article["abstract_zh"] = "（暂无摘要）"
    return articles


def main() -> None:
    print("Fetching articles from CrossRef...")
    all_articles: list[dict] = []

    for journal_id, config in JOURNALS.items():
        print(f"\n[{journal_id}] {config['name']}")
        try:
            articles = fetch_journal_articles(journal_id, config)
            print(f"  Found {len(articles)} articles")
            all_articles.extend(articles)
        except Exception as e:
            print(f"  Error fetching {journal_id}: {e}", file=sys.stderr)

    all_articles.sort(
        key=lambda a: a.get("published") or "0000-00-00",
        reverse=True,
    )

    print(f"\nTranslating {len(all_articles)} articles to Chinese...")
    all_articles = translate_articles(all_articles)

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "journals": {k: {"name": v["name"], "color": v["color"]} for k, v in JOURNALS.items()},
        "articles": all_articles,
    }

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved {len(all_articles)} articles to {DATA_FILE}")


if __name__ == "__main__":
    main()
