const JOURNAL_COLORS = { NC: "#c0392b", EST: "#2980b9", JHM: "#27ae60" };

let allArticles = [];
let currentFilter = "all";

async function loadArticles() {
  const loading = document.getElementById("loading");
  const empty = document.getElementById("empty");

  try {
    const resp = await fetch("data/articles.json");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    allArticles = data.articles || [];
    const updated = data.updated_at
      ? new Date(data.updated_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })
      : "未知";
    document.getElementById("update-time").textContent = `最后更新：${updated}（北京时间）`;

    loading.classList.add("hidden");
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

function renderArticles() {
  const container = document.getElementById("articles");
  const filtered =
    currentFilter === "all"
      ? allArticles
      : allArticles.filter((a) => a.journal === currentFilter);

  container.innerHTML = filtered.map(renderCard).join("");
}

function renderCard(article) {
  const badgeClass = article.journal;
  const pubDate = article.published || "日期未知";
  const abstractZh = article.abstract_zh || "（暂无摘要）";
  const abstractEn = article.abstract || "（No abstract available）";

  return `
    <article class="article-card">
      <div class="card-header">
        <span class="journal-badge ${badgeClass}">${article.journal}</span>
        <span class="pub-date">${pubDate}</span>
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
    </article>
  `;
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
