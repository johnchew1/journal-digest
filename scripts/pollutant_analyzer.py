#!/usr/bin/env python3
"""Classify articles by pollutant themes and generate daily writing briefs."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timezone


# ── Pollutant category patterns ──────────────────────────────────────────────

POLLUTANT_CATEGORIES: dict[str, list[str]] = {
    "微塑料": [
        r"microplastic", r"nanoplastic", r"\bMPs?\b", r"\bNPLs?\b",
        r"plastic particle", r"plastic debris", r"plastic pollution",
        r"polyethylene", r"polypropylene", r"polystyrene", r"polyurethane",
        r"PLA-NPL", r"tire wear", r"plastic foam", r"plasticizer",
    ],
    "PFAS": [
        r"PFAS", r"PFOA", r"PFOS", r"per- and polyfluoro", r"fluorinated",
        r"forever chemical",
    ],
    "塑化剂与内分泌干扰物": [
        r"phthalate", r"bisphenol", r"\bBPA\b", r"paraben", r"endocrine",
        r"plasticizer", r"antiandrogen",
    ],
    "药物与个人护理品": [
        r"pharmaceutical", r"antibiotic", r"PPCP", r"personal care",
        r"triclosan", r"disinfection by-product", r"trihalomethane",
        r"haloacetonitrile", r"chloramphenicol",
    ],
    "重金属与放射性": [
        r"\bmercury\b", r"\bcadmium\b", r"\blead\b", r"\b arsenic\b",
        r"\buranium\b", r"radionuclide", r"methylmercury",
    ],
    "纳米材料": [
        r"nanomaterial", r"nanoparticle", r"nanoplastic", r"nanozyme",
        r"\bMOF\b", r"quantum dot",
    ],
    "新污染物综合": [
        r"contaminant of emerging concern", r"\bCEC\b", r"emerging contaminant",
        r"emerging pollutant", r"emerging concern",
    ],
}

MICROPLASTIC_THEMES: dict[str, list[str]] = {
    "检测与表征": [
        r"detection", r"characteri", r"spectral", r"spectroscop", r"imaging",
        r"identification", r"quantif", r"monitoring", r"index",
    ],
    "环境行为与迁移": [
        r"transport", r"fate", r"distribution", r"deposition", r"suspension",
        r"sediment", r"bioaccumul", r"bioconcentr", r"trophic", r"ecosystem",
        r"marine", r"atmospheric", r"air-snow", r"drinking water",
    ],
    "老化与界面过程": [
        r"aging", r"weathering", r"adsorption", r"desorption", r"degradation",
        r"photoaged", r"oxidation", r"interface",
    ],
    "毒性与健康风险": [
        r"toxicity", r"exposure", r"health", r"risk", r"human", r"in vivo",
        r"in vitro", r"zebrafish", r"behavioral",
    ],
    "源头与控制": [
        r"mitigation", r"removal", r"treatment", r"abatement", r"control",
        r"retention", r"pavement", r"filter", r"barrier",
    ],
    "生态效应": [
        r"phytoplankton", r"microbial", r"biofilm", r"antibiotic resistance",
        r"ARG", r"algal", r"primary productiv",
    ],
}

WRITING_ANGLE_TEMPLATES: dict[str, list[str]] = {
    "微塑料": [
        "从{subtopic}切入：最新研究揭示了哪些容易被忽视的风险？",
        "对比{journal}最新成果：{subtopic}研究正在发生哪些范式转变？",
        "写给非专业读者：{keyword}到底意味着什么，我们该如何理解？",
        "政策与科普视角：{subtopic}研究对饮用水/食品安全监管有何启示？",
    ],
    "PFAS": [
        "PFAS 研究新进展：{keyword}——公众最需要知道什么？",
        "从实验室到现实：最新 PFAS 毒性/归趋研究如何影响治理逻辑？",
    ],
    "塑化剂与内分泌干扰物": [
        "日常暴露警示：{keyword} 研究告诉了我们什么？",
        "从职业暴露到家庭环境：塑化剂风险如何层层递进？",
    ],
    "药物与个人护理品": [
        "水环境中的隐形杀手：{keyword} 研究热点解读",
        "消毒副产物 + 新污染物：管网末端正在发生什么化学反应？",
    ],
    "default": [
        "新污染物周报：{keyword} 为何成为近期研究焦点？",
        "跨期刊观察：{journal} 最新论文传递了怎样的研究风向？",
    ],
}


def _search_text(article: dict) -> str:
    parts = [
        article.get("title", ""),
        article.get("abstract", ""),
        article.get("title_zh", ""),
        article.get("abstract_zh", ""),
    ]
    return " ".join(parts).lower()


def _match_patterns(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def classify_article(article: dict) -> dict:
    text = _search_text(article)
    categories = [
        cat for cat, patterns in POLLUTANT_CATEGORIES.items()
        if _match_patterns(text, patterns)
    ]
    is_microplastic = "微塑料" in categories
    is_emerging = bool(categories) or _match_patterns(
        text, POLLUTANT_CATEGORIES["新污染物综合"]
    )

    mp_themes = []
    if is_microplastic:
        mp_themes = [
            theme for theme, patterns in MICROPLASTIC_THEMES.items()
            if _match_patterns(text, patterns)
        ]

    return {
        "pollutant_categories": categories,
        "is_microplastic": is_microplastic,
        "is_emerging_pollutant": is_emerging,
        "microplastic_themes": mp_themes,
        "relevance_score": len(categories) + len(mp_themes),
    }


def _heat_level(count: int, total: int) -> str:
    if total == 0:
        return "低"
    ratio = count / total
    if ratio >= 0.25 or count >= 4:
        return "高"
    if ratio >= 0.12 or count >= 2:
        return "中"
    return "低"


def _pick_keyword(article: dict, theme: str) -> str:
    text = _search_text(article)
    for patterns in MICROPLASTIC_THEMES.get(theme, []):
        m = re.search(patterns, text, re.IGNORECASE)
        if m:
            return m.group(0)
    cats = article.get("pollutant_categories", [])
    return cats[0] if cats else "新污染物"


def _generate_angles(
    category: str,
    theme: str,
    articles: list[dict],
    count: int,
) -> list[str]:
    templates = WRITING_ANGLE_TEMPLATES.get(
        category, WRITING_ANGLE_TEMPLATES["default"]
    )
    sample = articles[0] if articles else {}
    keyword = _pick_keyword(sample, theme) if theme else category
    journal = sample.get("journal", "顶刊")

    angles = []
    for i, tmpl in enumerate(templates[:3]):
        angle = tmpl.format(
            subtopic=theme or category,
            keyword=keyword,
            journal=journal,
        )
        if count >= 3 and i == 0:
            angle += f"（本周已有 {count} 篇相关论文，话题热度较高）"
        angles.append(angle)
    return angles


def build_writing_brief(
    pollutant_articles: list[dict],
    microplastic_articles: list[dict],
) -> dict:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total = len(pollutant_articles)
    mp_count = len(microplastic_articles)

    # Category counts
    cat_counter: Counter = Counter()
    for a in pollutant_articles:
        for cat in a.get("pollutant_categories", []):
            cat_counter[cat] += 1

    # Microplastic sub-theme counts
    mp_theme_counter: Counter = Counter()
    for a in microplastic_articles:
        for theme in a.get("microplastic_themes", []):
            mp_theme_counter[theme] += 1

    # Group articles by category for angle generation
    by_category: dict[str, list[dict]] = defaultdict(list)
    for a in pollutant_articles:
        for cat in a.get("pollutant_categories", []):
            by_category[cat].append(a)

    by_mp_theme: dict[str, list[dict]] = defaultdict(list)
    for a in microplastic_articles:
        for theme in a.get("microplastic_themes", []) or ["微塑料综合"]:
            by_mp_theme[theme].append(a)

    # Hot themes (prioritize microplastic sub-themes, then pollutant categories)
    hot_themes = []

    for theme, count in mp_theme_counter.most_common(5):
        arts = by_mp_theme.get(theme, [])
        hot_themes.append({
            "theme": f"微塑料 · {theme}",
            "category": "微塑料",
            "article_count": count,
            "heat_level": _heat_level(count, mp_count),
            "sample_titles": [
                (a.get("title_zh") or a.get("title", ""))[:80]
                for a in arts[:3]
            ],
            "writing_angles": _generate_angles("微塑料", theme, arts, count),
        })

    for cat, count in cat_counter.most_common():
        if cat == "微塑料":
            continue
        arts = by_category.get(cat, [])
        hot_themes.append({
            "theme": cat,
            "category": cat,
            "article_count": count,
            "heat_level": _heat_level(count, total),
            "sample_titles": [
                (a.get("title_zh") or a.get("title", ""))[:80]
                for a in arts[:3]
            ],
            "writing_angles": _generate_angles(cat, "", arts, count),
        })

    hot_themes.sort(
        key=lambda t: (
            {"高": 3, "中": 2, "低": 1}[t["heat_level"]],
            t["article_count"],
        ),
        reverse=True,
    )

    # Daily writing picks (top 3 most relevant)
    ranked = sorted(
        pollutant_articles,
        key=lambda a: (a.get("is_microplastic", False), a.get("relevance_score", 0)),
        reverse=True,
    )
    daily_picks = []
    for a in ranked[:5]:
        cats = "、".join(a.get("pollutant_categories", [])[:2]) or "新污染物"
        mp_t = "、".join(a.get("microplastic_themes", [])[:2])
        angle_hint = f"微塑料/{mp_t}" if a.get("is_microplastic") else cats
        daily_picks.append({
            "title_zh": a.get("title_zh") or a.get("title", ""),
            "journal": a.get("journal", ""),
            "published": a.get("published", ""),
            "categories": a.get("pollutant_categories", []),
            "microplastic_themes": a.get("microplastic_themes", []),
            "why_write": (
                f"命中{'微塑料' if a.get('is_microplastic') else '新污染物'}热点"
                f"（{angle_hint}），具备科普/评论写作价值"
            ),
            "suggested_angle": _generate_angles(
                a.get("pollutant_categories", ["新污染物"])[0]
                if a.get("pollutant_categories")
                else "新污染物",
                (a.get("microplastic_themes") or [""])[0],
                [a],
                1,
            )[0],
            "url": a.get("url", ""),
        })

    # Overview narrative
    if mp_count == 0 and total == 0:
        overview = "本周暂无明确命中新污染物/微塑料关键词的论文，建议扩大检索范围或关注综述类文章。"
    elif mp_count >= 3:
        top_mp = mp_theme_counter.most_common(1)[0][0] if mp_theme_counter else "环境行为"
        overview = (
            f"本周共整理 {total} 篇新污染物相关文献，其中微塑料 {mp_count} 篇。"
            f"研究热点集中在「{top_mp}」，"
            f"建议优先从微塑料日常暴露、环境归趋或健康风险角度组织写作。"
        )
    else:
        top_cat = cat_counter.most_common(1)[0][0] if cat_counter else "新污染物"
        overview = (
            f"本周共整理 {total} 篇新污染物相关文献（微塑料 {mp_count} 篇）。"
            f"当前最热方向为「{top_cat}」，可结合本土案例或政策语境展开评论。"
        )

    mp_key_findings = []
    for a in microplastic_articles[:4]:
        title = a.get("title_zh") or a.get("title", "")
        themes = "、".join(a.get("microplastic_themes", [])) or "综合"
        mp_key_findings.append(f"【{themes}】{title[:60]}")

    return {
        "date": today,
        "overview": overview,
        "stats": {
            "total_pollutant": total,
            "microplastic": mp_count,
            "categories": dict(cat_counter),
            "microplastic_themes": dict(mp_theme_counter),
        },
        "hot_themes": hot_themes[:8],
        "microplastic_summary": {
            "count": mp_count,
            "top_themes": [
                {"theme": t, "count": c}
                for t, c in mp_theme_counter.most_common(5)
            ],
            "key_findings": mp_key_findings,
            "recommended_angles": _generate_angles(
                "微塑料",
                mp_theme_counter.most_common(1)[0][0]
                if mp_theme_counter
                else "环境行为",
                microplastic_articles,
                mp_count,
            ) if mp_count else [],
        },
        "daily_picks": daily_picks,
    }


def analyze_articles(articles: list[dict]) -> dict:
    """Tag articles and build pollutant digest + writing brief."""
    tagged = []
    for article in articles:
        tags = classify_article(article)
        tagged.append({**article, **tags})

    pollutant_articles = [
        a for a in tagged if a.get("is_emerging_pollutant")
    ]
    microplastic_articles = [
        a for a in tagged if a.get("is_microplastic")
    ]

    writing_brief = build_writing_brief(
        pollutant_articles, microplastic_articles
    )

    return {
        "articles": tagged,
        "digest": {
            "pollutant_count": len(pollutant_articles),
            "microplastic_count": len(microplastic_articles),
            "pollutant_articles": [
                {
                    "doi": a.get("doi"),
                    "title_zh": a.get("title_zh"),
                    "journal": a.get("journal"),
                    "published": a.get("published"),
                    "pollutant_categories": a.get("pollutant_categories"),
                    "microplastic_themes": a.get("microplastic_themes"),
                    "url": a.get("url"),
                }
                for a in pollutant_articles
            ],
            "writing_brief": writing_brief,
        },
    }
