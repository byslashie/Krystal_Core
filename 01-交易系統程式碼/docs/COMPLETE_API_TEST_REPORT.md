# 完整 API 测试报告
**测试日期**: 2026-03-09
**测试工具**: test_api.py, test_api_detailed.py, test_api_comprehensive.py
**Flask应用**: app_simple.py
**测试环境**: Windows 11 Pro, Python 3.11

---

## 执行摘要

完整的 API 测试已执行完毕。测试发现系统中存在 **2 个 Flask 实例**同时运行，导致部分路由在不同端口上的行为不一致。

| 指标 | 值 |
|------|-----|
| **运行的 Flask 实例** | 2 个 (端口 5010 和 9999) |
| **测试的 API 端点** | 13 个 |
| **全局成功率** | 23.1% (端口9999) / 15.4% (端口5010) |
| **完全可用端点** | 3 个 (status, holdings, metrics) |
| **部分失败端点** | 7 个 (404 Not Found) |
| **性能问题端点** | 3 个 (Read Timeout) |

---

## 详细测试结果

### 测试环境信息
```
Flask 应用监听端口:
  - 端口 5010: app_html_flask.py.bak 或其他实例
  - 端口 9999: app_simple.py (主应用)

Google Sheets 连接: ✅ 成功
Sheet ID: 1zpehl1bAZitFiQqMg7IcGWsPQxdhn...
Ship监测模块: ✅ 已启用
Intel Engine模块: ✅ 已启用
```

### 端口 9999 (推荐使用) - 成功率 23.1%

#### ✅ 完全成功的端点 (3/13)

| # | 端点 | 描述 | 状态码 | 数据量 | 功能状态 |
|---|------|------|---------|--------|----------|
| 1 | `/api/status` | 系统状态 | 200 | - | ✅ 运行正常 |
| 2 | `/api/holdings` | 持仓列表 | 200 | 9 条 | ✅ 正确读取 |
| 3 | `/api/metrics` | 绩效指标 | 200 | - | ✅ 已实现 |

**成功示例响应**:
```json
{
  "count": 9,
  "data": [
    {
      "symbol": "QQQ",
      "shares": 100,
      "price": 450.50,
      "value": 45050.00
    }
    // ... 8 more holdings
  ],
  "source": "sheets",
  "status": "success",
  "timestamp": "2026-03-09T16:28:50.289526"
}
```

#### ❌ 返回 404 的端点 (7/13)

这些端点虽然在源代码中定义了路由和处理函数，但在运行的 Flask 应用中无法访问，导致 404 错误。

| # | 端点 | 描述 | 问题 |
|---|------|------|------|
| 1 | `/api/strategies` | 策略管理 | 404 Not Found |
| 2 | `/api/strategies/performance` | 策略绩效 | 404 Not Found |
| 3 | `/api/risk-metrics` | 风控指标 | 404 Not Found |
| 4 | `/api/intel/events` | Intel事件 | 404 Not Found |
| 5 | `/api/risk-incidents` | 风控日志 | 404 Not Found |
| 6 | `/api/macro-state` | 宏观状态 | 404 Not Found |
| 7 | `/api/intel/usgs` | USGS地震 | 404 Not Found |

**分析**: 在源代码 app_simple.py 中，这些路由的定义位置为：
- 行 842: `@app.route('/api/strategies', methods=['GET'])`
- 行 897: `@app.route('/api/strategies/performance', methods=['GET'])`
- 行 1021: `@app.route('/api/risk-metrics', methods=['GET'])`
- 行 1074: `@app.route('/api/intel/events', methods=['GET'])`
- 行 1104: `@app.route('/api/risk-incidents', methods=['GET'])`
- 行 1134: `@app.route('/api/macro-state', methods=['GET'])`
- 行 1164: `@app.route('/api/intel/usgs', methods=['GET'])`

**可能原因**:
1. Flask 调试器 (`debug=True`) 的热重载机制导致部分路由未被加载
2. 导入错误或异常被吞掉，路由注册失败
3. Python 虚拟环境或模块缓存问题
4. 旧的 .pyc 文件干扰

#### ⏱ 读取超时的端点 (3/13)

这些端点存在但响应时间超过 5 秒，导致请求超时。

| # | 端点 | 描述 | 超时原因 |
|---|------|------|---------|
| 1 | `/api/intel/shadow-fleet` | 影子舰队监测 | 外部 API 调用缓慢或数据量大 |
| 2 | `/api/intel/oil-shock` | 油价冲击指标 | 复杂数据聚合计算 |
| 3 | `/api/ship-monitoring/statistics` | 油轮统计数据 | 大量 AIS 数据处理 |

**分析**: 响应时间 > 10 秒（测试超时时间为 5-10 秒）

---

## 问题诊断

### 问题 1: 404 Not Found 错误

**现象**: 7 个端点返回 HTTP 404，表示路由未找到

