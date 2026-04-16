---
description: Git Push - 將本地變更推送至遠端倉庫
---

此工作流程會自動將本地所有變更 commit 並 push 至遠端倉庫。

## 流程步驟

1. 確認目前 Git 狀態

```powershell
cd c:\Projects\Krystal_完整系統; git status
```

2. 新增所有變更至暫存區

```powershell
cd c:\Projects\Krystal_完整系統; git add .
```

3. 建立新分支（格式：feat/功能名稱 或 fix/修復編號），請將 `feat/update-$(Get-Date -Format 'yyyyMMdd-HHmm')` 替換為實際分支名稱（若已在正確分支則跳過此步驟）

```powershell
cd c:\Projects\Krystal_完整系統; git checkout -b feat/update-$(Get-Date -Format 'yyyyMMdd-HHmm')
```

4. 提交變更（請將 commit 訊息替換為描述本次變更的內容）

```powershell
cd c:\Projects\Krystal_完整系統; git commit -m "feat: update $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
```

5. 推送至遠端倉庫

```powershell
cd c:\Projects\Krystal_完整系統; git push origin HEAD
```

6. 確認推送結果

```powershell
cd c:\Projects\Krystal_完整系統; git log --oneline -5
```
