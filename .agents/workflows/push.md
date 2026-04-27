---
description: Git Push - 將本地變更推送至遠端倉庫
---

此工作流程會自動將本地所有變更 commit 並 push 至遠端倉庫。

## 流程步驟

1. 確認目前 Git 狀態並新增至暫存區

```bash
git status
git add -A
```

2. 提交變更（若已有未推送 commit 則跳過此步驟）

```bash
git commit -m "feat: update $(date +'%Y-%m-%d %H:%M')"
```

3. 推送至遠端（直接推送當前分支，不建立新分支）

```bash
git push origin HEAD
```

4. 確認推送結果

```bash
git log --oneline -5
```
