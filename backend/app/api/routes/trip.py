"""旅行规划API路由"""
import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import TripPlanRequest, TripPlan
from app.agents.trip_planner import get_trip_planner_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trip", tags=["旅行规划"])


@router.post("/plan", response_model=TripPlan)
async def create_trip_plan(request: TripPlanRequest) -> TripPlan:
    """
    创建旅行计划

    - **city**: 目的地城市
    - **start_date**: 开始日期 (YYYY-MM-DD)
    - **end_date**: 结束日期 (YYYY-MM-DD)
    - **days**: 旅行天数
    - **preferences**: 旅行偏好
    - **budget**: 预算等级
    - **transportation**: 交通方式
    - **accommodation**: 住宿类型
    """
    try:
        logger.info(f"收到旅行规划请求: {request.city}, {request.days}天")

        agent = get_trip_planner_agent()
        trip_plan = agent.plan_trip(request)

        logger.info(f"旅行规划完成: {len(trip_plan.days)}天行程")
        return trip_plan

    except Exception as e:
        logger.error(f"旅行规划失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"旅行规划失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "trip-planner"}
