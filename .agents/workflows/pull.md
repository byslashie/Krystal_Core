---
description: Git Pull - 從遠端倉庫拉取最新變更
---

此工作流程會從遠端倉庫拉取最新變更並合併至本地分支。

## 流程步驟

1. 確認目前 Git 狀態（確保本地無未儲存的衝突變更）

```powershell
cd c:\Projects\Krystal_完整系統; git status
```

2. 暫存本地未提交的變更（若有未提交變更）

```powershell
cd c:\Projects\Krystal_完整系統; git stash
```

3. 從遠端拉取最新變更

```powershell
cd c:\Projects\Krystal_完整系統; git pull origin $(git rev-parse --abbrev-ref HEAD)
```

4. 還原暫存的本地變更（若步驟 2 有執行 stash）

```powershell
cd c:\Projects\Krystal_完整系統; git stash pop
```

5. 確認最新 log

```powershell
cd c:\Projects\Krystal_完整系統; git log --oneline -5
```
