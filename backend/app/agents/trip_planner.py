"""旅行规划Agent"""
import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.agents.llm import LLMClient
from app.agents.prompts import PLANNER_AGENT_PROMPT
from app.services.amap_service import AmapService
from app.services.unsplash_service import UnsplashService
from app.models.schemas import TripPlanRequest, TripPlan, Attraction, Location

logger = logging.getLogger(__name__)


class TripPlannerAgent:
    """旅行规划Agent - 协调多个子任务"""

    def __init__(self):
        self.llm = LLMClient()
        self.amap_service = AmapService()
        self.unsplash_service = UnsplashService()

    def plan_trip(self, request: TripPlanRequest) -> TripPlan:
        """生成旅行计划"""
        logger.info(f"开始规划旅行: {request.city}, {request.days}天")

        # 步骤1: 搜索景点
        logger.info("步骤1: 搜索景点...")
        attractions_data = self._search_attractions(request.city, request.preferences)

        # 步骤2: 查询天气
        logger.info("步骤2: 查询天气...")
        weather_data = self._get_weather(request.city)

        # 步骤3: 搜索酒店
        logger.info("步骤3: 搜索酒店...")
        hotels_data = self._search_hotels(request.city, request.accommodation)

        # 步骤4: 生成完整计划
        logger.info("步骤4: 生成行程计划...")
        trip_plan = self._generate_plan(request, attractions_data, weather_data, hotels_data)

        # 步骤5: 为景点添加图片
        logger.info("步骤5: 获取景点图片...")
        self._add_attraction_images(trip_plan)

        logger.info("旅行规划完成!")
        return trip_plan

    def _search_attractions(self, city: str, preferences: str) -> List[Dict]:
        """搜索景点"""
        # 根据偏好选择搜索关键词
        keyword_map = {
            "历史文化": "博物馆 故宫 古迹",
            "自然风光": "公园 风景区 自然",
            "现代都市": "商业街 购物中心 地标",
            "美食体验": "小吃街 美食 特色餐厅",
            "休闲娱乐": "游乐园 娱乐 休闲",
        }
        keywords = keyword_map.get(preferences, "景点 旅游")

        # 搜索主要景点
        attractions = self.amap_service.search_attractions(city, keywords, page_size=15)

        if not attractions:
            # 如果没有结果，使用通用关键词
            attractions = self.amap_service.search_attractions(city, "景点", page_size=15)

        return attractions

    def _get_weather(self, city: str) -> Dict[str, Any]:
        """获取天气预报"""
        return self.amap_service.get_weather(city)

    def _search_hotels(self, city: str, accommodation_type: str) -> List[Dict]:
        """搜索酒店"""
        keyword_map = {
            "经济型酒店": "快捷酒店",
            "舒适型酒店": "商务酒店",
            "高档酒店": "五星酒店",
            "民宿": "民宿 客栈",
        }
        keywords = keyword_map.get(accommodation_type, "酒店")
        return self.amap_service.search_hotels(city, keywords, page_size=5)

    def _generate_plan(
        self,
        request: TripPlanRequest,
        attractions_data: List[Dict],
        weather_data: Dict,
        hotels_data: List[Dict]
    ) -> TripPlan:
        """使用LLM生成完整的旅行计划"""

        # 构建查询
        query = self._build_planner_query(request, attractions_data, weather_data, hotels_data)

        # 调用LLM生成计划
        response = self.llm.generate(
            system_prompt=PLANNER_AGENT_PROMPT,
            user_prompt=query,
            temperature=0.7
        )

        # 解析JSON响应
        trip_plan = self._parse_plan_response(response, request)
        return trip_plan

    def _build_planner_query(
        self,
        request: TripPlanRequest,
        attractions_data: List[Dict],
        weather_data: Dict,
        hotels_data: List[Dict]
    ) -> str:
        """构建规划Agent的查询"""

        # 格式化景点数据
        attractions_text = self._format_attractions(attractions_data)

        # 格式化天气数据
        weather_text = self._format_weather(weather_data, request.start_date, request.days)

        # 格式化酒店数据
        hotels_text = self._format_hotels(hotels_data)

        return f"""
请根据以下信息生成{request.city}的{request.days}日旅行计划:

**用户需求:**
- 目的地: {request.city}
- 日期: {request.start_date} 至 {request.end_date}
- 天数: {request.days}天
- 偏好: {request.preferences}
- 预算等级: {request.budget}
- 交通方式: {request.transportation}
- 住宿类型: {request.accommodation}

**可选景点信息:**
{attractions_text}

**天气预报:**
{weather_text}

**可选酒店信息:**
{hotels_text}

请根据以上信息生成详细的旅行计划，必须使用提供的景点和酒店数据中的真实位置坐标。
"""

    def _format_attractions(self, attractions: List[Dict]) -> str:
        """格式化景点数据"""
        if not attractions:
            return "暂无景点数据"

        lines = []
        for i, attr in enumerate(attractions[:15], 1):
            loc = attr.get("location", {})
            lines.append(
                f"{i}. {attr.get('name', '未知')}\n"
                f"   地址: {attr.get('address', '未知')}\n"
                f"   类型: {attr.get('type', '景点')}\n"
                f"   坐标: ({loc.get('longitude', 0)}, {loc.get('latitude', 0)})\n"
                f"   评分: {attr.get('rating', '暂无')}"
            )
        return "\n".join(lines)

    def _format_weather(self, weather_data: Dict, start_date: str, days: int) -> str:
        """格式化天气数据"""
        if not weather_data:
            return "暂无天气数据"

        casts = weather_data.get("casts", [])
        if not casts:
            return "暂无天气预报"

        lines = [f"城市: {weather_data.get('city', '未知')}"]
        for cast in casts[:days]:
            lines.append(
                f"- {cast.get('date', '')}: "
                f"白天{cast.get('dayweather', '')} {cast.get('daytemp', '')}°C, "
                f"夜间{cast.get('nightweather', '')} {cast.get('nighttemp', '')}°C, "
                f"{cast.get('daywind', '')}风 {cast.get('daypower', '')}级"
            )
        return "\n".join(lines)

    def _format_hotels(self, hotels: List[Dict]) -> str:
        """格式化酒店数据"""
        if not hotels:
            return "暂无酒店数据"

        lines = []
        for i, hotel in enumerate(hotels[:5], 1):
            loc = hotel.get("location", {})
            lines.append(
                f"{i}. {hotel.get('name', '未知')}\n"
                f"   地址: {hotel.get('address', '未知')}\n"
                f"   坐标: ({loc.get('longitude', 0)}, {loc.get('latitude', 0)})\n"
                f"   评分: {hotel.get('rating', '暂无')}"
            )
        return "\n".join(lines)

    def _parse_plan_response(self, response: str, request: TripPlanRequest) -> TripPlan:
        """解析LLM响应为TripPlan对象"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return TripPlan(**data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
        except Exception as e:
            logger.error(f"计划解析失败: {e}")

        # 返回默认计划
        logger.warning("使用默认计划")
        return self._create_default_plan(request)

    def _create_default_plan(self, request: TripPlanRequest) -> TripPlan:
        """创建默认的旅行计划"""
        from app.models.schemas import DayPlan, WeatherInfo, Budget, Meal, Hotel

        days = []
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")

        for i in range(request.days):
            current_date = start_date + timedelta(days=i)
            days.append(DayPlan(
                date=current_date.strftime("%Y-%m-%d"),
                day_index=i,
                description=f"第{i+1}天行程",
                transportation=request.transportation,
                accommodation=request.accommodation,
                attractions=[],
                meals=[
                    Meal(type="breakfast", name="酒店早餐", estimated_cost=30),
                    Meal(type="lunch", name="当地餐厅", estimated_cost=50),
                    Meal(type="dinner", name="特色餐厅", estimated_cost=80),
                ]
            ))

        return TripPlan(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=days,
            weather_info=[],
            overall_suggestions="建议提前查看天气预报，合理安排行程。",
            budget=Budget(
                total_attractions=0,
                total_hotels=0,
                total_meals=160 * request.days,
                total_transportation=100,
                total=160 * request.days + 100
            )
        )

    def _add_attraction_images(self, trip_plan: TripPlan) -> None:
        """为景点添加图片"""
        for day in trip_plan.days:
            for attraction in day.attractions:
                if not attraction.image_url:
                    image_url = self.unsplash_service.get_attraction_photo(
                        attraction.name,
                        trip_plan.city
                    )
                    if image_url:
                        attraction.image_url = image_url


# 单例实例
_trip_planner_agent: Optional[TripPlannerAgent] = None


def get_trip_planner_agent() -> TripPlannerAgent:
    """获取TripPlannerAgent单例"""
    global _trip_planner_agent
    if _trip_planner_agent is None:
        _trip_planner_agent = TripPlannerAgent()
    return _trip_planner_agent
