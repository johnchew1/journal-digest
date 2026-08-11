#!/usr/bin/env python3
"""Build weekly digest markdown for GitHub Issue push (no SMTP needed)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pollutant_analyzer import analyze_articles

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "public" / "data" / "articles.json"
WEEKLY_DIR = ROOT / "public" / "weekly"
SITE_URL = "https://johnchew1.github.io/journal-digest/"


def load_data() -> dict:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing {DATA_FILE}")
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def filter_weekly_articles(articles: list[dict], days: int = 7) -> list[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date()
    weekly = []
    for a in articles:
        pub = a.get("published")
        if not pub:
            continue
        try:
            pub_date = datetime.strptime(pub[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        if pub_date >= cutoff:
            weekly.append(a)
    return weekly


def build_weekly_analysis(data: dict | None = None) -> tuple[dict, str, str]:
    data = data or load_data()
    articles = data.get("articles", [])
    weekly = filter_weekly_articles(articles)
    if not weekly:
        weekly = articles

    analysis = analyze_articles(weekly)
    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    week_end = now.strftime("%Y-%m-%d")
    week_label = f"{week_start} ~ {week_end}"
    return analysis, week_label, week_end


def build_markdown(analysis: dict, week_label: str) -> str:
    brief = analysis["digest"]["writing_brief"]
    stats = brief.get("stats", {})
    pollutant = analysis["digest"]["pollutant_articles"]
    mp_articles = [a for a in pollutant if "微塑料" in a.get("pollutant_categories", [])]

    lines = [
        f"## 📬 期刊速递 · 每周写作风向",
        f"**{week_label}** · NC / EST / JHM",
        "",
        brief.get("overview", ""),
        "",
        f"- 新污染物：**{stats.get('total_pollutant', 0)}** 篇",
        f"- 微塑料：**{stats.get('microplastic', 0)}** 篇",
        f"- [查看完整网站]({SITE_URL})",
        "",
        "---",
        "",
        "### 🔥 热点主题",
        "",
    ]

    for t in brief.get("hot_themes", [])[:6]:
        lines.append(f"#### {t['theme']}（{t['heat_level']}热度 · {t['article_count']}篇）")
        for a in t.get("writing_angles", [])[:2]:
            lines.append(f"- {a}")
        lines.append("")

    lines += ["---", "", "### ✍️ 推荐写作选题", ""]
    for i, p in enumerate(brief.get("daily_picks", [])[:5], 1):
        lines.append(f"**{i}. {p.get('title_zh', '')}**")
        lines.append(f"- 期刊：{p.get('journal', '')} · {p.get('why_write', '')}")
        lines.append(f"- 💡 {p.get('suggested_angle', '')}")
        if p.get("url"):
            lines.append(f"- [阅读原文]({p['url']})")
        lines.append("")

    lines += ["---", "", "### 🔬 微塑料文献精选", ""]
    if mp_articles:
        for a in mp_articles[:8]:
            themes = "、".join(a.get("microplastic_themes", [])[:2]) or "综合"
            title = a.get("title_zh") or a.get("title", "")
            url = a.get("url", "")
            lines.append(f"- **[{themes}]** {title[:80]} ([原文]({url}))")
    else:
        lines.append("_本周暂无微塑料相关文献_")

    lines += [
        "",
        "---",
        "",
        "_由 GitHub Actions 自动生成 · 每周一 09:00（北京时间）_",
    ]
    return "\n".join(lines)


def main() -> None:
    output_path = None
    if len(sys.argv) > 1 and sys.argv[1] == "--output":
        output_path = Path(sys.argv[2])

    analysis, week_label, week_end = build_weekly_analysis()
    markdown = build_markdown(analysis, week_label)
    title = f"📬 周报 {week_end} · 新污染物写作风向"

    if output_path:
        output_path.write_text(markdown, encoding="utf-8")
        title_path = output_path.with_suffix(".title")
        title_path.write_text(title, encoding="utf-8")
        print(f"Wrote {output_path}")
        return

    # Default: save to public/weekly/
    WEEKLY_DIR.mkdir(parents=True, exist_ok=True)
    archive = WEEKLY_DIR / f"{week_end}.md"
    latest = WEEKLY_DIR / "latest.md"
    archive.write_text(markdown, encoding="utf-8")
    latest.write_text(markdown, encoding="utf-8")
    (WEEKLY_DIR / "latest.title").write_text(title, encoding="utf-8")
    print(markdown[:200])
    print(f"\nSaved to {latest}")


if __name__ == "__main__":
    main()
