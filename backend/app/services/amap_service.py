"""高德地图API服务"""
import logging
import requests
from typing import Optional, List, Dict, Any
from app.config import get_settings

logger = logging.getLogger(__name__)


class AmapService:
    """高德地图API服务"""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.amap_api_key
        self.base_url = "https://restapi.amap.com/v3"

    def text_search(self, keywords: str, city: str, types: str = "", page: int = 1, page_size: int = 10) -> List[Dict]:
        """POI文本搜索"""
        try:
            url = f"{self.base_url}/place/text"
            params = {
                "key": self.api_key,
                "keywords": keywords,
                "city": city,
                "citylimit": "true",
                "output": "json",
                "offset": page_size,
                "page": page
            }
            if types:
                params["types"] = types

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "1":
                pois = data.get("pois", [])
                results = []
                for poi in pois:
                    location = poi.get("location", "").split(",")
                    results.append({
                        "name": poi.get("name", ""),
                        "address": poi.get("address", ""),
                        "type": poi.get("type", ""),
                        "location": {
                            "longitude": float(location[0]) if len(location) == 2 else 0,
                            "latitude": float(location[1]) if len(location) == 2 else 0
                        },
                        "rating": poi.get("biz_ext", {}).get("rating", ""),
                        "tel": poi.get("tel", "")
                    })
                return results
            else:
                logger.warning(f"高德地图搜索失败: {data.get('info')}")
                return []

        except Exception as e:
            logger.error(f"POI搜索失败: {e}")
            return []

    def get_weather(self, city: str) -> Dict[str, Any]:
        """获取天气预报"""
        try:
            url = f"{self.base_url}/weather/weatherInfo"
            params = {
                "key": self.api_key,
                "city": city,
                "extensions": "all",  # 获取预报
                "output": "json"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "1":
                forecasts = data.get("forecasts", [])
                if forecasts:
                    return {
                        "city": forecasts[0].get("city", ""),
                        "province": forecasts[0].get("province", ""),
                        "casts": forecasts[0].get("casts", [])
                    }
            logger.warning(f"天气查询失败: {data.get('info')}")
            return {}

        except Exception as e:
            logger.error(f"天气查询失败: {e}")
            return {}

    def search_hotels(self, city: str, keywords: str = "酒店", page_size: int = 10) -> List[Dict]:
        """搜索酒店"""
        return self.text_search(keywords, city, types="100000", page_size=page_size)

    def search_attractions(self, city: str, keywords: str = "景点", page_size: int = 15) -> List[Dict]:
        """搜索景点"""
        # 风景名胜: 110000
        return self.text_search(keywords, city, types="110000", page_size=page_size)

    def search_restaurants(self, city: str, keywords: str = "餐厅", page_size: int = 10) -> List[Dict]:
        """搜索餐厅"""
        # 餐饮: 050000
        return self.text_search(keywords, city, types="050000", page_size=page_size)
