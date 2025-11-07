# 项目持仓分析功能 - 设置说明

## 📋 功能概述

"项目持仓分析"功能已成功实现，包括完整的前后端代码，支持：

### 核心功能
- ✅ **项目列表展示**：显示所有上传了净值的项目（去重）
- ✅ **资产类别管理**：按月录入股票、债券等资产配置比例
- ✅ **行业分类管理**：支持两种计算方式的行业持仓比例
- ✅ **数据验证**：完整的表单验证和业务逻辑验证
- ✅ **实际比例计算**：自动计算行业占总仓位的实际比例

### 行业比例计算方式
1. **基于股票仓位**：行业实际占比 = 行业比例 × 股票总仓位比例
2. **基于总仓位**：行业比例直接表示占总仓位的比例

## 🗄️ 数据库设计

### 新增表结构

#### 项目持仓资产表 (project_holding_asset)
```sql
- id: 主键
- project_name: 项目名称
- month: 月份 (DATE)
- a_share_ratio: A股比例 (DECIMAL)
- h_share_ratio: H股比例 (DECIMAL)
- us_share_ratio: 美股比例 (DECIMAL)
- other_market_ratio: 其他市场比例 (DECIMAL)
- stock_total_ratio: 股票总仓位比例 (计算字段)
- global_bond_ratio: 全球债券比例 (DECIMAL)
- convertible_bond_ratio: 可转债比例 (DECIMAL)
- other_ratio: 其他比例 (DECIMAL)
- created_at: 创建时间
```

#### 项目持仓行业表 (project_holding_industry)
```sql
- id: 主键
- project_name: 项目名称
- month: 月份 (DATE)
- ratio_type: 行业比例计算方式 (VARCHAR)
- industry1~5: 第1-5持仓行业 (VARCHAR)
- industry1_ratio~5_ratio: 行业比例 (DECIMAL)
- created_at: 创建时间
```

## 🔧 部署步骤

### 1. 数据库表创建

运行表创建脚本：
```bash
cd backend
python3 create_project_holding_tables.py
```

如果没有相应的Python环境，可以手动在数据库中执行以下SQL：

```sql
-- 创建项目持仓资产表
CREATE TABLE project_holding_asset (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name VARCHAR(50) NOT NULL,
    month DATE NOT NULL,
    a_share_ratio DECIMAL(5,2),
    h_share_ratio DECIMAL(5,2),
    us_share_ratio DECIMAL(5,2),
    other_market_ratio DECIMAL(5,2),
    stock_total_ratio DECIMAL(5,2),
    global_bond_ratio DECIMAL(5,2),
    convertible_bond_ratio DECIMAL(5,2),
    other_ratio DECIMAL(5,2),
    created_at DATE DEFAULT CURRENT_DATE,
    UNIQUE(project_name, month)
);

-- 创建项目持仓行业表
CREATE TABLE project_holding_industry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name VARCHAR(50) NOT NULL,
    month DATE NOT NULL,
    ratio_type VARCHAR(20) NOT NULL,
    industry1 VARCHAR(50),
    industry1_ratio DECIMAL(5,2),
    industry2 VARCHAR(50),
    industry2_ratio DECIMAL(5,2),
    industry3 VARCHAR(50),
    industry3_ratio DECIMAL(5,2),
    industry4 VARCHAR(50),
    industry4_ratio DECIMAL(5,2),
    industry5 VARCHAR(50),
    industry5_ratio DECIMAL(5,2),
    created_at DATE DEFAULT CURRENT_DATE,
    UNIQUE(project_name, month)
);
```

### 2. 后端服务启动

确保后端服务包含新的路由：
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 3. 前端服务启动

```bash
cd frontend
npm install
npm run dev
```

## 📱 使用说明

### 访问路径
- **项目列表页**：`/project-holding`
- **项目详情页**：`/project-holding/:projectName`

### 操作流程
1. **查看项目列表**：系统自动显示所有有净值数据的项目
2. **进入项目详情**：点击项目名称进入详情页
3. **资产配置管理**：
   - 选择"资产类别"标签
   - 点击"新增资产配置"
   - 选择月份，输入各类资产比例
   - 系统自动计算股票总仓位
4. **行业配置管理**：
   - 选择"行业分类"标签
   - 点击"新增行业配置"
   - 选择计算方式和月份
   - 输入最多5个行业及其比例
   - 系统自动计算实际占比

## 📊 已实现文件

### 后端文件
- ✅ `backend/app/models.py` - 新增数据模型
- ✅ `backend/app/schemas/project_holding.py` - 数据验证模式
- ✅ `backend/app/routes/project_holding.py` - API路由
- ✅ `backend/app/main.py` - 路由注册
- ✅ `backend/create_project_holding_tables.py` - 表创建脚本

### 前端文件
- ✅ `frontend/src/api/project-holding.js` - API接口
- ✅ `frontend/src/views/ProjectHoldingList.vue` - 项目列表页
- ✅ `frontend/src/views/ProjectHoldingDetail.vue` - 项目详情页
- ✅ `frontend/src/components/AssetConfigDialog.vue` - 资产配置对话框
- ✅ `frontend/src/components/IndustryConfigDialog.vue` - 行业配置对话框
- ✅ `frontend/src/router/index.js` - 路由配置
- ✅ `frontend/src/App.vue` - 导航菜单

## 🔍 API端点

### 项目管理
- `GET /api/project-holding/projects` - 获取项目列表
- `GET /api/project-holding/{project_name}` - 获取项目详情
- `GET /api/project-holding/{project_name}/analysis` - 获取项目分析数据

### 资产配置
- `POST /api/project-holding/{project_name}/asset` - 创建资产配置
- `PUT /api/project-holding/asset/{record_id}` - 更新资产配置
- `DELETE /api/project-holding/asset/{record_id}` - 删除资产配置

### 行业配置
- `POST /api/project-holding/{project_name}/industry` - 创建行业配置
- `PUT /api/project-holding/industry/{record_id}` - 更新行业配置
- `DELETE /api/project-holding/industry/{record_id}` - 删除行业配置

## ⚠️ 注意事项

1. **数据依赖**：项目列表基于已上传净值的基金数据
2. **权限验证**：需要确保只有授权用户可以访问
3. **数据完整性**：系统会自动验证比例数据的合理性
4. **计算逻辑**：特别注意行业比例的两种计算方式

## 🎉 功能特色

- **智能计算**：自动计算股票总仓位和行业实际占比
- **数据验证**：完整的前后端数据验证
- **用户友好**：直观的界面和操作流程
- **灵活配置**：支持多种资产类别和行业分类方式
- **历史记录**：按月保存历史配置记录

功能已完全实现，只需创建数据库表即可正常使用！