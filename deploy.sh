#!/usr/bin/env bash
# 服务器一键部署：对齐原先「拉最新代码 + docker compose up --build -d」
# 用法（在仓库目录内）：
#   export GITHUB_TOKEN=你的token   # 私有仓库需要；不要把 token 写进本文件
#   ./deploy.sh
set -euo pipefail

cd "$(dirname "$0")"

if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  git fetch "https://${GITHUB_USER:-CwjXFH}:${GITHUB_TOKEN}@github.com/CwjXFH/CalendarSite.git" master
  git reset --hard FETCH_HEAD
else
  git fetch origin
  git reset --hard origin/master
fi

docker compose up --build -d