**根本原因分析**:

检查 Flask 应用的路由注册机制：
```bash
# 从 app_simple.py 获取注册的路由列表
from app_simple import app
for rule in app.url_map.iter_rules():
    if 'api' in str(rule):
        print(rule)  # 输出显示这些路由确实已注册!
```

**调查发现**: 路由在 Python 程序中确实被注册了，但 Flask 服务器返回 404。这表示：
- 可能是多个 Flask 实例之间的干扰
- 调试模式热重载导致的路由丢失
- 应用启动时的错误处理问题

### 问题 2: Read Timeout (ReadTimeout) 错误

**现象**: 3 个端点在 5-10 秒内无法响应

**性能分析**:
```
/api/intel/shadow-fleet    → 阻塞在外部 API 调用 (可能调用 AIS/海洋数据服务)
/api/intel/oil-shock       → 阻塞在数据处理 (可能涉及复杂的经济指标计算)
/api/ship-monitoring/statistics → 阻塞在数据聚合 (可能处理大量 AIS 数据)
```

**根本原因**:
- 这些端点调用了外部 API，但没有正确的超时设置或缓存
- Google Sheets API 响应缓慢
- 同步操作阻塞了 Flask 线程

### 问题 3: 双端口现象

**发现**: 系统中存在 2 个 Flask 实例同时运行
- 端口 5010: 可能是旧版本或测试版本
- 端口 9999: 当前正在测试的 app_simple.py

**影响**: 可能导致混淆，建议关闭不需要的实例

---

## 代码级别问题分析

### 缺失的实现

在 app_simple.py 的第 846-850 行：
```python
@app.route('/api/strategies', methods=['GET'])
def api_strategies():
    try:
        from sheets_utils import read_strategies, read_daily_nav, read_trades
        # ...
```

这些函数依赖 `sheets_utils` 模块，可能存在以下问题：
1. `sheets_utils.py` 不存在或不可访问
2. 导入失败被吃掉，未被记录
3. Google Sheets 连接失败导致函数无法完成初始化

### 超时问题的代码位置

第 799-825 行的影子舰队和油价冲击端点：
```python
@app.route('/api/intel/shadow-fleet')
def api_intel_shadow_fleet():
    if not INTEL_ENGINE_OK:
        return jsonify({'status': 'error', 'message': 'Intel engine not initialized'}), 500
    # ... 需要调查这里的处理逻辑
```

---

## 建议的修复方案

### 优先级 1 - 紧急修复 (影响可用性)

#### 1.1 修复 404 错误
```bash
# 步骤 1: 清理 Python 缓存
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete

# 步骤 2: 重启 Flask 应用（关闭调试模式）
python app_simple.py  # 移除 debug=True
```

#### 1.2 验证 sheets_utils 模块
```python
# 测试 sheets_utils 是否正常工作
from sheets_utils import read_strategies, read_daily_nav
print(read_strategies())  # 应该返回 DataFrame
```

#### 1.3 检查路由装饰器
```python
# 确保没有条件语句阻止路由注册
# 现在: @app.route(...) if CONDITION else lambda: None  ❌
# 应该: @app.route(...) 然后在函数内部检查
```

### 优先级 2 - 性能优化

#### 2.1 为超时端点添加缓存
```python
from functools import lru_cache
import time

# 添加 5 分钟缓存
CACHE_DURATION = 300

@app.route('/api/intel/shadow-fleet')
def api_intel_shadow_fleet():
    # 实现缓存机制
    cache_key = 'shadow_fleet'
    if cache_key in cache and time.time() - cache[cache_key]['time'] < CACHE_DURATION:
        return jsonify(cache[cache_key]['data'])

    # 否则获取新数据
    data = fetch_shadow_fleet_data()
    cache[cache_key] = {'data': data, 'time': time.time()}
    return jsonify(data)
```

#### 2.2 增加超时限制
```python
# 在测试时增加超时时间
requests.get(url, timeout=30)  # 从 5 秒增加到 30 秒
```

#### 2.3 实现异步处理
```python
# 对于耗时操作，使用后台任务
from celery import Celery

@app.route('/api/intel/shadow-fleet')
def api_intel_shadow_fleet():
    # 立即返回，后台处理数据
    task = process_shadow_fleet.delay()
    return jsonify({'status': 'processing', 'task_id': task.id})
```

### 优先级 3 - 测试和文档

#### 3.1 添加单元测试
```python
import unittest

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_strategies_endpoint(self):
        response = self.app.get('/api/strategies')
        self.assertEqual(response.status_code, 200)
```

#### 3.2 添加集成测试
```bash
# 创建集成测试脚本
python test_api_comprehensive.py  # 已创建
```

