from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, List
import logging

# 导入路由模块
from .routes import nav, strategy, position, trade, dividend
from .database import init_database, get_database_status
from .init_data import init_data_if_needed

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例
app = FastAPI(
    title="Private Fund Management API",
    description="私募基金管理系统后端API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS中间件，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路由 - 健康检查
@app.get("/")
async def root():
    """
    根路径 - 返回API状态信息
    """
    return {
        "message": "Private Fund Management API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

# 健康检查路由
@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {"status": "healthy", "message": "API服务正常运行"}

# API信息路由
@app.get("/api/info")
async def api_info():
    """
    获取API基本信息
    """
    return {
        "api_name": "Private Fund Management",
        "version": "1.0.0",
        "description": "私募基金管理系统API",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "funds": "/api/funds",
            "investors": "/api/investors"
        }
    }

# 已删除冗余的示例基金路由，实际基金管理功能在其他模块中实现

# 数据库状态检查路由
@app.get("/api/database/status")
async def database_status():
    """
    获取数据库连接状态和基本信息
    """
    try:
        status = get_database_status()
        return {
            "status": "success",
            "message": "数据库状态获取成功",
            "data": status
        }
    except Exception as e:
        logger.error(f"获取数据库状态失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取数据库状态失败: {str(e)}"
        )

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    全局异常处理器
    """
    logger.error(f"全局异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "服务器内部错误", "detail": str(exc)}
    )

# 注册路由
app.include_router(nav.router, tags=["净值管理"])
app.include_router(strategy.router, tags=["策略管理"])
app.include_router(position.router, tags=["持仓分析"])
app.include_router(dividend.router, tags=["分红管理"])
app.include_router(trade.router, tags=["交易分析"])

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """
    应用启动时执行
    """
    logger.info("Private Fund Management API 启动成功")
    logger.info("API文档地址: http://localhost:8000/docs")
    
    # 初始化数据库
    try:
        init_database()
        logger.info("数据库初始化成功")
        
        # 初始化示例数据
        init_data_if_needed()
        logger.info("示例数据初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """
    应用关闭时执行
    """
    logger.info("Private Fund Management API 正在关闭...")

# 开发环境启动配置
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )