# 数据库表结构

## 表关系图
```
Fund (基金主表) 1──N Nav (净值表)
  │              1──1 Strategy (策略表)
  │              1──N Position (持仓表) N──1 Client (客户表)
  │              1──N Dividend (分红表)
  │              1──N ClientDividend (客户分红表) N──1 Client
  └──────────── 1──1 FundScheduleRule (档期规则表)

Transaction (交易表) - 独立表,无外键约束
ProjectHoldingAsset (项目资产表) - 独立表
ProjectHoldingIndustry (项目行业表) - 独立表
IndexMeta (指数元数据表) 1──N IndexDaily (指数日行情表)
```

## 核心表结构

### Fund (基金主表)
| 字段 | 类型 | 说明 |
|------|------|------|
| fund_code | String(20) PK | 基金代码,如L03126 |
| fund_name | String(100) | 基金全名 |
| short_name | String(100) | 基金简称,去除"龙舟-"前缀和后缀 |
| noah_product_id | String(50) | 诺亚CRM系统产品ID |

### Strategy (策略表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增ID |
| fund_code | String(20) FK Unique | 关联基金代码 |
| project_name | String(50) | 项目名称 |
| main_strategy | String(30) | 大类策略:成长/固收/宏观/其他 |
| sub_strategy | String(30) | 细分策略:主观多头/量化多头等 |
| is_qd | Boolean | 是否QD产品 |

### Nav (净值表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增ID |
| fund_code | String(20) FK | 关联基金代码 |
| nav_date | Date | 净值日期 |
| unit_nav | Numeric(16,6) | 单位净值 |
| accum_nav | Numeric(16,6) | 累计净值 |
| **UK**: (fund_code, nav_date) | | 唯一约束 |

### Client (客户表)
| 字段 | 类型 | 说明 |
|------|------|------|
| group_id | String(20) PK | 集团号,保留前导零如000319506 |
| obscured_name | String(10) | 遮蔽姓名,如邢*东 |
| domestic_planner | String(50) | 国内理财师 |

### Position (持仓表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增ID |
| group_id | String(20) FK | 关联客户集团号 |
| fund_code | String(20) FK | 关联基金代码 |
| stock_date | Date | 存量时间 |
| first_buy_date | Date | 首次买入日期 |
| cost_with_fee | Numeric(16,2) | 含费成本 |
| cost_without_fee | Numeric(16,2) | 不含费金额 |
| shares | Numeric(16,2) | 持仓份额 |
| **UK**: (group_id, fund_code, stock_date) | | 唯一约束 |

### Dividend (分红表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增ID |
| fund_code | String(20) FK | 关联基金代码 |
| dividend_date | Date | 分红发放日期 |
| dividend_per_share | Numeric(16,6) | 每份分红金额 |
| ex_dividend_date | Date | 除息日(基准日) |
| record_date | Date | 登记日 |
| pre_dividend_nav | Numeric(16,4) | 除权前净值 |
| **UK**: (fund_code, dividend_date) | | 唯一约束 |

### ClientDividend (客户分红记录表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增ID |
| group_id | String(20) FK | 关联客户集团号 |
| fund_code | String(20) FK | 关联基金代码 |
| transaction_type | String(20) | 交易类型:现金红利/红利转投 |
| confirmed_amount | Numeric(16,2) | 确认金额(原币) |
| confirmed_shares | Numeric(16,6) | 确认份额 |
| confirmed_date | Date | 确认日期 |
| **UK**: (group_id, fund_code, confirmed_date, transaction_type) | | 唯一约束 |

### FundScheduleRule (基金档期规则表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增ID |
| fund_code | String(20) FK Unique | 关联基金代码 |
| subscription_rule | Text | 申购规则描述 |
| redemption_rule | Text | 赎回规则描述 |
| lock_period | String(100) | 锁定期描述 |

### Transaction (交易表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增ID |
| group_id | String(20) | 集团号(无外键) |
| client_name | String(50) | 客户遮蔽姓名 |
| fund_name | String(100) | 基金名称 |
| transaction_type | String(30) | 交易类型名称 |
| confirmed_date | Date | 交易确认日期 |
| confirmed_shares | Numeric(16,6) | 确认份额 |
| confirmed_amount | Numeric(16,2) | 确认金额 |
| transaction_fee | Numeric(16,2) | 手续费 |
| product_code | String(30) | 产品代码 |

### ProjectHoldingAsset (项目资产表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增ID |
| project_name | String(50) | 项目名称 |
| month | Date | 月份 |
| a_share_ratio | Numeric(5,2) | A股比例 |
| h_share_ratio | Numeric(5,2) | H股比例 |
| us_share_ratio | Numeric(5,2) | 美股比例 |
| stock_total_ratio | Numeric(5,2) | 股票总仓位(计算字段) |
| global_bond_ratio | Numeric(5,2) | 全球债券比例 |
| **UK**: (project_name, month) | | 唯一约束 |

### ProjectHoldingIndustry (项目行业表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增ID |
| project_name | String(50) | 项目名称 |
| month | Date | 月份 |
| ratio_type | String(20) | 比例计算方式:based_on_stock/based_on_total |
| industry1~5 | String(50) | 前五大行业名称 |
| industry1~5_ratio | Numeric(5,2) | 对应行业比例 |
| **UK**: (project_name, month) | | 唯一约束 |

### IndexMeta (指数元数据表)
| 字段 | 类型 | 说明 |
|------|------|------|
| ts_code | String(20) PK | Tushare指数代码,如000300.SH |
| index_name | String(50) | 指数名称,如沪深300 |
| latest_trade_date | String(8) | 最新交易日期,YYYYMMDD |
| total_records | Integer | 总记录数 |
| is_active | Boolean | 是否启用 |

### IndexDaily (指数日行情表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 自增ID |
| ts_code | String(20) | Tushare指数代码 |
| trade_date | String(8) | 交易日期,YYYYMMDD |
| close | Numeric(12,4) | 收盘点位 |
| pct_chg | Numeric(12,4) | 涨跌幅(%) |
| **UK**: (ts_code, trade_date) | | 唯一约束 |

## 重要字段说明
- **基金代码**: 如L03126,L00001,最大20字符
- **集团号**: 客户唯一标识,保留前导零,如000319506
- **净值日期**: 每日净值记录的日期
- **单位净值**: 基金每份的价值
- **累计净值**: 包含分红的累计价值,必须>=单位净值
- **含费成本**: 客户投资总成本(含申购费)
- **不含费金额**: 客户实际投入金额(不含申购费)
