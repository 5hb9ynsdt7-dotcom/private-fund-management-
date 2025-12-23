# 项目上下文

## 项目目标
私募基金管理系统 - 用于管理私募基金净值、策略、持仓、交易、分红等全流程数据

## 技术栈
**后端**: FastAPI + SQLAlchemy + SQLite/MySQL + Uvicorn
**前端**: Vue 3 + Element Plus + ECharts + Vue Router + Vite
**数据处理**: Pandas + openpyxl (Excel导入导出)
**部署**: Docker + Railway

## 目录结构
```
privatefund/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI应用入口
│       ├── database.py          # 数据库配置
│       ├── models.py            # SQLAlchemy模型
│       ├── routes/              # 路由模块
│       │   ├── nav.py           # 净值管理
│       │   ├── strategy.py      # 策略管理
│       │   ├── position.py      # 持仓分析
│       │   ├── dividend.py      # 分红管理
│       │   ├── trade.py         # 交易分析
│       │   ├── nav_crawler.py   # 净值抓取
│       │   ├── fund_schedule.py # 基金档期
│       │   ├── quantitative.py  # 量化分析
│       │   └── tushare.py       # Tushare数据
│       ├── services/            # 业务逻辑层
│       └── schemas/             # Pydantic请求/响应模型
├── frontend/
│   └── src/
│       ├── views/               # 页面组件
│       ├── components/          # 可复用组件
│       └── App.vue              # 主应用组件
└── VERSION                      # 版本号: 1.2.0
```

## 核心业务概念
- **基金(Fund)**: 私募证券投资基金产品,基金代码如L03126
- **净值(NAV)**: 基金单位净值/累计净值,按日期记录
- **策略(Strategy)**: 基金投资策略分类(成长/固收/宏观等)
- **持仓(Position)**: 客户在基金中的持有份额和成本
- **分红(Dividend)**: 基金分红记录(每份分红金额、除息日等)
- **集团号(Group ID)**: 客户唯一标识,如000319506
- **项目持仓**: 项目级别的资产配置和行业分布
- **档期**: 基金申购赎回开放时间规则
