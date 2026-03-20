# 组合净值存储与业绩PK扩展设计方案

> 设计日期：2026-03-19
> 目标：支持回测组合、实盘组合的净值存储和业绩PK对比

## 一、需求分析

### 当前问题
1. 业绩PK只能对比单个产品（私募基金、公募基金）
2. 回测组合运行后，净值数据只在前端展示，没有持久化存储
3. 实盘组合没有计算和存储周度净值
4. 无法对比"回测组合 vs 实盘组合"或"组合 vs 产品"

### 目标
1. 创建统一的组合净值存储表
2. 回测运行后自动保存周度净值
3. 实盘组合定期计算并保存周度净值
4. 业绩PK支持选择：产品、回测组合、实盘组合

---

## 二、数据库设计

### 2.1 新增表：PortfolioNav（组合净值表）

```python
class PortfolioNav(Base):
    """
    组合净值表 - 统一存储各类组合的净值数据
    支持回测组合、实盘组合的周度/日度净值
    """
    __tablename__ = 'portfolio_nav'
    __table_args__ = (
        UniqueConstraint('portfolio_type', 'portfolio_id', 'nav_date',
                        name='uix_portfolio_nav'),
        Index('idx_portfolio_nav_lookup', 'portfolio_type', 'portfolio_id', 'nav_date'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 组合标识
    portfolio_type = Column(String(20), nullable=False, comment='组合类型：backtest/live')
    portfolio_id = Column(Integer, nullable=False, comment='组合ID（关联到具体组合表）')
    portfolio_name = Column(String(100), comment='组合名称（冗余字段，便于查询）')

    # 净值数据
    nav_date = Column(Date, nullable=False, index=True, comment='净值日期')
    unit_nav = Column(Numeric(16, 6), nullable=False, comment='单位净值')
    accum_nav = Column(Numeric(16, 6), nullable=False, comment='累计净值')

    # 收益数据（可选）
    daily_return = Column(Numeric(12, 6), comment='日收益率（%）')
    total_return = Column(Numeric(12, 4), comment='累计收益率（%）')

    # 组合市值（可选）
    total_value = Column(Numeric(20, 2), comment='组合总市值（元）')

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<PortfolioNav(type='{self.portfolio_type}', id={self.portfolio_id}, date='{self.nav_date}', nav={self.unit_nav})>"
```

### 2.2 字段说明

| 字段 | 类型 | 说明 |
|-----|------|------|
| portfolio_type | String(20) | backtest=回测组合, live=实盘组合 |
| portfolio_id | Integer | 关联到 backtest_portfolio.id 或 public_fund_portfolio.id |
| portfolio_name | String(100) | 组合名称（冗余存储，避免JOIN查询）|
| nav_date | Date | 净值日期（周五或最后交易日）|
| unit_nav | Numeric(16,6) | 单位净值（初始为1.0000）|
| accum_nav | Numeric(16,6) | 累计净值（考虑分红）|
| daily_return | Numeric(12,6) | 日收益率（可选）|
| total_return | Numeric(12,4) | 累计收益率（可选）|
| total_value | Numeric(20,2) | 组合总市值（可选）|

### 2.3 唯一约束
- 同一组合（type + id）+ 同一日期 = 唯一记录
- 索引：(portfolio_type, portfolio_id, nav_date) 加速查询

---

## 三、业务逻辑设计

### 3.1 回测组合净值存储

**触发时机**：用户运行回测时

**流程**：
```
1. 用户点击"运行回测" → POST /api/portfolio-backtest/run
2. 回测服务计算每日净值曲线
3. 提取周度净值（每周五或最后交易日）
4. 批量插入 PortfolioNav 表
5. 返回回测结果给前端
```

**代码位置**：`services/portfolio_backtest_service.py`

**修改点**：
```python
def run_backtest(...):
    # 现有逻辑：计算回测结果
    result = {...}

    # 新增：保存周度净值
    if portfolio_id:  # 如果是已保存的组合
        weekly_navs = extract_weekly_nav(result['nav_curve'])
        save_portfolio_nav(
            portfolio_type='backtest',
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name,
            nav_data=weekly_navs
        )

    return result
```

