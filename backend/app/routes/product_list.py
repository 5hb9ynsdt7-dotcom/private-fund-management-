"""
产品清单管理API路由
Product List Management Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import date

from app.database import get_db
from app.models import ProductList, ProductListItem, Fund, Nav

router = APIRouter(
    prefix="/api/product-lists",
    tags=["产品清单管理"]
)


# Pydantic模型
class ProductListItemCreate(BaseModel):
    fund_code: str


class ProductListCreate(BaseModel):
    name: str
    description: str = None
    fund_codes: List[str] = []


class ProductListUpdate(BaseModel):
    name: str = None
    description: str = None
    fund_codes: List[str] = None


class ProductListItemResponse(BaseModel):
    fund_code: str
    fund_name: str
    short_name: str = None
    latest_nav_date: Optional[date] = None

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    id: int
    name: str
    description: str = None
    created_at: str
    updated_at: str
    items: List[ProductListItemResponse] = []

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ProductListResponse], summary="获取所有产品清单")
async def get_all_product_lists(db: Session = Depends(get_db)):
    """获取所有产品清单"""
    lists = db.query(ProductList).all()

    result = []
    for plist in lists:
        items = []
        for item in plist.items:
            fund = db.query(Fund).filter(Fund.fund_code == item.fund_code).first()
            if fund:
                # 查询最新净值日期
                latest_nav = db.query(Nav).filter(
                    Nav.fund_code == fund.fund_code
                ).order_by(Nav.nav_date.desc()).first()

                items.append(ProductListItemResponse(
                    fund_code=fund.fund_code,
                    fund_name=fund.fund_name,
                    short_name=fund.short_name,
                    latest_nav_date=latest_nav.nav_date if latest_nav else None
                ))

        result.append(ProductListResponse(
            id=plist.id,
            name=plist.name,
            description=plist.description,
            created_at=plist.created_at.isoformat(),
            updated_at=plist.updated_at.isoformat(),
            items=items
        ))

    return result


@router.post("/", response_model=ProductListResponse, summary="创建产品清单")
async def create_product_list(
    data: ProductListCreate,
    db: Session = Depends(get_db)
):
    """创建新的产品清单"""
    # 创建清单
    new_list = ProductList(
        name=data.name,
        description=data.description
    )
    db.add(new_list)
    db.flush()
    
    # 添加产品项
    for fund_code in data.fund_codes:
        # 验证基金是否存在
        fund = db.query(Fund).filter(Fund.fund_code == fund_code).first()
        if not fund:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"基金 {fund_code} 不存在"
            )
        
        item = ProductListItem(
            list_id=new_list.id,
            fund_code=fund_code
        )
        db.add(item)
    
    db.commit()
    db.refresh(new_list)
    
    # 构建响应
    items = []
    for item in new_list.items:
        fund = db.query(Fund).filter(Fund.fund_code == item.fund_code).first()
        if fund:
            # 查询最新净值日期
            latest_nav = db.query(Nav).filter(
                Nav.fund_code == fund.fund_code
            ).order_by(Nav.nav_date.desc()).first()

            items.append(ProductListItemResponse(
                fund_code=fund.fund_code,
                fund_name=fund.fund_name,
                short_name=fund.short_name,
                latest_nav_date=latest_nav.nav_date if latest_nav else None
            ))
    
    return ProductListResponse(
        id=new_list.id,
        name=new_list.name,
        description=new_list.description,
        created_at=new_list.created_at.isoformat(),
        updated_at=new_list.updated_at.isoformat(),
        items=items
    )


@router.get("/{list_id}", response_model=ProductListResponse, summary="获取单个产品清单")
async def get_product_list(
    list_id: int,
    db: Session = Depends(get_db)
):
    """获取指定ID的产品清单"""
    plist = db.query(ProductList).filter(ProductList.id == list_id).first()

    if not plist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"产品清单 {list_id} 不存在"
        )

    # 构建响应
    items = []
    for item in plist.items:
        fund = db.query(Fund).filter(Fund.fund_code == item.fund_code).first()
        if fund:
            # 查询最新净值日期
            latest_nav = db.query(Nav).filter(
                Nav.fund_code == fund.fund_code
            ).order_by(Nav.nav_date.desc()).first()

            items.append(ProductListItemResponse(
                fund_code=fund.fund_code,
                fund_name=fund.fund_name,
                short_name=fund.short_name,
                latest_nav_date=latest_nav.nav_date if latest_nav else None
            ))

    return ProductListResponse(
        id=plist.id,
        name=plist.name,
        description=plist.description,
        created_at=plist.created_at.isoformat(),
        updated_at=plist.updated_at.isoformat(),
        items=items
    )


@router.put("/{list_id}", response_model=ProductListResponse, summary="更新产品清单")
async def update_product_list(
    list_id: int,
    data: ProductListUpdate,
    db: Session = Depends(get_db)
):
    """更新产品清单"""
    plist = db.query(ProductList).filter(ProductList.id == list_id).first()

    if not plist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"产品清单 {list_id} 不存在"
        )

    # 更新基本信息
    if data.name is not None:
        plist.name = data.name
    if data.description is not None:
        plist.description = data.description

    # 更新产品列表
    if data.fund_codes is not None:
        # 删除现有的产品项
        db.query(ProductListItem).filter(ProductListItem.list_id == list_id).delete()

        # 添加新的产品项
        for fund_code in data.fund_codes:
            # 验证基金是否存在
            fund = db.query(Fund).filter(Fund.fund_code == fund_code).first()
            if not fund:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"基金 {fund_code} 不存在"
                )

            item = ProductListItem(
                list_id=list_id,
                fund_code=fund_code
            )
            db.add(item)

    db.commit()
    db.refresh(plist)

    # 构建响应
    items = []
    for item in plist.items:
        fund = db.query(Fund).filter(Fund.fund_code == item.fund_code).first()
        if fund:
            # 查询最新净值日期
            latest_nav = db.query(Nav).filter(
                Nav.fund_code == fund.fund_code
            ).order_by(Nav.nav_date.desc()).first()

            items.append(ProductListItemResponse(
                fund_code=fund.fund_code,
                fund_name=fund.fund_name,
                short_name=fund.short_name,
                latest_nav_date=latest_nav.nav_date if latest_nav else None
            ))

    return ProductListResponse(
        id=plist.id,
        name=plist.name,
        description=plist.description,
        created_at=plist.created_at.isoformat(),
        updated_at=plist.updated_at.isoformat(),
        items=items
    )


@router.delete("/{list_id}", summary="删除产品清单")
async def delete_product_list(
    list_id: int,
    db: Session = Depends(get_db)
):
    """删除产品清单"""
    plist = db.query(ProductList).filter(ProductList.id == list_id).first()

    if not plist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"产品清单 {list_id} 不存在"
        )

    db.delete(plist)
    db.commit()

    return {
        "success": True,
        "message": f"产品清单 '{plist.name}' 已删除"
    }