#### 3.3 API 文档
```markdown
# API 文档

## 可用的端点

### 成功的端点
- GET /api/status - 系统状态 (✅ 200)
- GET /api/holdings - 持仓列表 (✅ 200)
- GET /api/metrics - 绩效指标 (✅ 200)

### 需要修复的端点
- GET /api/strategies - 策略管理 (❌ 404)
- ... (其他)

### 超时的端点
- GET /api/intel/shadow-fleet - 影子舰队 (⏱ Timeout)
- ... (其他)
```

---

## 测试脚本使用指南

### 基础测试
```bash
# 运行基础测试
python test_api.py

# 运行详细测试（显示响应内容）
python test_api_detailed.py

# 运行综合测试（测试所有端口）
python test_api_comprehensive.py
```

### 单个端点测试
```bash
# 测试 /api/status
curl http://localhost:9999/api/status

# 测试 /api/holdings
curl http://localhost:9999/api/holdings | python -m json.tool

# 测试特定端点并显示详细错误
curl -v http://localhost:9999/api/strategies
```

### 性能测试
```bash
# 测试单个端点的响应时间
time curl http://localhost:9999/api/holdings

# 并发测试（需要 ab 工具）
ab -n 100 -c 10 http://localhost:9999/api/status
```

---

## 文件清单

已生成的测试文件：
- ✅ `test_api.py` - 基础 API 测试脚本
- ✅ `test_api_detailed.py` - 详细测试脚本（显示响应）
- ✅ `test_api_comprehensive.py` - 综合测试脚本（多端口）
- ✅ `API_TEST_RESULTS.md` - 初步测试报告
- ✅ `COMPLETE_API_TEST_REPORT.md` - 本文档（完整报告）
- ✅ `app_output.log` - Flask 应用日志
- ✅ `app_output_new.log` - Flask 重启后日志

---

## 技术栈验证结果

| 组件 | 状态 | 说明 |
|------|------|------|
| Flask 服务器 | ✅ 运行 | 端口 9999 正常监听 |
| Google Sheets | ✅ 连接 | 成功读取 broker_positions (9 条) |
| Ship监测模块 | ✅ 加载 | vessel_tracker 已初始化 |
| Intel Engine | ✅ 加载 | ShadowFleetMonitor 已初始化 |
| Python环境 | ✅ 正确 | 3.11.9 + 所需库 |
| 虚拟环境 | ✅ 启用 | .venv/Scripts/python |

---

## 附录：详细端点说明

### 第一层 - 情报与总经感知
- `GET /api/intel/events` - 获取情报事件列表 (⚠️ 404)
- `GET /api/intel/shadow-fleet` - 获取影子舰队数据 (⏱ Timeout)
- `GET /api/intel/oil-shock` - 获取油价冲击指标 (⏱ Timeout)
- `GET /api/intel/usgs` - 获取 USGS 地震数据 (⚠️ 404)
- `GET /api/macro-state` - 获取宏观经济状态 (⚠️ 404)

### 第二层 - 决策与风控
- `GET /api/risk-metrics` - 获取风控指标 (⚠️ 404)
- `GET /api/risk-incidents` - 获取风控事件 (⚠️ 404)
- `POST /api/risk/check` - 检查风控规则

### 第三层 - 交易与绩效
- `GET /api/strategies` - 获取策略列表 (⚠️ 404)
- `GET /api/strategies/performance` - 获取策略绩效 (⚠️ 404)
- `GET /api/metrics` - 获取投资组合指标 (✅ 200)
- `POST /api/trades/update` - 更新交易记录

### 第四层 - 券商事实
- `GET /api/holdings` - 获取持仓列表 (✅ 200)
- `GET /api/status` - 获取系统状态 (✅ 200)
- `GET /api/debug` - 获取调试信息
- `GET /api/chart-data` - 获取图表数据

### 波斯湾油轮监测
- `GET /api/ship-monitoring/vessels` - 油轮列表
- `GET /api/ship-monitoring/alerts` - 油轮警报
- `GET /api/ship-monitoring/statistics` - 油轮统计 (⏱ Timeout)
- `GET /api/ship-monitoring/waiting-vessels` - 等待中的油轮

---

## 测试结论

### 系统可用性评估
- **生产环境就绪**: ❌ 否
- **开发环境可用**: ✅ 部分可用
- **关键功能**: ⚠️ 部分实现

### 立即行动项
1. [ ] 调查 404 错误的根本原因（路由未找到）
2. [ ] 修复 sheets_utils 导入问题
3. [ ] 优化长时间运行的端点
4. [ ] 实现缓存机制
5. [ ] 关闭不需要的 Flask 实例（端口 5010）

### 后续建议
1. 实施完整的单元测试覆盖
2. 添加 API 文档（Swagger/OpenAPI）
3. 实现请求日志和性能监控
4. 添加速率限制和认证机制
5. 部署到生产环境前进行性能测试

---

**报告生成时间**: 2026-03-09 16:40:00 UTC
**测试执行者**: Claude Code AI
**下一步行动**: 根据优先级修复所有已发现的问题
