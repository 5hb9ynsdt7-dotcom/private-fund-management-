# 版本管理方案

## 版本号规范

本项目采用 **语义化版本控制 (Semantic Versioning)** 规范：

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
```

### 版本号含义

- **MAJOR (主版本号)**: 不兼容的API修改
- **MINOR (次版本号)**: 向下兼容的功能性新增  
- **PATCH (修订号)**: 向下兼容的问题修正
- **PRERELEASE (预发布)**: 可选的预发布版本标识 (alpha, beta, rc)
- **BUILD (构建元数据)**: 可选的构建信息

### 版本示例

- `1.0.0` - 正式发布版本
- `1.1.0` - 新增功能版本
- `1.0.1` - 问题修复版本
- `2.0.0` - 重大更新版本
- `1.1.0-beta.1` - 预发布版本

## 分支管理策略

### 主要分支

- **main**: 主分支，保存生产环境代码
- **develop**: 开发分支，集成最新开发功能
- **release/x.x.x**: 发布分支，准备发布的版本
- **hotfix/x.x.x**: 热修复分支，紧急修复生产问题

### 功能分支

- **feature/功能名称**: 新功能开发分支
- **bugfix/问题描述**: 错误修复分支
- **docs/文档更新**: 文档更新分支

## 发布流程

### 1. 功能开发流程

```bash
# 1. 从develop创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/新功能名称

# 2. 开发完成后合并到develop
git checkout develop
git merge feature/新功能名称
git push origin develop
```

### 2. 版本发布流程

```bash
# 1. 从develop创建发布分支
git checkout develop
git checkout -b release/1.1.0

# 2. 更新版本号和文档
# 更新 package.json, __init__.py 等文件中的版本号
# 更新 CHANGELOG.md

# 3. 测试发布分支
# 执行完整测试流程

# 4. 合并到main并打标签
git checkout main
git merge release/1.1.0
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin main --tags

# 5. 合并回develop
git checkout develop
git merge release/1.1.0
git push origin develop
```

### 3. 热修复流程

```bash
# 1. 从main创建热修复分支
git checkout main
git checkout -b hotfix/1.0.1

# 2. 修复问题并测试

# 3. 合并到main和develop
git checkout main
git merge hotfix/1.0.1
git tag -a v1.0.1 -m "Hotfix version 1.0.1"
git push origin main --tags

git checkout develop
git merge hotfix/1.0.1
git push origin develop
```

## 文件版本管理

### 版本信息位置

- **后端**: `backend/app/__init__.py` 中的 `__version__`
- **前端**: `frontend/package.json` 中的 `version`
- **项目**: `VERSION` 文件和 `CHANGELOG.md`

### 版本更新检查单

发布新版本前的检查项：

- [ ] 更新所有版本号文件
- [ ] 更新 CHANGELOG.md
- [ ] 运行完整测试套件
- [ ] 更新 README.md (如需要)
- [ ] 创建发布说明
- [ ] 打包和部署测试

## 标签管理

### 标签命名规范

- 正式版本: `v1.0.0`
- 预发布版本: `v1.1.0-beta.1`
- 热修复版本: `v1.0.1`

### 标签管理命令

```bash
# 创建带注释的标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签到远程
git push origin v1.0.0
git push origin --tags

# 查看标签
git tag -l

# 删除标签
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```

## 自动化工具

### 版本号自动更新脚本

创建 `scripts/update-version.sh` 脚本来自动更新版本号：

```bash
#!/bin/bash
NEW_VERSION=$1

# 更新后端版本
sed -i '' "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" backend/app/__init__.py

# 更新前端版本  
sed -i '' "s/\"version\": \".*\"/\"version\": \"$NEW_VERSION\"/" frontend/package.json

# 更新项目版本
echo $NEW_VERSION > VERSION

echo "版本已更新到 $NEW_VERSION"
```

### 发布自动化

可以使用 GitHub Actions 或其他CI/CD工具实现：

- 自动测试
- 自动构建
- 自动部署
- 自动生成发布说明

## 最佳实践

1. **每次提交都要有清晰的提交信息**
2. **定期合并develop到feature分支**
3. **发布前充分测试**
4. **维护详细的CHANGELOG**
5. **使用Pull Request进行代码审查**
6. **保持分支整洁，及时删除已合并的分支**

## 团队协作

### 提交信息规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型 (type):
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建过程或辅助工具的变动

示例：
```
feat(position): 添加阶段收益计算功能

- 实现买入时间在阶段中间的收益计算逻辑
- 统一今年以来收益与阶段收益计算方法
- 添加阶段收益小计功能

Closes #123
```