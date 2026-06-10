"""事件埋点 & 数据统计路由"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models.event import Event
from utils.jwt_utils import get_current_user

router = APIRouter(prefix="/api/v1/events", tags=["事件埋点"])


# ============================================================
# Pydantic 请求/响应模型
# ============================================================


class TrackEventRequest(BaseModel):
    """事件上报请求"""

    event_type: str = Field(
        ...,
        description="事件类型",
        pattern=r"^(symptom_select|pay_modal_show|pay_click|pay_success|summary_generate|share_click)$",
    )
    event_data: Dict[str, Any] = Field(default_factory=dict, description="事件附加数据")


class TrackEventResponse(BaseModel):
    """事件上报响应"""

    success: bool = True
    message: str = "事件已记录"


class EventStatsItem(BaseModel):
    """事件统计项"""

    event_type: str
    count: int
    last_hour: int = 0
    today: int = 0


class EventStatsResponse(BaseModel):
    """事件统计响应"""

    total: int
    items: List[EventStatsItem]


# ============================================================
# API 接口
# ============================================================


@router.post("/track", response_model=TrackEventResponse)
def track_event(
    request: TrackEventRequest,
    db: Session = Depends(get_db),
    current_user: Optional[Any] = Depends(get_current_user),
):
    """上报事件（埋点）"""
    user_id = None
    if current_user and hasattr(current_user, "id"):
        user_id = current_user.id

    event = Event(
        user_id=user_id,
        event_type=request.event_type,
        event_data=request.event_data,
        created_at=datetime.now(),
    )
    db.add(event)
    db.commit()

    return TrackEventResponse(success=True, message="事件已记录")


@router.get("/stats", response_model=EventStatsResponse)
def get_event_stats(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """查询事件统计数据（管理后台用）"""
    # 检查是否为管理员（简单权限校验）
    if not current_user or getattr(current_user, "role", None) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可查看统计数据",
        )

    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 查询所有事件类型及其总数
    total = db.query(func.count(Event.id)).scalar() or 0

    # 按 event_type 分组统计
    rows = (
        db.query(
            Event.event_type,
            func.count(Event.id).label("count"),
        )
        .group_by(Event.event_type)
        .all()
    )

    items = []
    for row in rows:
        event_type = row.event_type
        count = row.count

        # 近1小时统计
        last_hour = (
            db.query(func.count(Event.id))
            .filter(
                Event.event_type == event_type,
                Event.created_at >= one_hour_ago,
            )
            .scalar()
            or 0
        )

        # 今日统计
        today = (
            db.query(func.count(Event.id))
            .filter(
                Event.event_type == event_type,
                Event.created_at >= today_start,
            )
            .scalar()
            or 0
        )

        items.append(
            EventStatsItem(
                event_type=event_type,
                count=count,
                last_hour=last_hour,
                today=today,
            )
        )

    return EventStatsResponse(total=total, items=items)
