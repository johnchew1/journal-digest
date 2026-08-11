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

## 每周邮件推送

每周一 **09:00（北京时间）** 自动将过去一周精简整理的内容发送到 `zihanzhou1705@outlook.com`。

邮件内容包括：
- 新污染物/微塑料写作风向总览
- 热点主题与写作角度
- 推荐写作选题
- 微塑料文献精选

### 配置邮件（一次性设置）

在 GitHub 仓库 **Settings → Secrets and variables → Actions** 中添加：

| Secret | 值 | 说明 |
|--------|-----|------|
| `SMTP_HOST` | `smtp.office365.com` | Outlook 发件服务器 |
| `SMTP_PORT` | `587` | TLS 端口 |
| `SMTP_USER` | 你的 Outlook 邮箱 | 发件账号 |
| `SMTP_PASSWORD` | 应用密码 | 见下方说明 |

**获取 Outlook 应用密码：**
1. 登录 [Microsoft 账户安全页](https://account.microsoft.com/security)
2. 开启两步验证（如未开启）
3. 创建「应用密码」，复制 16 位密码填入 `SMTP_PASSWORD`

**本地测试：**
```bash
DRY_RUN=1 python scripts/weekly_email.py          # 预览内容
SMTP_USER=... SMTP_PASSWORD=... python scripts/weekly_email.py  # 实际发送
```

**手动触发：** GitHub → Actions → Weekly Email Digest → Run workflow

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
│   ├── fetch_articles.py
│   ├── pollutant_analyzer.py
│   ├── regenerate_digest.py
│   └── weekly_email.py
└── .github/workflows/
    ├── daily-update.yml
    ├── deploy-pages.yml
    └── weekly-email.yml
```
