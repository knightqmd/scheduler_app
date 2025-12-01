from __future__ import annotations

import json
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
        self._use_mock = False
        if not OpenAI:
            logger.warning(
                "未检测到 openai SDK，已启用内置 mock 响应，运行 `pip install openai` 可调用真实模型。"
            )
            self._use_mock = True
            return
        if not self.api_key:
            logger.warning(
                "未检测到 ARK_API_KEY，已启用内置 mock 响应。设置 ARK_API_KEY 后将调用远端模型。"
            )
            self._use_mock = True
            return
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        logger.debug(
            "已初始化 DoubaoModelClient，base_url=%s, model=%s",
            self.base_url,
            self.model_name,
        )

    def _mock_schedule(self) -> str:
        """Return a deterministic schedule for offline debugging."""

        mock_items = [
            {
                "day": "周一",
                "start": "09:00",
                "end": "10:00",
                "title": "回顾现有日程",
                "notes": "mock 响应用于本地调试",
            },
            {
                "day": "周三",
                "start": "15:00",
                "end": "16:00",
                "title": "处理用户新增需求",
            },
            {
                "day": "周五",
                "start": "17:00",
                "end": "18:00",
                "title": "整理一周总结",
            },
        ]
        return json.dumps(mock_items, ensure_ascii=False, indent=2)

    def generate_schedule(self, prompt: str) -> str:
        if self._use_mock:
            logger.info("使用内置 mock 响应，便于本地调试，无需 ARK_API_KEY。")
            return self._mock_schedule()
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