### 3.2 实盘组合净值计算

**触发时机**：
1. 定时任务：每日收盘后自动计算
2. 手动触发：用户点击"更新净值"

**计算逻辑**：
```
1. 获取组合持仓列表（各产品及权重）
2. 获取各产品最新净值
3. 计算组合单位净值 = Σ(产品净值 × 权重)
4. 计算累计净值（考虑历史分红）
5. 存入 PortfolioNav 表
```

**新增API**：
```
POST /api/portfolio/calculate-nav/{portfolio_id}  # 手动计算净值
GET  /api/portfolio/nav-history/{portfolio_id}    # 查询净值历史
```

**代码位置**：`services/portfolio_service.py`

### 3.3 业绩PK扩展

**修改点**：

1. **获取可对比对象列表**
```python
GET /api/performance/objects
返回：
{
    "products": [
        {"type": "private", "code": "xxx", "name": "xxx"},
        {"type": "public", "code": "xxx", "name": "xxx"}
    ],
    "portfolios": [
        {"type": "backtest", "id": 1, "name": "量化组合A"},
        {"type": "live", "id": 2, "name": "实盘组合B"}
    ]
}
```

2. **执行对比**
```python
POST /api/performance/compare
请求体：
{
    "objects": [
        {"type": "product", "code": "xxx"},
        {"type": "backtest", "id": 1},
        {"type": "live", "id": 2}
    ],
    "time_range": "1y",
    "benchmark": "000300.SH"
}
```

3. **数据获取逻辑**
```python
def get_nav_data(obj):
    if obj['type'] == 'product':
        # 从 Nav 表查询
        return query_product_nav(obj['code'])
    elif obj['type'] in ['backtest', 'live']:
        # 从 PortfolioNav 表查询
        return query_portfolio_nav(obj['type'], obj['id'])
```

---

## 四、前端修改

### 4.1 业绩PK页面（PerformancePK.vue）

**修改点**：

1. **对象选择器**
```vue
<el-select v-model="selectedType">
  <el-option label="产品" value="product" />
  <el-option label="回测组合" value="backtest" />
  <el-option label="实盘组合" value="live" />
</el-select>

<el-select v-model="selectedObject" v-if="selectedType === 'product'">
  <!-- 产品列表 -->
</el-select>

<el-select v-model="selectedObject" v-if="selectedType === 'backtest'">
  <!-- 回测组合列表 -->
</el-select>

<el-select v-model="selectedObject" v-if="selectedType === 'live'">
  <!-- 实盘组合列表 -->
</el-select>
```

2. **已选对象展示**
```vue
<el-tag v-for="obj in selectedObjects" :key="obj.id">
  <el-icon v-if="obj.type === 'product'"><TrendCharts /></el-icon>
  <el-icon v-if="obj.type === 'backtest'"><DataAnalysis /></el-icon>
  <el-icon v-if="obj.type === 'live'"><Money /></el-icon>
  {{ obj.name }}
</el-tag>
```

### 4.2 回测页面（PortfolioBacktest.vue）

**新增功能**：
- 回测完成后提示"净值已保存，可在业绩PK中对比"
- 显示"查看净值历史"按钮

### 4.3 实盘组合页面（Portfolio/PortfolioList.vue）

**新增功能**：
- "更新净值"按钮
- "净值历史"图表
- "加入PK对比"快捷入口

---

## 五、实施步骤

### Phase 1: 数据库和基础服务（2-3天）
- [ ] 创建 PortfolioNav 表（migration）
- [ ] 实现 PortfolioNavService 基础CRUD
- [ ] 编写单元测试

### Phase 2: 回测组合净值存储（1-2天）
- [ ] 修改 portfolio_backtest_service.py
- [ ] 提取周度净值逻辑
- [ ] 批量保存净值数据
- [ ] 测试回测流程

