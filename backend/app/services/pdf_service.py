"""
图片导出服务
Image Export Service
实现持仓详情页面的图片导出功能
"""

import logging
from datetime import date
from typing import Optional
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.orm import Session
from io import BytesIO

logger = logging.getLogger(__name__)


class ImageExportService:
    """图片导出服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_client_position_image(
        self, 
        group_id: str, 
        frontend_url: str = "http://localhost:3001"
    ) -> tuple[BytesIO, str]:
        """
        生成客户持仓详情PNG图片
        
        Args:
            group_id: 客户集团号
            frontend_url: 前端应用URL
            
        Returns:
            tuple[BytesIO, str]: (PNG图片文件流, 文件名)
        """
        try:
            # 1. 获取客户信息
            from ..models import Client
            client = self.db.query(Client).filter(Client.group_id == group_id).first()
            if not client:
                raise HTTPException(status_code=404, detail=f"客户 {group_id} 不存在")
            
            # 2. 获取存量时间（最新更新日期）
            from ..models import Position
            latest_position = self.db.query(Position)\
                                   .filter(Position.group_id == group_id)\
                                   .order_by(Position.stock_date.desc())\
                                   .first()
            
            stock_date = latest_position.stock_date if latest_position else date.today()
            
            # 3. 生成文件名：客户名_存量日期.png
            client_name = self._get_client_display_name(client.obscured_name)
            filename = f"{client_name}_{stock_date.strftime('%Y-%m-%d')}.png"
            
            # 4. 生成PNG图片  
            # 检查frontend_url是否包含完整路径
            from urllib.parse import unquote
            decoded_url = unquote(frontend_url)
            
            if "/position/detail/" in decoded_url:
                # 前端传递的是完整URL（已包含路径和参数）
                final_url = decoded_url
            else:
                # 传统方式，构造基础URL
                final_url = f"{decoded_url}/position/detail/{group_id}"
                
            image_buffer = await self._generate_image_from_url(final_url)
            
            logger.info(f"PNG图片生成成功: {filename}")
            return image_buffer, filename
            
        except Exception as e:
            logger.error(f"图片生成失败: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"图片生成失败: {str(e)}"
            )
    
    def _get_client_display_name(self, obscured_name: Optional[str]) -> str:
        """获取客户显示名称（去掉*后的部分）"""
        if not obscured_name:
            return "客户"
        
        # 提取*前的部分作为显示名称
        display_name = obscured_name.split('*')[0] if '*' in obscured_name else obscured_name
        return display_name or "客户"
    
    async def _generate_image_from_url(self, url: str) -> BytesIO:
        """
        从URL生成PNG图片
        
        使用Playwright截图功能
        """
        try:
            return await self._generate_screenshot_with_playwright(url)
        except ImportError:
            logger.error("Playwright不可用，无法生成截图")
            raise HTTPException(status_code=500, detail="图片生成服务不可用")
        except Exception as e:
            logger.error(f"Playwright截图失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"图片生成失败: {str(e)}")
    
    async def _generate_screenshot_with_playwright(self, url: str) -> BytesIO:
        """使用Playwright生成PNG截图"""
        from playwright.async_api import async_playwright
        
        image_buffer = BytesIO()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 设置较大的视窗大小以确保内容完整显示
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # 等待页面完全加载
            logger.info(f"正在访问URL: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # 等待关键元素加载完成
            try:
                logger.info("等待页面元素加载...")
                
                # 等待数据加载完成
                await page.wait_for_selector('.revenue-overview', timeout=20000)
                logger.info("收益概览加载完成")
                
                await page.wait_for_selector('.charts-section', timeout=20000)
                logger.info("图表区域加载完成")
                
                # 等待图表实际渲染完成
                await page.wait_for_selector('.chart-container > div', timeout=20000)
                logger.info("图表容器加载完成")
                
                await page.wait_for_selector('.position-table', timeout=20000)
                logger.info("表格区域加载完成")
                
                # 等待表格数据加载
                await page.wait_for_selector('.position-table tbody tr', timeout=20000)
                logger.info("表格数据加载完成")
                
                # 检查是否有阶段收益时间段显示
                try:
                    period_display = await page.query_selector('.period-display')
                    if period_display:
                        logger.info("检测到阶段收益时间段显示")
                        await page.wait_for_selector('.period-display .el-alert', timeout=10000)
                        logger.info("阶段收益时间段显示加载完成")
                    else:
                        logger.info("未检测到阶段收益时间段显示")
                except Exception as e:
                    logger.info(f"阶段收益时间段检查失败: {e}")
                
                # 等待图表和数据完全渲染
                await page.wait_for_timeout(5000)
                logger.info("等待渲染完成")
                
                # 强制触发图表重新渲染
                await page.evaluate("""
                    () => {
                        // 触发ECharts图表重新渲染
                        window.dispatchEvent(new Event('resize'));
                        
                        // 如果有echarts实例，手动调用resize
                        if (window.echarts) {
                            const charts = document.querySelectorAll('.chart-container > div');
                            charts.forEach(chart => {
                                const instance = window.echarts.getInstanceByDom(chart);
                                if (instance) {
                                    instance.resize();
                                }
                            });
                        }
                    }
                """)
                
                # 等待重新渲染完成
                await page.wait_for_timeout(2000)
                
                # 优化截图显示样式
                await page.add_style_tag(content="""
                    /* 完全隐藏侧边栏和顶部导航 */
                    .el-aside { display: none !important; }
                    .sidebar { display: none !important; }
                    .app-header { display: none !important; }
                    .el-header { display: none !important; }
                    .header-actions { display: none !important; }
                    .table-controls { display: none !important; }
                    
                    /* 隐藏底层持仓分析部分 */
                    .underlying-analysis { display: none !important; }
                    .underlying-position-analysis { display: none !important; }
                    
                    /* 阶段收益时间段提示优化 - 确保在图片中显示 */
                    .period-display {
                        margin: 16px 0 24px 0 !important;
                        position: relative !important;
                        z-index: 10 !important;
                        display: block !important;
                        visibility: visible !important;
                        opacity: 1 !important;
                    }
                    .period-display .el-alert {
                        font-size: 16px !important;
                        font-weight: 600 !important;
                        background-color: #e1f3d8 !important;
                        border-color: #67c23a !important;
                        color: #529b2e !important;
                        padding: 12px 16px !important;
                        border-radius: 4px !important;
                        box-shadow: 0 2px 4px rgba(103, 194, 58, 0.12) !important;
                    }
                    .period-display .el-alert .el-alert__content {
                        font-size: 16px !important;
                        font-weight: 600 !important;
                    }
                    
                    /* 重新布局主容器 */
                    .app-container { height: auto !important; }
                    .el-container { margin: 0 !important; padding: 0 !important; }
                    .el-main { 
                        margin-left: 0 !important; 
                        padding: 0 !important;
                        width: 100% !important;
                        background-color: white !important;
                    }
                    .position-detail { 
                        padding: 20px !important; 
                        width: 100% !important;
                        max-width: none !important;
                        background-color: white !important;
                    }
                    
                    /* 页面标题优化 */
                    .page-header { 
                        margin-bottom: 20px !important;
                    }
                    .page-header h2 {
                        font-size: 24px !important;
                        color: #303133 !important;
                    }
                    
                    /* 收益概览卡片优化 */
                    .revenue-overview { 
                        margin-bottom: 20px !important;
                    }
                    .overview-card {
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                    }
                    
                    /* 图表区域优化 */
                    .charts-section { 
                        margin-bottom: 20px !important;
                        width: 100% !important;
                    }
                    .chart-card { 
                        height: 400px !important;
                        min-height: 400px !important;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                        margin-bottom: 20px !important;
                    }
                    .chart-container { 
                        height: 350px !important; 
                        width: 100% !important;
                        min-height: 350px !important;
                    }
                    
                    /* 表格区域优化 */
                    .position-table-card {
                        margin-bottom: 20px !important;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                    }
                    .position-table {
                        width: 100% !important;
                        font-size: 12px !important;
                    }
                    .position-table th {
                        padding: 10px 8px !important;
                        background-color: #fafafa !important;
                        font-weight: 600 !important;
                        border-bottom: 2px solid #e4e7ed !important;
                    }
                    .position-table td {
                        padding: 8px 8px !important;
                        border-bottom: 1px solid #ebeef5 !important;
                    }
                    
                    /* 图片导出专用表格列宽调整 - 撑满整个区域 */
                    .position-table {
                        table-layout: fixed !important;
                        width: 1880px !important;
                        min-width: 1880px !important;
                    }
                    
                    /* 统一设置所有表格：基金名称375px，其他列平均分配 */
                    .position-table .el-table__header-wrapper th:nth-child(1),
                    .position-table .el-table__body-wrapper td:nth-child(1) {
                        width: 375px !important;
                        min-width: 375px !important;
                    }
                    
                    /* 其他列平均分配剩余空间：(1880-375)/11 ≈ 137px */
                    .position-table .el-table__header-wrapper th:nth-child(n+2),
                    .position-table .el-table__body-wrapper td:nth-child(n+2) {
                        width: 137px !important;
                        min-width: 137px !important;
                    }
                    
                    /* 确保Element Plus组件正确显示 */
                    .el-card {
                        border: 1px solid #ebeef5 !important;
                        border-radius: 4px !important;
                    }
                    .el-statistic {
                        text-align: center !important;
                    }
                """)
                
                # 等待样式生效和重新渲染
                await page.wait_for_timeout(3000)
                
                # 调试：检查页面内容
                try:
                    chart_count = await page.evaluate('() => document.querySelectorAll(".chart-container > div").length')
                    logger.info(f"找到 {chart_count} 个图表容器")
                    
                    table_rows = await page.evaluate('() => document.querySelectorAll(".position-table tbody tr").length')
                    logger.info(f"找到 {table_rows} 行表格数据")
                    
                    overview_cards = await page.evaluate('() => document.querySelectorAll(".overview-card").length')
                    logger.info(f"找到 {overview_cards} 个收益卡片")
                    
                    # 检查阶段收益时间段显示
                    period_display_count = await page.evaluate('() => document.querySelectorAll(".period-display").length')
                    logger.info(f"找到 {period_display_count} 个阶段收益时间段显示")
                    
                    if period_display_count > 0:
                        period_text = await page.evaluate('() => {const el = document.querySelector(".period-display .el-alert"); return el ? el.textContent : "无文本"}')
                        logger.info(f"阶段收益时间段文本: {period_text}")
                    
                except Exception as e:
                    logger.warning(f"调试信息获取失败: {e}")
                
            except Exception as e:
                logger.warning(f"等待页面元素超时: {str(e)}")
            
            # 找到主内容区域进行截图
            main_element = await page.query_selector('.position-detail')
            if main_element:
                logger.info("截图主内容区域")
                screenshot_bytes = await main_element.screenshot(
                    type='png'  # PNG不支持quality参数
                )
            else:
                logger.info("截图整个页面")
                screenshot_bytes = await page.screenshot(
                    type='png',
                    full_page=True  # 全页截图，PNG不支持quality参数
                )
            
            await browser.close()
            
            image_buffer.write(screenshot_bytes)
            image_buffer.seek(0)
            
        return image_buffer