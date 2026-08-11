#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GH="$ROOT/.bin/gh_2.97.0_macOS_arm64/bin/gh"

if ! "$GH" auth status &>/dev/null; then
  echo "请先登录 GitHub："
  echo "  $GH auth login --web"
  exit 1
fi

cd "$ROOT"

REPO_NAME="journal-digest"
if "$GH" repo view "$REPO_NAME" &>/dev/null; then
  echo "仓库已存在，直接推送..."
  git remote remove origin 2>/dev/null || true
  git remote add origin "https://github.com/$("$GH" api user -q .login)/$REPO_NAME.git"
else
  echo "创建 GitHub 仓库..."
  "$GH" repo create "$REPO_NAME" --public --source=. --remote=origin --description="Daily digest of NC, EST, JHM journal articles with Chinese translations"
fi

git push -u origin main

echo ""
echo "启用 GitHub Pages..."
"$GH" api repos/"$("$GH" api user -q .login)"/"$REPO_NAME"/pages \
  -X POST \
  -f build_type=workflow \
  -f source[branch]=main \
  -f source[path]=/ 2>/dev/null || echo "Pages 可能已启用，跳过"

echo ""
echo "触发首次部署..."
git push origin main

echo ""
echo "完成！网站将在几分钟后上线："
"$GH" api repos/"$("$GH" api user -q .login)"/"$REPO_NAME"/pages -q .html_url 2>/dev/null || echo "  https://<your-username>.github.io/journal-digest/"
