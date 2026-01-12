# Private Fund Management System - Release Notes v2.1.0

> 发布日期：2025-01-12
> 版本类型：功能版本 (Minor Release)
> 基于版本：v2.0.0

---

## 🎉 版本概述

v2.1.0 是一个重大功能增强版本，新增了**业绩PK对比系统**、**组合回测系统**和**年度回顾功能**，大幅提升了投资分析能力。同时完善了公募基金模块和实盘组合管理功能，为用户提供更全面的投资管理工具。

## ✨ 新增功能

### 1. 业绩PK对比系统 🏆

一个全新的业绩对比分析工具，支持多产品、多组合的横向对比分析。

#### 核心特性
- **多类型对比**
  - 单品对比：选择2-10个产品进行对比
  - 组合对比：对比不同投资组合的表现
  - 支持私募基金与公募基金的混合对比

- **灵活的时间范围**
  - 预设时间：近1个月、3个月、6个月、1年、3年
  - 成立以来：查看产品全生命周期表现
  - 自定义范围：精确选择开始和结束日期

- **基准对比**
  - 可选择市场指数作为基准
  - 同时展示超额收益
  - 支持沪深300、中证500等主流指数

- **对齐模式**
  - 共同时间对齐：使用所有产品的共同时间段
  - 分别对齐：每个产品使用各自的完整时间段

- **PK记录管理**
  - 保存常用的对比配置
  - 快速加载历史PK记录
  - 支持记录的编辑和删除

#### 技术实现
- 后端路由：`/api/performance/*`
- 服务层：`PerformancePKService`
- 数据模型：`PerformancePKRecord`
- 前端页面：`PerformancePK.vue`

#### API接口
```
GET  /api/performance/products        # 获取可对比产品列表
POST /api/performance/compare         # 执行业绩对比
POST /api/performance/pk/save         # 保存PK记录
GET  /api/performance/pk/list         # 获取PK记录列表
GET  /api/performance/pk/{pk_id}      # 获取PK记录详情
DELETE /api/performance/pk/{pk_id}    # 删除PK记录
```

---

### 2. 组合回测系统 📈

专业的投资组合回测工具，支持多产品组合的历史表现模拟。

#### 核心特性
- **灵活的组合配置**
  - 权重配置：按百分比分配各产品权重（总和100%）
  - 金额配置：按具体金额分配各产品投资额
  - 支持动态添加/删除产品

- **回测参数设置**
  - 初始资金：自定义起始投资金额（万元）
  - 回测时间：选择任意历史时间段
  - 调仓频率：不调仓、月度、季度、半年、年度
  - 分红处理：分红再投资 或 现金分红
  - 费用考虑：可选是否计入交易费用

- **组合管理**
  - 保存组合配置：给组合命名并保存
  - 快速加载：从已保存组合中快速加载配置
  - 组合列表：查看所有保存的组合
  - 组合删除：删除不需要的组合配置

- **回测结果展示**
  - 组合净值曲线
  - 累计收益率
  - 年化收益率
  - 最大回撤
  - 夏普比率
  - 与基准的对比（可选）

#### 技术实现
- 后端路由：`/api/portfolio-backtest/*`
- 服务层：`PortfolioBacktestService`
- 数据模型：`BacktestPortfolio`
- 前端页面：`PortfolioBacktest.vue`

#### API接口
```
POST   /api/portfolio-backtest/run           # 运行组合回测
POST   /api/portfolio-backtest/save          # 保存组合配置
GET    /api/portfolio-backtest/portfolios    # 获取组合列表
GET    /api/portfolio-backtest/portfolios/{id}  # 获取组合详情
DELETE /api/portfolio-backtest/portfolios/{id}  # 删除组合
```

---

### 3. 年度回顾组件 📅

全新的年度投资复盘功能，帮助用户回顾和分析年度投资表现。

#### 核心特性
- **年度汇总**
  - 年度总收益展示
  - 表现最佳/最差季度统计
  - 年初/年末市值对比

- **季度收益分析**
  - 四个季度收益对比
  - 累计收益曲线
  - 图表可视化展示

- **持仓变动分析**
  - 年度持仓变化追踪
  - 新增/减持产品统计
  - 持仓结构变化对比

#### 技术实现
- 前端组件：`AnnualReview.vue`
- 集成到持仓详情页面
- 支持多年度数据切换

---

### 4. 公募基金模块增强 🏦

完善公募基金管理功能，提供更丰富的公募基金数据和分析。

#### 主要改进
- **公募基金库**
  - 完整的公募基金数据库
  - 支持基金搜索和筛选
  - 基金基本信息展示

- **公募基金详情页**
  - 详细的基金信息
  - 净值走势图表
  - 历史业绩数据

#### 路由变更
```
/public-fund                          # 公募基金库（原PublicFund改名）
/public-fund/detail/:fundCode         # 公募基金详情页（新增）
```

---

### 5. 实盘组合功能 💼

新增实盘组合管理模块，区别于回测组合。

