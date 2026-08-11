#!/usr/bin/env python3
"""Build and send weekly digest email for pollutant/microplastic writing brief."""

from __future__ import annotations

import json
import os
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from pollutant_analyzer import analyze_articles

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "public" / "data" / "articles.json"
SITE_URL = "https://johnchew1.github.io/journal-digest/"
DEFAULT_TO = "zihanzhou1705@outlook.com"


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


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_html(analysis: dict, week_label: str) -> str:
    brief = analysis["digest"]["writing_brief"]
    stats = brief.get("stats", {})
    pollutant = analysis["digest"]["pollutant_articles"]
    mp_articles = [a for a in pollutant if "微塑料" in a.get("pollutant_categories", [])]

    hot_themes_html = ""
    for t in brief.get("hot_themes", [])[:6]:
        angles = "".join(f"<li>{_esc(a)}</li>" for a in t.get("writing_angles", [])[:2])
        hot_themes_html += f"""
        <div style="margin-bottom:16px;padding:12px;background:#f8f9fa;border-left:4px solid #2980b9;">
          <strong>{_esc(t['theme'])}</strong>
          <span style="color:#666;font-size:13px;"> · {_esc(t['heat_level'])}热度 · {t['article_count']}篇</span>
          <ul style="margin:8px 0 0;padding-left:18px;font-size:14px;color:#333;">{angles}</ul>
        </div>"""

    picks_html = ""
    for i, p in enumerate(brief.get("daily_picks", [])[:5], 1):
        picks_html += f"""
        <tr>
          <td style="padding:8px 0;vertical-align:top;width:24px;color:#888;">{i}.</td>
          <td style="padding:8px 0;">
            <strong style="font-size:14px;">{_esc(p.get('title_zh', ''))}</strong>
            <div style="font-size:12px;color:#666;margin-top:4px;">
              [{_esc(p.get('journal', ''))}] {_esc(p.get('why_write', ''))}
            </div>
            <div style="font-size:13px;color:#117a65;margin-top:4px;">💡 {_esc(p.get('suggested_angle', ''))}</div>
          </td>
        </tr>"""

    mp_list_html = ""
    for a in mp_articles[:8]:
        themes = "、".join(a.get("microplastic_themes", [])[:2]) or "综合"
        mp_list_html += f"""
        <li style="margin-bottom:8px;">
          <strong>[{_esc(themes)}]</strong> {_esc(a.get('title_zh', ''))[:70]}
          <a href="{_esc(a.get('url', ''))}" style="font-size:12px;color:#2980b9;">原文</a>
        </li>"""

    cat_stats = stats.get("categories", {})
    cat_line = " · ".join(f"{k} {v}篇" for k, v in cat_stats.items()) or "暂无"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;
             max-width:640px;margin:0 auto;padding:20px;color:#222;line-height:1.6;">
  <div style="background:#1a2332;color:#fff;padding:20px;border-radius:8px 8px 0 0;">
    <h1 style="margin:0;font-size:20px;">📬 期刊速递 · 每周写作风向</h1>
    <p style="margin:8px 0 0;opacity:0.85;font-size:14px;">{week_label} · NC / EST / JHM</p>
  </div>

  <div style="border:1px solid #e5e2db;border-top:none;padding:20px;border-radius:0 0 8px 8px;">
    <p style="background:#f0f4f8;padding:12px;border-radius:6px;border-left:4px solid #2980b9;">
      {_esc(brief.get('overview', ''))}
    </p>

    <p style="font-size:14px;color:#555;">
      新污染物 <strong>{stats.get('total_pollutant', 0)}</strong> 篇 ·
      微塑料 <strong>{stats.get('microplastic', 0)}</strong> 篇<br>
      {cat_line}
    </p>

    <h2 style="font-size:16px;border-bottom:2px solid #eee;padding-bottom:6px;">🔥 本周热点主题</h2>
    {hot_themes_html or '<p>暂无热点数据</p>'}

    <h2 style="font-size:16px;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:24px;">
      ✍️ 推荐写作选题
    </h2>
    <table style="width:100%;border-collapse:collapse;">{picks_html}</table>

    <h2 style="font-size:16px;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:24px;">
      🔬 微塑料文献精选
    </h2>
    <ul style="padding-left:18px;font-size:14px;">{mp_list_html or '<li>本周暂无微塑料相关文献</li>'}</ul>

    <p style="text-align:center;margin-top:28px;">
      <a href="{SITE_URL}" style="background:#2980b9;color:#fff;padding:10px 24px;
         text-decoration:none;border-radius:6px;font-size:14px;">查看完整网站 →</a>
    </p>

    <p style="font-size:11px;color:#999;text-align:center;margin-top:20px;">
      数据来源 CrossRef · 自动整理 NC/EST/JHM · 每周一 09:00 推送
    </p>
  </div>
</body>
</html>"""


def build_text(analysis: dict, week_label: str) -> str:
    brief = analysis["digest"]["writing_brief"]
    lines = [
        f"期刊速递 · 每周写作风向 ({week_label})",
        "=" * 40,
        brief.get("overview", ""),
        "",
        "【推荐写作选题】",
    ]
    for i, p in enumerate(brief.get("daily_picks", [])[:5], 1):
        lines.append(f"{i}. {p.get('title_zh', '')}")
        lines.append(f"   💡 {p.get('suggested_angle', '')}")
    lines += ["", f"完整内容：{SITE_URL}"]
    return "\n".join(lines)


def send_email(subject: str, html: str, text: str) -> None:
    host = os.environ.get("SMTP_HOST", "smtp.office365.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    to_addr = os.environ.get("EMAIL_TO", DEFAULT_TO)
    from_addr = os.environ.get("EMAIL_FROM", user)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())

    print(f"Email sent to {to_addr}")


def main() -> None:
    data = load_data()
    articles = data.get("articles", [])
    weekly = filter_weekly_articles(articles)

    if not weekly:
        print("No articles in the past 7 days, using all available.", file=sys.stderr)
        weekly = articles

    analysis = analyze_articles(weekly)
    brief = analysis["digest"]["writing_brief"]

    now = datetime.now(timezone.utc)
    week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    week_end = now.strftime("%Y-%m-%d")
    week_label = f"{week_start} ~ {week_end}"

    subject = (
        f"【期刊速递】新污染物写作风向 · 微塑料{brief['stats'].get('microplastic', 0)}篇 "
        f"({week_end})"
    )
    html = build_html(analysis, week_label)
    text = build_text(analysis, week_label)

    if os.environ.get("DRY_RUN"):
        print("=== DRY RUN ===")
        print(f"Subject: {subject}")
        print(text[:500])
        return

    required = ["SMTP_USER", "SMTP_PASSWORD"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    send_email(subject, html, text)


if __name__ == "__main__":
    main()
