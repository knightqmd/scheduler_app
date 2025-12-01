from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from typing import List, Optional

from scheduler_app import ScheduleItem, ScheduleService, WeekSchedule
from scheduler_app.model_client import DoubaoModelClient
from scheduler_app.schedule_loader import load_existing_schedule

logger = logging.getLogger(__name__)


def read_user_request() -> str:
    logger.debug("准备读取用户输入")
    print("请输入今天的日程需求，支持多行输入，直接输入空行即可结束：")
    try:
        lines = []
        while True:
            line = sys.stdin.readline()
            if line == "":
                break  # EOF（例如管道输入）依然允许
            stripped = line.rstrip("\n")
            if stripped == "":
                break
            lines.append(stripped)
        data = "\n".join(lines).strip()
    except KeyboardInterrupt:
        print("\n已取消。")
        sys.exit(0)
    if not data:
        print("未检测到输入，请重新运行并提供日程需求。")
        sys.exit(1)
    logger.debug("用户输入内容：%s", data)
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI 日程规划 CLI")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="输出详细调试信息（或设置环境变量 SCHEDULER_DEBUG=1）",
    )
    parser.add_argument(
        "--request",
        help="直接传入日程需求字符串，便于脚本化运行（为空则进入交互式输入）",
    )
    return parser.parse_args()


def configure_logging(enable_debug: bool) -> None:
    lvl = logging.DEBUG if enable_debug else logging.INFO
    level_name_map = {
        logging.DEBUG: "调试",
        logging.INFO: "信息",
        logging.WARNING: "警告",
        logging.ERROR: "错误",
        logging.CRITICAL: "严重",
    }
    for level, name in level_name_map.items():
        logging.addLevelName(level, name)
    logging.basicConfig(level=lvl, format="[%(levelname)s] %(name)s - %(message)s")
    logger.debug("日志系统已初始化，等级：%s", logging.getLevelName(lvl))


def extract_json_array(text: str) -> Optional[str]:
    """Best-effort extraction of JSON array substring from model output."""
    match = re.search(r"\[.*\]", text, re.S)
    if match:
        return match.group(0)
    return None


VALID_DAYS = {"周一", "周二", "周三", "周四", "周五", "周六", "周日"}


def _is_valid_time_str(value: str) -> bool:
    return bool(re.match(r"^[0-2]\d:[0-5]\d$", value))


def update_schedule_from_model_output(
    schedule: WeekSchedule, output: str
) -> List[ScheduleItem]:
    """Parse model JSON output and replace schedule items with validation."""
    json_block = extract_json_array(output)
    if not json_block:
        raise ValueError("未找到 JSON 数组格式的模型输出")
    try:
        items = json.loads(json_block)
    except json.JSONDecodeError as exc:
        raise ValueError(f"模型输出 JSON 解析失败: {exc}") from exc
    if not isinstance(items, list):
        raise ValueError("模型输出不是列表")

    schedule.days.clear()
    schedule.free_text = None
    parsed_items: List[ScheduleItem] = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        day = entry.get("day")
        start = entry.get("start")
        end = entry.get("end")
        title = entry.get("title")
        location = entry.get("location") or None
        notes = entry.get("notes") or None
        if not all([day, start, end, title]):
            logger.warning("跳过字段不完整的条目：%s", entry)
            continue
        if str(day) not in VALID_DAYS:
            logger.warning("非法 day，跳过：%s", day)
            continue
        if not (_is_valid_time_str(str(start)) and _is_valid_time_str(str(end))):
            logger.warning("时间格式不正确，跳过：%s-%s", start, end)
            continue
        item = ScheduleItem(
            title=str(title),
            start=str(start),
            end=str(end),
            location=str(location) if location else None,
            notes=str(notes) if notes else None,
            tag=str(entry.get("tag")) if entry.get("tag") else None,
        )
        schedule.add_item(day=str(day), item=item)
        parsed_items.append(item)
    if not parsed_items:
        raise ValueError("模型输出未包含有效日程条目")
    return parsed_items


def main() -> None:
    args = parse_args()
    enable_debug = args.debug or os.environ.get("SCHEDULER_DEBUG") == "1"
    configure_logging(enable_debug)
    logger.info("启动 AI 日程规划 CLI，调试模式：%s", enable_debug)
    existing_schedule = load_existing_schedule()
    print("检测到以下已有日程，将自动纳入规划：")
    print(existing_schedule.as_markdown())
    user_request = args.request.strip() if args.request else ""
    if not user_request:
        user_request = read_user_request()
    else:
        logger.info("收到命令行传入的日程需求，跳过交互输入")
    logger.info("已收集输入，准备调用模型，以本周日程为上下文调整新增需求")
    model_client = DoubaoModelClient()
    service = ScheduleService(model_client)
    try:
        plan = service.plan(user_request, existing_schedule)
    except Exception as exc:
        logger.exception("生成日程失败")
        print("调用模型失败，请检查 ARK_API_KEY、网络和模型配置。")
        print(f"错误信息：{exc}")
        sys.exit(1)
    else:
        print("\n===== 模型返回（原始） =====")
        print(plan.strip())
        try:
            update_schedule_from_model_output(existing_schedule, plan)
        except Exception as exc:
            logger.exception("解析或更新日程失败")
            print("未能解析模型输出为固定格式，请调整提示或稍后重试。")
            print(f"错误信息：{exc}")
            sys.exit(1)
        print("\n===== 已更新的一周日程 =====")
        print(existing_schedule.as_markdown())


if __name__ == "__main__":
    main()
