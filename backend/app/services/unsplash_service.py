"""Unsplash图片服务"""
import logging
import requests
from typing import Optional, List, Dict
from app.config import get_settings

logger = logging.getLogger(__name__)


class UnsplashService:
    """Unsplash图片服务"""

    def __init__(self):
        settings = get_settings()
        self.access_key = settings.unsplash_access_key
        self.base_url = "https://api.unsplash.com"

    def search_photos(self, query: str, per_page: int = 10) -> List[Dict]:
        """搜索图片"""
        if not self.access_key:
            logger.warning("Unsplash API密钥未配置")
            return []

        try:
            url = f"{self.base_url}/search/photos"
            params = {
                "query": query,
                "per_page": per_page,
                "client_id": self.access_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            photos = []
            for result in results:
                photos.append({
                    "url": result["urls"]["regular"],
                    "thumb_url": result["urls"]["thumb"],
                    "description": result.get("description", "") or result.get("alt_description", ""),
                    "photographer": result["user"]["name"]
                })

            return photos

        except Exception as e:
            logger.error(f"搜索图片失败: {e}")
            return []

    def get_photo_url(self, query: str) -> Optional[str]:
        """获取单张图片URL"""
        photos = self.search_photos(query, per_page=1)
        return photos[0].get("url") if photos else None

    def get_city_photo(self, city: str) -> Optional[str]:
        """获取城市图片"""
        return self.get_photo_url(f"{city} city travel")

    def get_attraction_photo(self, attraction_name: str, city: str) -> Optional[str]:
        """获取景点图片"""
        return self.get_photo_url(f"{attraction_name} {city}")
