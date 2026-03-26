"""LLM客户端封装"""
import logging
from openai import OpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM客户端"""

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            default_headers={"X-Model-Provider-Id": "azure_openai"}
        )
        self.model = settings.llm_model

    def chat(self, messages: list, temperature: float = 0.7) -> str:
        """发送聊天请求"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """便捷方法：生成回复"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.chat(messages, temperature)
