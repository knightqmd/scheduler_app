from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Protocol

from .models import UserSchedule

logger = logging.getLogger(__name__)


class ScheduleModel(Protocol):
    """Protocol describing the subset of the LLM client we need."""

    def generate_schedule(self, prompt: str) -> str:
        ...


@dataclass
class ScheduleService:
    """Orchestrates combining user input with existing schedule data."""

    model: ScheduleModel

    def build_prompt(self, user_request: str, existing_schedule: UserSchedule) -> str:
        """Create a structured prompt for the LLM."""
        logger.debug(
            "构建 prompt：user_request=%s, existing_items=%d",
            user_request,
            len(existing_schedule.items),
        )
        prompt = (
            "你是一个日程规划助手。请根据用户的需求生成一个合理的日程安排，"
            "同时兼顾他已有的日程，不要与现有安排冲突。如有需要，可在空闲时间"
            "插入新的任务或优化建议。请用条目形式输出。\n\n"
            f"【用户需求】\n{user_request}\n\n"
            f"【已有日程】\n{existing_schedule.as_markdown()}\n\n"
            "【输出要求】\n- 指明每个任务的时间范围\n- 如果需要调整已有日程，"
            "简单说明原因\n- 汇总给出一天的关键优先级"
        )
        logger.debug("Prompt 内容预览：%s", prompt[:200])
        return prompt

    def plan(self, user_request: str, existing_schedule: UserSchedule) -> str:
        prompt = self.build_prompt(user_request, existing_schedule)
        logger.info("开始调用模型生成日程")
        result = self.model.generate_schedule(prompt)
        logger.info("模型返回内容长度：%d", len(result))
        logger.debug("模型原始输出：%s", result)
        return result
