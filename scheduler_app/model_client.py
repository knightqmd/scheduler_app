from __future__ import annotations

import logging
import os
from typing import Optional

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - fallback when SDK is missing
    OpenAI = None  # type: ignore

logger = logging.getLogger(__name__)


class DoubaoModelClient:
    """Thin wrapper around the Doubao (Ark) chat completion endpoint."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("ARK_API_KEY")
        self.base_url = base_url or os.environ.get(
            "ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
        )
        self.model_name = model_name or os.environ.get(
            "ARK_MODEL", "doubao-seed-1-6-251015"
        )
        self._client = None
        if not OpenAI:
            logger.error("未检测到 openai SDK，请先安装依赖：pip install openai")
            return
        if not self.api_key:
            logger.error("未检测到 ARK_API_KEY，无法调用模型")
            return
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        logger.debug(
            "已初始化 DoubaoModelClient，base_url=%s, model=%s",
            self.base_url,
            self.model_name,
        )

    def generate_schedule(self, prompt: str) -> str:
        if not self._client:
            raise RuntimeError(
                "Doubao/OpenAI client not initialized，请确认已安装 openai 且配置 ARK_API_KEY。"
            )
        logger.debug("调用远端模型：%s", self.model_name)
        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的中文日程规划助手。",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as exc:  # pragma: no cover - runtime safety
            logger.warning("调用模型失败：%s", exc)
            raise
