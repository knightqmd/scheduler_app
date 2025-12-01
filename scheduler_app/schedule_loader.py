from __future__ import annotations

"""Utilities for loading existing user schedules automatically."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Iterable, Mapping

from .models import ScheduleItem, WeekSchedule

logger = logging.getLogger(__name__)


_DEFAULT_WEEK: Dict[str, Iterable[Mapping[str, str]]] = {
    "周一": [
        {
            "title": "团队例会",
            "start": "09:00",
            "end": "10:00",
            "location": "会议室 A",
            "notes": "同步本周重点",
        },
        {
            "title": "产品评审",
            "start": "15:00",
            "end": "16:00",
            "location": "线上会议",
        },
    ],
    "周三": [
        {
            "title": "需求梳理",
            "start": "14:00",
            "end": "15:30",
            "location": "会议室 B",
        }
    ],
    "周五": [
        {
            "title": "一对一沟通",
            "start": "10:30",
            "end": "11:00",
            "notes": "与直线经理",
        },
        {"title": "健身", "start": "18:00", "end": "19:00"},
    ],
}


def _populate_schedule(schedule: WeekSchedule, entries: Mapping[str, Iterable[Mapping[str, str]]]) -> None:
    for day, items in entries.items():
        for item in items:
            try:
                schedule.add_item(
                    day,
                    ScheduleItem(
                        title=str(item["title"]),
                        start=str(item["start"]),
                        end=str(item["end"]),
                        location=str(item.get("location")) if item.get("location") else None,
                        notes=str(item.get("notes")) if item.get("notes") else None,
                    ),
                )
            except KeyError:
                logger.debug("跳过缺少必填字段的日程条目：%s", item)


def load_existing_schedule(owner: str = "用户", file_path: str | None = None) -> WeekSchedule:
    """Load the user's existing schedule without requiring manual input.

    If ``file_path`` (or environment variable ``SCHEDULE_FILE``) points to a JSON
    file, it should contain a mapping of weekday to a list of items, e.g.::

        {
          "days": {
            "周一": [{"title": "会议", "start": "09:00", "end": "10:00"}],
            "周三": [{"title": "写周报", "start": "16:00", "end": "17:00"}]
          },
          "free_text": "来自日历系统的备注"
        }

    When no external file is provided, a built-in demo schedule is returned so
    that the CLI can run out-of-the-box.
    """

    schedule = WeekSchedule(owner=owner)
    path = file_path or os.environ.get("SCHEDULE_FILE")
    if path:
        candidate = Path(path)
        if candidate.is_file():
            logger.info("从文件加载已有日程：%s", candidate)
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                entries = data.get("days") if isinstance(data, dict) else None
                if isinstance(entries, dict):
                    _populate_schedule(schedule, entries)
                    free_text = data.get("free_text") or data.get("notes")
                    if isinstance(free_text, str):
                        schedule.set_free_text(free_text)
                    return schedule
                logger.warning("日程文件格式无效，期待包含 'days' 字段：%s", data)
            except Exception as exc:  # pragma: no cover - runtime safety
                logger.warning("读取日程文件失败，将使用内置示例：%s", exc)
        else:
            logger.warning("未找到日程文件：%s，改用内置示例", candidate)

    logger.info("未提供日程文件，使用内置示例日程")
    _populate_schedule(schedule, _DEFAULT_WEEK)
    return schedule
