from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ScheduleItem:
    """Represents a single event in the user's calendar."""

    title: str
    start: str
    end: str
    location: Optional[str] = None
    notes: Optional[str] = None

    def as_bullet(self) -> str:
        details = [f"{self.start} → {self.end}", self.title]
        if self.location:
            details.append(f"@ {self.location}")
        if self.notes:
            details.append(f"({self.notes})")
        return " - " + " | ".join(details)


@dataclass
class UserSchedule:
    """Container for a list of scheduled events."""

    owner: str
    items: List[ScheduleItem] = field(default_factory=list)

    def add_item(self, item: ScheduleItem) -> None:
        self.items.append(item)

    def as_markdown(self) -> str:
        if not self.items:
            return "当前用户没有已知日程。"
        bullets = "\n".join(item.as_bullet() for item in self.items)
        return f"用户 {self.owner} 已有日程：\n{bullets}"


@dataclass
class WeekSchedule:
    """Stores schedule items grouped by weekday."""

    owner: str
    days: Dict[str, List[ScheduleItem]] = field(default_factory=dict)
    free_text: Optional[str] = None

    def add_item(self, day: str, item: ScheduleItem) -> None:
        """Add an item under a weekday key, preserving insertion order."""
        if day not in self.days:
            self.days[day] = []
        self.days[day].append(item)

    def set_free_text(self, text: str) -> None:
        self.free_text = text.strip() or None

    def as_markdown(self) -> str:
        blocks: List[str] = []
        if self.free_text:
            blocks.append("用户提供的日程描述：")
            blocks.append(self.free_text)
        if not self.days:
            if blocks:
                return "\n".join(blocks)
            return "当前一周暂无日程。"
        blocks: List[str] = []
        for day, items in self.days.items():
            blocks.append(f"{day}：")
            if not items:
                blocks.append(" - （无计划）")
                continue
            blocks.extend(item.as_bullet() for item in items)
        header = f"用户 {self.owner} 一周日程：\n"
        if self.free_text:
            header += "（以下基于用户的自由描述与已有条目整理）\n"
        return header + "\n".join(blocks)
