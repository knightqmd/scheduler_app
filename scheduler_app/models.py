from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


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
