# 完整 API 测试报告
**生成时间**: 2026-03-09 16:28:50
**应用版本**: app_simple.py
**运行端口**: http://localhost:9999

---

## 测试总结

| 指标 | 数值 |
|------|------|
| **总端点数** | 13 |
| **成功端点** | 3 ✓ |
| **失败端点** | 10 ✗ |
| **成功率** | 23.1% |

---

## 详细测试结果

### ✅ 成功的端点 (3/13)

#### 1. **系统状态** - `/api/status`
- **状态码**: 200
- **描述**: 获取系统运行状态
- **响应**:
  ```json
  {
    "app": "running",
    "sheets": true,
    "timestamp": "2026-03-09T16:28:50.289526"
  }
  ```
- **功能**: ✅ 正常运行

#### 2. **持仓列表** - `/api/holdings`
- **状态码**: 200
- **描述**: 获取当前持仓数据
- **响应统计**:
  - 数据条数: 9
  - 来源: Google Sheets (broker_positions)
  - 包含数据: NASDAQ (QQQ, ACWX, MU, SNDK) 和台股 (50, 6208, 3158) 等
- **功能**: ✅ 成功从 Google Sheets 读取真实持仓数据

#### 3. **绩效指标** - `/api/metrics`
- **状态码**: 200
- **描述**: 获取投资组合绩效指标
- **响应**: 包含 data 和 status 字段
- **功能**: ✅ 成功读取绩效数据

---

### ❌ 失败的端点 (10/13)

#### 类型 1: 路由未注册 (404 错误) - 7 个端点

这些端点返回 404 错误，表示路由定义未在 Flask 应用中正确注册。

1. **策略管理** - `/api/strategies`
   - 状态码: 404
   - 问题: 路由未定义
   - 预期功能: 获取策略列表

2. **策略绩效** - `/api/strategies/performance`
   - 状态码: 404
   - 问题: 路由未定义
   - 预期功能: 获取策略绩效数据

3. **风控指标** - `/api/risk-metrics`
   - 状态码: 404
   - 问题: 路由未定义
   - 预期功能: 获取风险控制指标

4. **Intel事件** - `/api/intel/events`
   - 状态码: 404
   - 问题: 路由未定义
   - 预期功能: 获取情报事件

5. **风控日志** - `/api/risk-incidents`
   - 状态码: 404
   - 问题: 路由未定义
   - 预期功能: 获取风控事件日志

6. **宏观状态** - `/api/macro-state`
   - 状态码: 404
   - 问题: 路由未定义
   - 预期功能: 获取宏观经济状态

7. **USGS地震** - `/api/intel/usgs`
   - 状态码: 404
   - 问题: 路由未定义
   - 预期功能: 获取 USGS 地震数据

#### 类型 2: 读取超时 (ReadTimeout) - 3 个端点

这些端点存在但在 10 秒超时内未能完成响应，表示可能的性能问题或阻塞操作。

8. **影子舰队** - `/api/intel/shadow-fleet`
   - 异常: ReadTimeout (read timeout=10)
   - 问题: 端点响应时间过长（可能涉及复杂数据处理或外部 API 调用）
   - 预期功能: 获取影子舰队监测数据

9. **油价冲击** - `/api/intel/oil-shock`
   - 异常: ReadTimeout (read timeout=10)
   - 问题: 端点响应时间过长（可能涉及复杂数据处理或外部 API 调用）
   - 预期功能: 获取油价冲击指标

10. **油轮统计** - `/api/ship-monitoring/statistics`
    - 异常: ReadTimeout (read timeout=10)
    - 问题: 端点响应时间过长（可能涉及复杂的油轮监测数据处理）
    - 预期功能: 获取波斯湾油轮统计数据

---

## 问题分析

### 1. 404 错误原因
**根本原因**: 在 `app_simple.py` 中，以下路由定义可能存在但未被正确注册或被注释掉：
- `/api/strategies`
- `/api/strategies/performance`
- `/api/risk-metrics`
- `/api/intel/events`
- `/api/risk-incidents`
- `/api/macro-state`
- `/api/intel/usgs`