### Phase 3: 实盘组合净值计算（2-3天）
- [ ] 实现净值计算逻辑
- [ ] 新增API接口
- [ ] 定时任务配置（可选）
- [ ] 测试净值计算准确性

### Phase 4: 业绩PK扩展（2-3天）
- [ ] 修改 performance_pk_service.py
- [ ] 支持多类型对象查询
- [ ] 统一净值数据获取接口
- [ ] 测试混合对比功能

### Phase 5: 前端改造（2-3天）
- [ ] 修改业绩PK页面
- [ ] 修改回测页面
- [ ] 修改实盘组合页面
- [ ] UI/UX优化

### Phase 6: 测试和优化（1-2天）
- [ ] 端到端测试
- [ ] 性能优化
- [ ] 文档更新

**总计：10-16天**

---

## 六、技术要点

### 6.1 周度净值提取
```python
def extract_weekly_nav(daily_nav_curve):
    """从日度净值曲线提取周度净值（每周五）"""
    weekly_navs = []
    for date, nav in daily_nav_curve:
        if date.weekday() == 4:  # 周五
            weekly_navs.append({
                'nav_date': date,
                'unit_nav': nav['unit_nav'],
                'accum_nav': nav['accum_nav']
            })
    return weekly_navs
```

### 6.2 实盘组合净值计算
```python
def calculate_portfolio_nav(portfolio_id):
    """计算实盘组合净值"""
    # 1. 获取组合配置
    portfolio = get_portfolio(portfolio_id)
    holdings = portfolio.holdings  # [{fund_code, weight}, ...]

    # 2. 获取各产品最新净值
    nav_data = {}
    for holding in holdings:
        nav = get_latest_nav(holding['fund_code'])
        nav_data[holding['fund_code']] = nav

    # 3. 计算组合净值
    unit_nav = sum(
        nav_data[h['fund_code']].unit_nav * h['weight']
        for h in holdings
    )

    # 4. 计算累计净值（考虑历史分红）
    accum_nav = calculate_accum_nav(portfolio_id, unit_nav)

    return {
        'nav_date': datetime.now().date(),
        'unit_nav': unit_nav,
        'accum_nav': accum_nav
    }
```

### 6.3 性能优化
1. **批量插入**：使用 `bulk_insert_mappings` 批量插入净值数据
2. **索引优化**：在 (portfolio_type, portfolio_id, nav_date) 上建立联合索引
3. **缓存策略**：常用组合的净值数据缓存到 Redis
4. **异步计算**：实盘组合净值计算使用后台任务

---

## 七、风险和注意事项

### 7.1 数据一致性
- 回测组合修改配置后，需要清除旧的净值数据
- 实盘组合调仓后，净值计算逻辑需要调整

### 7.2 历史数据迁移
- 现有的回测组合没有净值数据，需要提供"重新计算"功能
- 实盘组合需要从历史持仓数据回溯计算净值

### 7.3 性能考虑
- 大量组合的净值计算可能耗时较长
- 需要考虑分页查询和懒加载

### 7.4 用户体验
- 净值计算中显示进度条
- 提供"快速对比"功能（预设常用组合）

---

## 八、后续扩展

### 8.1 更多组合类型
- 支持"虚拟组合"（用户自定义配置，不实际持仓）
- 支持"策略组合"（按策略分类的产品组合）

### 8.2 更多净值频率
- 支持日度净值（用于更精细的分析）
- 支持月度净值（用于长期趋势分析）

### 8.3 更多对比维度
- 风险调整收益（夏普比率、索提诺比率）
- 最大回撤对比
- 波动率对比
- 胜率统计

---

## 九、总结

本方案通过创建统一的 `PortfolioNav` 表，实现了：
1. ✅ 回测组合净值持久化存储
2. ✅ 实盘组合净值自动计算
3. ✅ 业绩PK支持多类型对象对比
4. ✅ 可扩展的架构设计

核心优势：
- 统一的数据模型，便于维护
- 灵活的对比方式，提升用户体验
- 可扩展的架构，支持未来功能迭代
