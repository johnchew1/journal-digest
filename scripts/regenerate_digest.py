#!/usr/bin/env python3
"""Re-run pollutant analysis on existing articles.json without re-fetching."""

import json
import sys
from pathlib import Path

from pollutant_analyzer import analyze_articles

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "public" / "data" / "articles.json"


def main() -> None:
    if not DATA_FILE.exists():
        print(f"Missing {DATA_FILE}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    articles = data.get("articles", [])
    print(f"Analyzing {len(articles)} articles...")

    analysis = analyze_articles(articles)
    data["articles"] = analysis["articles"]
    data["digest"] = analysis["digest"]

    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    brief = analysis["digest"]["writing_brief"]
    print(f"Pollutant: {analysis['digest']['pollutant_count']}, "
          f"Microplastic: {analysis['digest']['microplastic_count']}")
    print(f"Overview: {brief['overview']}")


if __name__ == "__main__":
    main()
