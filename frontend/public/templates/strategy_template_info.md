# 策略配置Excel模板说明

## 模板文件名
strategy_template.xlsx

## 列结构
| 列名 | 字段名 | 必填 | 说明 | 示例 |
|------|--------|------|------|------|
| A | fund_code | 是 | 基金代码，6位字符 | L03126 |
| B | fund_name | 否 | 基金名称 | 精选成长基金 |
| C | major_strategy | 是 | 大类策略 | growth/fixed_income/macro/other |
| D | sub_strategy | 否 | 细分策略 | growth_stock/pure_bond/macro_hedge |
| E | is_qd | 否 | 是否QD | TRUE/FALSE |
| F | risk_level | 否 | 风险等级 | low/medium/high |
| G | status | 否 | 状态 | active/inactive |
| H | description | 否 | 策略描述 | 专注于成长性股票投资 |

## 数据示例
```
L03126,精选成长基金,growth,growth_stock,FALSE,medium,active,专注于成长性股票投资
L03127,稳健收益基金,fixed_income,pure_bond,FALSE,low,active,主要投资政府债券
L03128,灵活配置基金,macro,macro_hedge,TRUE,high,active,宏观对冲策略
```

## 注意事项
1. 基金代码必须是6位字符
2. 大类策略必须从枚举值中选择
3. QD字段使用TRUE/FALSE
4. 首行为标题行，从第二行开始为数据
5. 支持.xlsx和.xls格式