#### 核心特性
- 组合列表管理
- 组合详情展示
- 实盘持仓跟踪
- 收益统计分析

#### 技术实现
- 后端路由：`/api/portfolio/*`
- 前端页面：`Portfolio/PortfolioList.vue`、`Portfolio/PortfolioDetail.vue`

---

## 🔧 功能优化

### 数据库模型扩展

#### Fund 表
- 新增字段：`product_features` (产品特征)
  - 记录产品策略特征
  - 如：股票多头、量化对冲等

#### FundScheduleRule 表
- 新增字段：`fee_structure` (费用结构)
  - JSON格式存储分档费率信息
  - 支持复杂的费率配置

#### 新增表
- `BacktestPortfolio` - 回测组合配置表
  - 保存用户创建的回测组合
  - 存储组合配置和参数

- `PerformancePKRecord` - 业绩PK记录表
  - 保存用户的对比配置
  - 快速重现历史对比场景

### 前端路由优化
- 重构公募基金路由结构
- 新增业绩PK路由
- 新增组合回测路由
- 新增实盘组合路由

### 主应用集成
- `main.py` 集成4个新路由模块
  - `public_fund` - 公募基金
  - `portfolio` - 实盘组合
  - `portfolio_backtest` - 组合回测
  - `performance_pk` - 业绩PK

---

## 📊 性能优化

### 数据查询优化
- 业绩对比查询优化
- 回测计算性能提升
- 公募基金数据检索优化

### 缓存机制
- 对比结果缓存
- 回测数据缓存
- 提升重复查询速度

---

## 🐛 Bug修复

### 数据处理修复
- 修复净值数据处理中的日期格式问题
- 修复分红数据计算逻辑
- 修复量化分析指标计算错误

### UI/UX修复
- 优化页面响应速度
- 修复图表显示异常
- 改进表格排序逻辑

---

## 📦 依赖更新

### 前端依赖
- Element Plus 组件库保持最新
- ECharts 图表库更新
- Vue Router 路由增强

### 后端依赖
- FastAPI 框架保持稳定
- SQLAlchemy ORM 优化
- Pandas 数据处理增强

---

## 🔄 数据库迁移

### 新增表
```sql
-- 回测组合配置表
CREATE TABLE backtest_portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_name VARCHAR(100) NOT NULL,
    portfolio_config TEXT NOT NULL,
    initial_capital NUMERIC(16, 2),
    weight_mode VARCHAR(20) DEFAULT 'weight',
    rebalance_frequency VARCHAR(20) DEFAULT 'quarterly',
    reinvest_dividend BOOLEAN DEFAULT 1,
    consider_fees BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 业绩PK记录表
CREATE TABLE performance_pk_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    compare_type VARCHAR(20) NOT NULL,
    objects TEXT NOT NULL,
    time_range VARCHAR(20),
    custom_range TEXT,
    benchmark VARCHAR(20),
    align_mode VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 表结构变更
```sql
-- Fund表新增字段
ALTER TABLE fund ADD COLUMN product_features VARCHAR(200);

-- FundScheduleRule表新增字段
ALTER TABLE fund_schedule_rule ADD COLUMN fee_structure TEXT;
```

---

## 📝 升级说明

### 从 v2.0.0 升级到 v2.1.0

#### 1. 备份数据
```bash
# 备份数据库
cp backend/privatefund.db backend/privatefund_backup_v2.0.0.db
```

#### 2. 更新代码
```bash
# 拉取最新代码
git fetch --tags
git checkout v2.1.0
```

#### 3. 更新依赖
```bash
# 后端依赖
cd backend
source backend_venv/bin/activate  # 或 venv/bin/activate
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install
```

#### 4. 运行数据库迁移
```bash
cd backend
# 数据库迁移会在应用启动时自动执行
python -m uvicorn app.main:app --reload
```

#### 5. 重启服务
```bash
# 后端
cd backend
./backend_venv/bin/uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm run dev
```

---

## ⚠️ 注意事项

### 兼容性说明
- ✅ 完全兼容 v2.0.0 的数据
- ✅ 现有功能保持不变
- ✅ API接口向后兼容

### 已知限制
- 组合回测功能需要完整的历史净值数据
- 业绩PK对比最多支持10个对象
- 公募基金数据依赖外部数据源

### 建议
- 升级前建议备份数据库
- 首次运行会执行数据库迁移，可能需要几秒钟
- 建议在测试环境先验证功能

---

## 🎯 后续计划

### v2.2.0 规划
- [ ] 风险分析模块
- [ ] 资产配置建议
- [ ] 智能组合优化
- [ ] 更多图表类型

### 长期规划
- 机器学习预测模型
- 实时数据推送
- 移动端应用
- 多用户权限管理

---

## 👥 贡献者

感谢所有为 v2.1.0 做出贡献的开发者！

---

## 📞 反馈与支持

如有问题或建议，请通过以下方式联系：
- GitHub Issues: [项目地址]
- 邮箱: [联系邮箱]

---

**Private Fund Management System v2.1.0** - 让投资分析更专业、更高效！
