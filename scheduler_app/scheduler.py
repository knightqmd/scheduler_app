from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Protocol, Tuple, Union

from .models import UserSchedule, WeekSchedule

logger = logging.getLogger(__name__)


class ScheduleModel(Protocol):
    """Protocol describing the subset of the LLM client we need."""

    def generate_schedule(self, prompt: str) -> str:
        ...


@dataclass
class ScheduleService:
    """Orchestrates combining user input with existing schedule data."""

    model: ScheduleModel

    def _normalize_week_schedule(
        self, existing_schedule: Union[WeekSchedule, UserSchedule]
    ) -> Tuple[WeekSchedule, int]:
        """Ensure downstream prompt always sees a WeekSchedule."""
        if isinstance(existing_schedule, WeekSchedule):
            count = sum(len(items) for items in existing_schedule.days.values())
            return existing_schedule, count
        if isinstance(existing_schedule, UserSchedule):
            wrapped = WeekSchedule(owner=existing_schedule.owner)
            for item in existing_schedule.items:
                wrapped.add_item("未指定", item)
            return wrapped, len(existing_schedule.items)
        raise TypeError("existing_schedule must be WeekSchedule or UserSchedule")

    def build_prompt(
        self, user_request: str, existing_schedule: Union[WeekSchedule, UserSchedule]
    ) -> str:
        """Create a structured prompt for the LLM."""
        normalized_schedule, count = self._normalize_week_schedule(existing_schedule)
        logger.debug(
            "构建 prompt：user_request=%s, existing_items=%d",
            user_request,
            count,
        )
        prompt = (
            "你是一个日程规划助手。请根据用户的新增需求与下方提供的一周日程，"
            "生成一周的合理安排，不要与现有安排冲突。保持现有日程不变，除非冲突必须调整。\n\n"
            f"【用户需求】\n{user_request}\n\n"
            f"【本周日程（请作为输入上下文一并纳入规划）】\n{normalized_schedule.as_markdown()}\n\n"
            "【输出格式（必须严格遵守，仅输出 JSON，不要添加额外说明）】\n"
            "[\n"
            '  {"day":"周一","start":"09:00","end":"10:30","title":"事项","location":"可选","notes":"可选"},\n'
            "  ... 按需添加周二至周日的任务 ...\n"
            "]\n"
            "- day 取值仅限：周一,周二,周三,周四,周五,周六,周日\n"
            "- start/end 必须为 24 小时制 HH:MM，start < end\n"
            "- title 必填，location/notes 可为空字符串\n"
            "- 保持与输入日程不冲突；若需要调整已有安排，请直接输出调整后的时间段"
        )
        logger.debug("Prompt 内容预览：%s", prompt[:200])
        return prompt

    def plan(
        self, user_request: str, existing_schedule: Union[WeekSchedule, UserSchedule]
    ) -> str:
        prompt = self.build_prompt(user_request, existing_schedule)
        logger.info("开始调用模型生成日程")
        result = self.model.generate_schedule(prompt)
        logger.info("模型返回内容长度：%d", len(result))
        logger.debug("模型原始输出：%s", result)
        return result
