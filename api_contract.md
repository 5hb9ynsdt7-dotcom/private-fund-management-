# API 接口约定

## 基础规范
- **Base URL**: `/api`
- **响应格式**: `{success: bool, message: str, data: any}`
- **分页参数**: `page`, `page_size`
- **排序参数**: `sort_by`, `sort_order`
- **日期格式**: `YYYY-MM-DD` 或 `YYYYMMDD`

## 核心接口

### 净值管理 `/api/nav`
| 接口 | 方法 | 用途 | 关键参数 |
|------|------|------|----------|
| `/upload` | POST | 批量上传Excel净值文件 | files: List[UploadFile] |
| `/manual` | POST | 手动添加净值记录 | fund_code, nav_date, unit_nav, accum_nav |
| `/list` | GET | 分页查询净值列表 | fund_code?, fund_name?, start_date?, end_date? |
| `/{nav_id}` | DELETE | 删除单条净值记录 | nav_id |
| `/latest/{fund_code}` | GET | 获取指定基金最新净值 | fund_code |
| `/fund/{fund_code}` | GET | 获取指定基金净值记录 | fund_code, limit (默认10,最大10000) |
| `/template` | GET | 下载Excel导入模板 | - |

### 策略管理 `/api/strategy`
| 接口 | 方法 | 用途 | 关键参数 |
|------|------|------|----------|
| `/upload` | POST | 批量上传策略Excel | file |
| `/manual` | POST | 手动添加策略 | fund_code, main_strategy, sub_strategy, is_qd |
| `/list` | GET | 查询策略列表 | main_strategy?, is_qd? |
| `/{fund_code}` | PUT | 更新策略 | fund_code, strategy_data |

### 持仓分析 `/api/position`
| 接口 | 方法 | 用途 | 关键参数 |
|------|------|------|----------|
| `/upload` | POST | 上传持仓Excel | file |
| `/list` | GET | 查询持仓列表 | fund_code?, group_id?, stock_date? |
| `/analysis` | GET | 持仓分析统计 | fund_code, analysis_date |
| `/export` | GET | 导出分析报告 | fund_code, format |

### 分红管理 `/api/dividend`
| 接口 | 方法 | 用途 | 关键参数 |
|------|------|------|----------|
| `/upload` | POST | 上传分红Excel | file |
| `/list` | GET | 查询分红记录 | fund_code?, start_date?, end_date? |
| `/client` | GET | 客户分红交易记录 | group_id?, fund_code? |

### 净值抓取 `/api/nav-crawler`
| 接口 | 方法 | 用途 | 关键参数 |
|------|------|------|----------|
| `/crawl/{fund_code}` | POST | 抓取指定基金净值 | fund_code, start_date?, end_date? |
| `/batch-crawl` | POST | 批量抓取净值 | fund_codes: List[str] |

### 量化分析 `/api/quantitative`
| 接口 | 方法 | 用途 | 关键参数 |
|------|------|------|----------|
| `/products` | GET | 获取产品列表 | - |
| `/analysis/{fund_code}` | GET | 单产品分析 | fund_code, start_date, end_date |
| `/summary` | GET | 综合分析 | fund_codes: List[str] |

## 业务约束
1. **净值数据**: 累计净值 >= 单位净值 > 0
2. **日期唯一**: 同一基金+日期组合唯一,重复上传自动更新
3. **集团号格式**: 保留前导零,补齐至9位
4. **基金代码**: 最大20字符,字母数字组合
5. **分红金额**: 必须大于0,分红日期不能是未来
6. **Excel导入**: 支持`.xlsx`/`.xls`,自动去重并返回处理统计
7. **分页限制**: page_size最大1000条
8. **级联删除**: 删除基金时自动删除关联的净值、策略、持仓、分红记录
