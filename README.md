# Private Fund Management System

> 私募基金管理系统 v1.0.0

一个专业的私募基金管理系统，提供净值管理、策略配置、持仓分析、交易分析等功能。

## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [部署指南](#部署指南)
- [API文档](#api文档)
- [版本管理](#版本管理)
- [贡献指南](#贡献指南)

## ✨ 功能特性

### 核心功能模块

- **📈 净值管理**: 基金净值数据上传、查询、历史记录管理
- **⚙️ 策略管理**: 投资策略配置、大类/细分策略设置、QD产品标识
- **📊 持仓分析**: 客户持仓详情、收益计算、策略分布可视化
- **💰 分红管理**: 现金分红记录、红利转投处理
- **🔄 交易分析**: 资金流向分析、客户活跃度统计、基金表现评估

### 计算功能

- **持有收益计算**: 考虑现金分红的准确收益计算
- **阶段收益分析**: 灵活时间范围的收益分析，智能处理买入时间
- **今年以来收益**: 与阶段收益逻辑一致的YTD计算
- **策略分组统计**: 按大类策略自动分组和小计

### 数据可视化

- **ECharts图表**: 持仓分布、策略分析饼图
- **动态表格**: 分组显示、小计汇总、QD标识
- **响应式设计**: 支持各种屏幕尺寸

## 🛠 技术栈

### 后端技术

- **框架**: FastAPI 
- **数据库**: SQLite (SQLAlchemy ORM)
- **数据处理**: Pandas, NumPy
- **文件处理**: OpenPyXL (Excel文件处理)
- **API文档**: Swagger/OpenAPI 自动生成

### 前端技术

- **框架**: Vue 3 (Composition API)
- **UI组件**: Element Plus
- **图表库**: ECharts
- **HTTP客户端**: Axios
- **路由**: Vue Router 4
- **构建工具**: Vite

### 开发工具

- **版本控制**: Git
- **代码规范**: ESLint, Black (Python)
- **API测试**: FastAPI 自动测试界面
- **部署**: Docker 支持

## 📁 项目结构

```
privatefund/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── routes/         # API路由
│   │   ├── models.py       # 数据模型
│   │   ├── schemas/        # Pydantic模式
│   │   ├── services/       # 业务逻辑
│   │   └── main.py         # 应用入口
│   ├── requirements.txt    # Python依赖
│   └── Dockerfile         # Docker配置
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 公共组件
│   │   ├── api/          # API接口
│   │   └── router/       # 路由配置
│   ├── package.json      # Node.js依赖
│   └── Dockerfile        # Docker配置
├── docs/                 # 项目文档
├── VERSION_MANAGEMENT.md # 版本管理方案
├── CHANGELOG.md         # 版本更新日志
└── README.md           # 项目说明
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- npm 或 yarn

### 本地开发

1. **克隆项目**
```bash
git clone [repository-url]
cd privatefund
```

2. **启动后端服务**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

3. **启动前端服务**
```bash
cd frontend
npm install
npm run dev
```

4. **访问应用**
- 前端应用: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 📚 API文档

### 自动生成文档

访问 http://localhost:8000/docs 查看完整的API文档，包括：

- 所有接口的详细说明
- 请求/响应参数
- 在线测试功能
- 数据模型定义

### 主要API端点

- **净值管理**: `/api/nav/*`
- **策略管理**: `/api/strategy/*`  
- **持仓分析**: `/api/position/*`
- **分红管理**: `/api/dividend/*`
- **交易分析**: `/api/trade/*`

## 📋 使用指南

### 数据上传格式

1. **净值数据**: Excel格式，包含基金代码、净值日期、单位净值、累计净值
2. **持仓数据**: Excel格式，包含客户信息、基金代码、持仓份额、成本等
3. **分红数据**: Excel格式，包含分红类型、确认金额、确认日期等

### 计算逻辑说明

- **持有收益** = 最新市值 - 成本(含费) - 现金分红
- **阶段收益** = (期末净值 - 期初净值) × 持仓份额
  - 买入时间在阶段内：使用买入净值作为期初净值
  - 买入时间在阶段前：使用阶段开始日净值作为期初净值

## 📊 版本管理

当前版本：**v1.0.0**

查看 [VERSION_MANAGEMENT.md](./VERSION_MANAGEMENT.md) 了解：
- 版本号规范
- 分支管理策略  
- 发布流程
- 提交信息规范

查看 [CHANGELOG.md](./CHANGELOG.md) 了解版本更新历史。

## 🤝 贡献指南

### 开发流程

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

### 代码规范

- 后端：遵循 PEP 8 Python代码规范
- 前端：使用 ESLint 检查代码质量
- 提交信息：遵循 [约定式提交](https://www.conventionalcommits.org/zh-hans/)

## 📄 许可证

本项目采用 [MIT License](./LICENSE) 许可证。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 项目Issues: [GitHub Issues](repository-url/issues)
- 邮箱: [your-email]
- 文档: [项目文档](./docs/)

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户。

---

**Private Fund Management System** - 让私募基金管理更简单高效