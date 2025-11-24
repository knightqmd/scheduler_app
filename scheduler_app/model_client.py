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
        allow_mock: bool = True,
    ) -> None:
        self.api_key = api_key or os.environ.get("ARK_API_KEY")
        self.base_url = base_url or os.environ.get(
            "ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
        )
        self.model_name = model_name or os.environ.get(
            "ARK_MODEL", "doubao-seed-1-6-251015"
        )
        self.allow_mock = allow_mock
        self._client = None
        if self.api_key and OpenAI:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            logger.debug(
                "已初始化 DoubaoModelClient，base_url=%s, model=%s",
                self.base_url,
                self.model_name,
            )
        else:
            logger.warning(
                "DoubaoModelClient 运行于 mock 模式（未检测到 SDK 或 API Key）"
            )

    def generate_schedule(self, prompt: str) -> str:
        if self._client:
            logger.debug("调用远端模型：%s", self.model_name)
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
        if not self.allow_mock:
            raise RuntimeError(
                "OpenAI/Doubao client not initialized. "
                "Please install openai and set ARK_API_KEY."
            )
        logger.debug("使用 mock 响应，prompt 首行：%s", prompt.splitlines()[0])
        return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        # Simple deterministic fallback so the CLI can demo without API access.
        lines = [line for line in prompt.splitlines() if line.startswith(" - ")]
        baseline = "\n".join(lines[-3:])
        return (
            "【模拟日程】\n"
            "08:00-09:00 | 晨间准备与优先事项确认\n"
            "09:00-11:30 | 处理用户请求中的主要任务\n"
            "14:00-16:00 | 与已有日程保持协调，预留机动时间\n"
            "20:00-20:30 | 回顾一天并记录待办\n\n"
            f"提示：以下为已有条目摘要，供参考：\n{baseline or '（无）'}"
        )
