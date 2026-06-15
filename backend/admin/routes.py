from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.order import Order
from models.query_record import QueryRecord
from models.llm_log import LLMLog
from models.promotion import Promotion
from sqlalchemy import func
import os

router = APIRouter(prefix="/admin", tags=["管理后台"])
templates = Jinja2Templates(directory="admin/templates")

# 硬编码管理员账号（V2.2 简化版）
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123")

def verify_admin(username: str, password: str) -> bool:
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

@router.get("/", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if not verify_admin(username, password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "用户名或密码错误"
        })
    # 简化版：直接跳转 dashboard，实际应生成 session
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    return response

@router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    # 统计数据
    total_users = db.query(User).count()
    total_orders = db.query(Order).count()
    total_revenue = db.query(func.sum(Order.amount)).filter(Order.status == "paid").scalar() or 0
    total_queries = db.query(QueryRecord).count()
    total_llm_calls = db.query(LLMLog).count()
    total_llm_cost = db.query(func.sum(LLMLog.cost_cny)).scalar() or 0
    
    # 最近7天查询趋势
    from datetime import datetime, timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_queries = db.query(QueryRecord).filter(QueryRecord.created_at >= seven_days_ago).count()
    
    # 活跃用户（最近7天有查询的用户）
    active_users = db.query(QueryRecord.user_id).filter(
        QueryRecord.created_at >= seven_days_ago
    ).distinct().count()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": {
            "total_users": total_users,
            "total_orders": total_orders,
            "total_revenue": round(float(total_revenue), 2),
            "total_queries": total_queries,
            "total_llm_calls": total_llm_calls,
            "total_llm_cost": round(float(total_llm_cost), 2),
            "recent_queries": recent_queries,
            "active_users": active_users
        }
    })

@router.get("/promotions", response_class=HTMLResponse)
def admin_promotions(request: Request, db: Session = Depends(get_db)):
    promotions = db.query(Promotion).order_by(Promotion.created_at.desc()).all()
    return templates.TemplateResponse("promotions.html", {
        "request": request,
        "promotions": promotions
    })

@router.post("/promotions/create")
def create_promotion(
    code: str = Form(...),
    name: str = Form(...),
    discount_type: str = Form(...),
    discount_value: float = Form(...),
    valid_days: int = Form(7),
    max_uses: int = Form(100),
    db: Session = Depends(get_db)
):
    promotion = Promotion(
        code=code,
        name=name,
        discount_type=discount_type,
        discount_value=discount_value,
        valid_days=valid_days,
        max_uses=max_uses
    )
    db.add(promotion)
    db.commit()
    return RedirectResponse(url="/admin/promotions", status_code=302)
