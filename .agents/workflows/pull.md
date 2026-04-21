---
description: Git Pull - 從遠端倉庫拉取最新變更
---

此工作流程會從遠端倉庫拉取最新變更並合併至本地分支。

## 流程步驟

1. 獲取遠端所有最新狀態

```bash
git fetch --all
```

2. 自動尋找遠端最新更新的分支，並切換、拉取（解決跨裝置同步問題）

```bash
LATEST_BRANCH=$(git branch -r --sort=-committerdate | grep -v HEAD | head -n 1 | sed 's/origin\///' | xargs)
if [ -n "$LATEST_BRANCH" ]; then
    echo "最新分支為: $LATEST_BRANCH，正在切換與拉取..."
    git checkout $LATEST_BRANCH
    git pull origin $LATEST_BRANCH
else
    echo "找不到帶有的時間戳分支，使用預設定拉取。"
    git pull origin HEAD
fi
```

3. 確認最新 log

```bash
git log --oneline -5
```
