let allArticles = [];
let digest = null;
let currentFilter = "all";

async function loadArticles() {
  const loading = document.getElementById("loading");
  const empty = document.getElementById("empty");

  try {
    const resp = await fetch("data/articles.json");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    allArticles = data.articles || [];
    digest = data.digest || null;

    const updated = data.updated_at
      ? new Date(data.updated_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })
      : "未知";
    document.getElementById("update-time").textContent = `最后更新：${updated}（北京时间）`;

    loading.classList.add("hidden");
    renderWritingBrief();

    if (allArticles.length === 0) {
      empty.classList.remove("hidden");
    } else {
      renderArticles();
    }
  } catch (err) {
    loading.textContent = "加载失败，请确认 data/articles.json 是否存在。";
    console.error(err);
  }
}

function renderWritingBrief() {
  const section = document.getElementById("writing-brief");
  if (!digest?.writing_brief) {
    section.classList.add("hidden");
    return;
  }

  const brief = digest.writing_brief;
  const stats = brief.stats || {};

  section.classList.remove("hidden");
  section.innerHTML = `
    <div class="brief-header">
      <h2>📝 今日写作主题风向</h2>
      <span class="brief-date">${escapeHtml(brief.date || "")}</span>
    </div>
    <p class="brief-overview">${escapeHtml(brief.overview)}</p>

    <div class="stats-row">
      <div class="stat-chip">新污染物 <strong>${stats.total_pollutant ?? digest.pollutant_count ?? 0}</strong> 篇</div>
      <div class="stat-chip mp">微塑料 <strong>${stats.microplastic ?? digest.microplastic_count ?? 0}</strong> 篇</div>
    </div>

    ${renderHotThemes(brief.hot_themes || [])}
    ${renderDailyPicks(brief.daily_picks || [])}
    ${renderMicroplasticSummary(brief.microplastic_summary)}
  `;
}

function renderHotThemes(themes) {
  if (!themes.length) return "";
  return `
    <div class="brief-section">
      <h3>热点主题</h3>
      <div class="theme-grid">
        ${themes
          .map(
            (t) => `
          <div class="theme-card heat-${t.heat_level === "高" ? "high" : t.heat_level === "中" ? "mid" : "low"}">
            <div class="theme-card-header">
              <span class="theme-name">${escapeHtml(t.theme)}</span>
              <span class="heat-badge">${escapeHtml(t.heat_level)}热度 · ${t.article_count}篇</span>
            </div>
            <ul class="angle-list">
              ${(t.writing_angles || []).map((a) => `<li>${escapeHtml(a)}</li>`).join("")}
            </ul>
          </div>`
          )
          .join("")}
      </div>
    </div>`;
}

function renderDailyPicks(picks) {
  if (!picks.length) return "";
  return `
    <div class="brief-section">
      <h3>推荐写作选题</h3>
      <div class="picks-list">
        ${picks
          .slice(0, 5)
          .map(
            (p, i) => `
          <div class="pick-card">
            <div class="pick-num">${i + 1}</div>
            <div class="pick-body">
              <div class="pick-meta">
                <span class="journal-badge ${p.journal}">${escapeHtml(p.journal)}</span>
                ${(p.categories || []).map((c) => `<span class="tag">${escapeHtml(c)}</span>`).join("")}
              </div>
              <h4>${escapeHtml(p.title_zh)}</h4>
              <p class="pick-why">${escapeHtml(p.why_write)}</p>
              <p class="pick-angle">💡 ${escapeHtml(p.suggested_angle)}</p>
              ${p.url ? `<a class="doi-link" href="${escapeHtml(p.url)}" target="_blank" rel="noopener">阅读原文 →</a>` : ""}
            </div>
          </div>`
          )
          .join("")}
      </div>
    </div>`;
}

function renderMicroplasticSummary(summary) {
  if (!summary?.count) return "";
  return `
    <div class="brief-section mp-section">
      <h3>微塑料专题摘要</h3>
      <div class="mp-themes">
        ${(summary.top_themes || [])
          .map((t) => `<span class="tag mp-tag">${escapeHtml(t.theme)} (${t.count})</span>`)
          .join("")}
      </div>
      ${summary.key_findings?.length ? `<ul class="findings-list">${summary.key_findings.map((f) => `<li>${escapeHtml(f)}</li>`).join("")}</ul>` : ""}
    </div>`;
}

function filterArticles() {
  switch (currentFilter) {
    case "pollutant":
      return allArticles.filter((a) => a.is_emerging_pollutant);
    case "microplastic":
      return allArticles.filter((a) => a.is_microplastic);
    case "all":
      return allArticles;
    default:
      return allArticles.filter((a) => a.journal === currentFilter);
  }
}

function renderArticles() {
  const container = document.getElementById("articles");
  const filtered = filterArticles();
  const empty = document.getElementById("empty");

  if (filtered.length === 0) {
    container.innerHTML = "";
    empty.classList.remove("hidden");
    empty.textContent = "该分类下暂无文章";
    return;
  }
  empty.classList.add("hidden");
  container.innerHTML = filtered.map(renderCard).join("");
}

function renderCard(article) {
  const pubDate = article.published || "日期未知";
  const abstractZh = article.abstract_zh || "（暂无摘要）";
  const abstractEn = article.abstract || "（No abstract available）";
  const tags = [
    ...(article.pollutant_categories || []),
    ...(article.microplastic_themes || []).map((t) => `MP·${t}`),
  ];

  return `
    <article class="article-card ${article.is_microplastic ? "is-mp" : ""}">
      <div class="card-header">
        <span class="journal-badge ${article.journal}">${article.journal}</span>
        <span class="pub-date">${pubDate}</span>
        ${tags.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join("")}
      </div>
      <h2 class="title-zh">${escapeHtml(article.title_zh || article.title)}</h2>
      <p class="title-en">${escapeHtml(article.title)}</p>
      <div class="abstract-block">
        <div class="abstract-label">摘要 · 中文</div>
        <p class="abstract-zh">${escapeHtml(abstractZh)}</p>
      </div>
      <div class="abstract-block">
        <div class="abstract-label">Abstract · English</div>
        <p class="abstract-en">${escapeHtml(abstractEn)}</p>
      </div>
      ${
        article.url
          ? `<div class="card-footer"><a class="doi-link" href="${escapeHtml(article.url)}" target="_blank" rel="noopener">查看原文 →</a></div>`
          : ""
      }
    </article>`;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

document.getElementById("filter-bar").addEventListener("click", (e) => {
  const btn = e.target.closest(".filter-btn");
  if (!btn) return;

  document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  currentFilter = btn.dataset.filter;
  renderArticles();
});

loadArticles();
