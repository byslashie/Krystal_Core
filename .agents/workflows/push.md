---
description: Git Push - 將本地變更推送至遠端倉庫
---

此工作流程會自動將本地所有變更 commit 並 push 至遠端倉庫。

## 流程步驟

1. 確認目前 Git 狀態並新增至暫存區

```bash
git status
git add .
```

2. 建立新分支（依據當前時間自動動態產生）

```bash
BRANCH_NAME="feat/update-$(date +'%Y%m%d-%H%M')"
git checkout -b $BRANCH_NAME
```

3. 提交變更並推送至遠端倉庫

```bash
git commit -m "feat: update $(date +'%Y-%m-%d %H:%M')"
git push -u origin $BRANCH_NAME
```

4. 確認推送結果

```bash
git log --oneline -5
```
