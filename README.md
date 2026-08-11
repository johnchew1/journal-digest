# 期刊速递 · NC / EST / JHM

每日自动抓取以下三本期刊的最新文章，并提供中文翻译：

| 缩写 | 期刊 |
|------|------|
| **NC** | Nature Communications |
| **EST** | Environmental Science & Technology |
| **JHM** | Journal of Hazardous Materials |

## 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 抓取文章并翻译（约需 2-5 分钟）
python scripts/fetch_articles.py

# 启动本地网站
cd public && python -m http.server 8080
```

浏览器访问 http://localhost:8080

## 自动更新

项目包含 GitHub Actions 工作流（`.github/workflows/daily-update.yml`），每天北京时间 16:00 自动运行抓取脚本并提交更新。

部署到 GitHub Pages 后，网站会自动展示最新数据：

1. 推送代码到 GitHub
2. 在仓库 Settings → Pages 中，Source 选择 **GitHub Actions** 或 **Deploy from branch**（`main` / `public` 目录）

## 数据来源

- 文章元数据：[CrossRef API](https://api.crossref.org/)
- 中文翻译：Google Translate（通过 deep-translator）

## 目录结构

```
journal-digest/
├── public/           # 静态网站
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── data/
│       └── articles.json
├── scripts/
│   └── fetch_articles.py
└── .github/workflows/
    └── daily-update.yml
```
