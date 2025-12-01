from __future__ import annotations

"""SQLite-backed storage for persisting the weekly schedule."""

import sqlite3
from pathlib import Path
from typing import Iterable

from .models import ScheduleItem, WeekSchedule


class ScheduleStorage:
    """Persist and load weekly schedules using SQLite."""

    def __init__(self, db_path: str | Path = "data/schedule.db", owner: str = "用户") -> None:
        self.db_path = Path(db_path)
        self.owner = owner
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schedule_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    day TEXT NOT NULL,
                    start TEXT NOT NULL,
                    end TEXT NOT NULL,
                    title TEXT NOT NULL,
                    location TEXT,
                    notes TEXT,
                    tag TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schedule_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            # Lightweight migration for missing tag column
            try:
                conn.execute("ALTER TABLE schedule_items ADD COLUMN tag TEXT")
            except sqlite3.OperationalError:
                pass  # column already exists
            try:
                conn.execute("ALTER TABLE schedule_meta ADD COLUMN value TEXT")
            except sqlite3.OperationalError:
                pass

    def _write_items(self, conn: sqlite3.Connection, schedule: WeekSchedule) -> None:
        conn.execute("DELETE FROM schedule_items")
        for day, items in schedule.days.items():
            for item in items:
                conn.execute(
                    """
                    INSERT INTO schedule_items (day, start, end, title, location, notes, tag)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (day, item.start, item.end, item.title, item.location, item.notes, item.tag),
                )

    def _write_meta(self, conn: sqlite3.Connection, schedule: WeekSchedule) -> None:
        conn.execute("DELETE FROM schedule_meta WHERE key = 'free_text'")
        if schedule.free_text:
            conn.execute(
                "INSERT INTO schedule_meta (key, value) VALUES ('free_text', ?)",
                (schedule.free_text,),
            )
        if hasattr(self, "_long_term_plan") and self._long_term_plan:
            conn.execute(
                "DELETE FROM schedule_meta WHERE key = 'long_term_plan'"
            )
            conn.execute(
                "INSERT INTO schedule_meta (key, value) VALUES ('long_term_plan', ?)",
                (self._long_term_plan,),
            )

    def save(self, schedule: WeekSchedule) -> None:
        with sqlite3.connect(self.db_path) as conn:
            self._write_items(conn, schedule)
            self._write_meta(conn, schedule)
            conn.commit()

    def _read_items(self, conn: sqlite3.Connection, schedule: WeekSchedule) -> None:
        cursor = conn.execute(
            "SELECT day, start, end, title, location, notes, tag FROM schedule_items ORDER BY day, start"
        )
        for day, start, end, title, location, notes, tag in cursor.fetchall():
            schedule.add_item(
                day,
                ScheduleItem(
                    title=title,
                    start=start,
                    end=end,
                    location=location or None,
                    notes=notes or None,
                    tag=tag or None,
                ),
            )

    def _read_meta(self, conn: sqlite3.Connection, schedule: WeekSchedule) -> None:
        cursor = conn.execute("SELECT value FROM schedule_meta WHERE key = 'free_text'")
        row = cursor.fetchone()
        if row and row[0]:
            schedule.set_free_text(row[0])
        cursor = conn.execute("SELECT value FROM schedule_meta WHERE key = 'long_term_plan'")
        row = cursor.fetchone()
        self._long_term_plan = row[0] if row and row[0] else ""

    def load(self) -> WeekSchedule:
        schedule = WeekSchedule(owner=self.owner)
        with sqlite3.connect(self.db_path) as conn:
            self._read_items(conn, schedule)
            self._read_meta(conn, schedule)
        return schedule

    def get_long_term_plan(self) -> str:
        if not hasattr(self, "_long_term_plan"):
            # ensure load reads meta
            self.load()
        return getattr(self, "_long_term_plan", "") or ""

    def save_long_term_plan(self, text: str) -> None:
        self._long_term_plan = text.strip()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM schedule_meta WHERE key = 'long_term_plan'")
            if self._long_term_plan:
                conn.execute(
                    "INSERT INTO schedule_meta (key, value) VALUES ('long_term_plan', ?)",
                    (self._long_term_plan,),
                )
            conn.commit()

    def replace(self, entries: Iterable[tuple[str, ScheduleItem]]) -> WeekSchedule:
        """Replace storage with provided entries (utility for batch writes)."""
        schedule = WeekSchedule(owner=self.owner)
        for day, item in entries:
            schedule.add_item(day, item)
        self.save(schedule)
        return schedule