**解决方案**:
1. 检查 `app_simple.py` 中是否存在这些路由定义
2. 确认是否被条件判断或异常处理阻止
3. 验证 Google Sheets 中是否存在对应的数据表（sheets_utils 依赖）

### 2. ReadTimeout 错误原因
**可能原因**:
- 外部 API 调用超时（USGS、AIS 数据源等）
- 复杂的数据聚合或计算耗时过长
- Google Sheets API 响应缓慢
- 网络连接问题

**受影响端点**:
- `/api/intel/shadow-fleet` - 需要调用 shadow fleet 监测服务
- `/api/intel/oil-shock` - 需要调用油价数据服务
- `/api/ship-monitoring/statistics` - 需要处理大量油轮追踪数据

---

## 代码现状检查

### 在 app_simple.py 中已定义的路由：
✅ `/api/holdings` - 持仓数据 (行 526)
✅ `/api/status` - 系统状态 (行 578)
✅ `/api/debug` - 调试信息 (行 588)
✅ `/api/chart-data` - 图表数据 (行 602)
✅ `/api/ship-monitoring/vessels` - 油轮列表 (行 624)
✅ `/api/ship-monitoring/alerts` - 油轮警报 (行 646)
✅ `/api/ship-monitoring/statistics` - 油轮统计 (行 677) *超时*
✅ `/api/ship-monitoring/waiting-vessels` - 等待中的油轮 (行 719)
✅ `/api/intel/shadow-fleet` - 影子舰队 (行 799) *超时*
✅ `/api/intel/oil-shock` - 油价冲击 (行 821) *超时*
✅ `/api/strategies` - 策略 (行 842) *404*
✅ `/api/strategies/performance` - 策略绩效 (行 897) *404*
✅ `/api/upload-csv` - CSV 上传 (行 924)
✅ `/api/trades/update` - 交易更新 (行 986)
✅ `/api/risk-metrics` - 风控指标 (行 1021) *404*
✅ `/api/intel/events` - 情报事件 (行 1074) *404*
✅ `/api/risk-incidents` - 风控事件 (行 1104) *404*
✅ `/api/macro-state` - 宏观状态 (行 1134) *404*
✅ `/api/intel/usgs` - USGS 地震 (行 1164) *404*

---

## 建议措施

### 优先级 1 - 紧急修复（影响功能）
1. **404 错误的路由** - 需要调查为什么这些路由在应用中注册但不可访问
   - 检查是否有条件判断（如 `SHIP_MONITOR_OK` 或环境变量）阻止了路由注册
   - 验证 Google Sheets 数据源是否可用
   - 运行 `sheets_utils.py` 验证 Sheets 连接

2. **ReadTimeout 问题** - 需要优化这些端点的性能
   - 增加超时时间（用于测试）
   - 实现缓存机制（如 5 分钟缓存）
   - 分离耗时操作为后台任务

### 优先级 2 - 性能优化
1. 为长时间运行的端点添加缓存
2. 实现异步数据处理
3. 添加请求超时日志

### 优先级 3 - 测试扩展
1. 添加单元测试覆盖所有端点
2. 添加集成测试验证数据准确性
3. 实施性能基准测试

---

## 技术栈验证

- ✅ Flask 服务器运行正常 (端口 9999)
- ✅ Google Sheets 连接成功 (能成功读取 broker_positions)
- ✅ 基础数据路由工作正常 (3/13 成功)
- ⚠️ 部分高级功能未完全实现或有性能问题

---

## 附录：测试脚本调用

```bash
# 启动 Flask 应用
python app_simple.py

# 运行完整测试
python test_api.py

# 运行详细测试（显示响应详情）
python test_api_detailed.py
```

**应用访问**: http://localhost:9999
**文档生成**: API_TEST_RESULTS.md
