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
    tag: Optional[str] = None  # e.g., 短期提醒 / 长期习惯

    def as_bullet(self) -> str:
        details = [f"{self.start} → {self.end}", self.title]
        if self.location:
            details.append(f"@ {self.location}")
        if self.notes:
            details.append(f"({self.notes})")
        if self.tag:
            details.append(f"[{self.tag}]")
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
        header_lines: List[str] = []
        body_lines: List[str] = []
        if self.free_text:
            header_lines.append("用户提供的日程描述：")
            header_lines.append(self.free_text)
        if not self.days:
            if header_lines:
                return "\n".join(header_lines)
            return "当前一周暂无日程。"
        for day, items in self.days.items():
            body_lines.append(f"{day}：")
            if not items:
                body_lines.append(" - （无计划）")
                continue
            body_lines.extend(item.as_bullet() for item in items)
        header = f"用户 {self.owner} 一周日程：\n"
        if self.free_text:
            header += "（以下基于用户的自由描述与已有条目整理）\n"
        prefix = "\n".join(header_lines)
        if prefix:
            prefix += "\n"
        return prefix + header + "\n".join(body_lines)
