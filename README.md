# 期刊速递 · NC / EST / JHM

每日自动抓取以下三本期刊的最新文章，整理新污染物/微塑料专题，并提供中文翻译与写作风向。

| 缩写 | 期刊 |
|------|------|
| **NC** | Nature Communications |
| **EST** | Environmental Science & Technology |
| **JHM** | Journal of Hazardous Materials |

**网站：** https://johnchew1.github.io/journal-digest/

## 每周推送（零配置）

每周一 **09:00（北京时间）** 自动创建 GitHub 周报 Issue，GitHub 会发邮件到你的注册邮箱（**无需 SMTP、无需应用密码**）。

### 只需 2 步（一次性，约 1 分钟）

**1. 关注仓库**

打开 https://github.com/johnchew1/journal-digest ，点击右上角 **Watch → All Activity**

**2. 开启 Issue 邮件通知**

打开 https://github.com/settings/notifications ，在 **Email** 区域勾选 **Issues**。

确认 GitHub 绑定邮箱为 `zihanzhou1705@outlook.com`：  
https://github.com/settings/emails

**手动测试：** Actions → Weekly Digest Push → Run workflow

**历史周报：** https://github.com/johnchew1/journal-digest/issues?q=label%3Aweekly-digest

## 本地运行

```bash
pip install -r requirements.txt
python scripts/fetch_articles.py
python scripts/weekly_digest.py    # 预览周报
cd public && python -m http.server 8080
```

## 自动更新

- 每天 16:00（北京时间）：抓取新文章
- 每周一 09:00（北京时间）：推送周报 Issue

## 数据来源

- 文章元数据：[CrossRef API](https://api.crossref.org/)
- 中文翻译：Google Translate（deep-translator）

## 目录结构

```
journal-digest/
├── public/
│   ├── index.html
│   ├── data/articles.json
│   └── weekly/latest.md
├── scripts/
│   ├── fetch_articles.py
│   ├── pollutant_analyzer.py
│   └── weekly_digest.py
└── .github/workflows/
    ├── daily-update.yml
    ├── deploy-pages.yml
    └── weekly-digest.yml
```
