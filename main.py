from __future__ import annotations

import argparse
import logging
import os
import sys

from scheduler_app import ScheduleItem, ScheduleService, UserSchedule
from scheduler_app.model_client import DoubaoModelClient

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
        data = ""
        print(f"未检测到输入，使用默认示例：{data}")
    logger.debug("用户输入内容：%s", data)
    return data


def load_existing_schedule() -> UserSchedule:
    schedule = UserSchedule(owner="小李")
    schedule.add_item(
        ScheduleItem(
            title="看电影",
            start="09:30",
            end="10:00",
            location="会议室 ",
            notes="同步核心进度",
        )
    )
    schedule.add_item(
        ScheduleItem(
            title="客户回访",
            start="11:00",
            end="12:00",
            location="线上会议",
            notes="确认交付验收",
        )
    )
    schedule.add_item(
        ScheduleItem(
            title="Roadmap 讨论",
            start="16:00",
            end="17:00",
            location="会议室 C",
            notes="需提前准备资料",
        )
    )
    logger.debug("共加载 %d 条已有日程", len(schedule.items))
    return schedule


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI 日程规划 CLI")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="输出详细调试信息（或设置环境变量 SCHEDULER_DEBUG=1）",
    )
    return parser.parse_args()


def configure_logging(enable_debug: bool) -> None:
    lvl = logging.DEBUG if enable_debug else logging.INFO
    logging.basicConfig(level=lvl, format="[%(levelname)s] %(name)s - %(message)s")
    logger.debug("日志系统已初始化，等级：%s", logging.getLevelName(lvl))


def main() -> None:
    args = parse_args()
    enable_debug = args.debug or os.environ.get("SCHEDULER_DEBUG") == "1"
    configure_logging(enable_debug)
    logger.info("启动 AI 日程规划 CLI，调试模式：%s", enable_debug)
    user_request = read_user_request()
    schedule = load_existing_schedule()
    logger.info("已收集输入，准备调用模型")
    model_client = DoubaoModelClient()
    service = ScheduleService(model_client)
    try:
        plan = service.plan(user_request, schedule)
    except Exception as exc:
        logger.exception("生成日程失败")
        print("调用模型失败，请检查 ARK_API_KEY、网络和模型配置。")
        print(f"错误信息：{exc}")
        sys.exit(1)
    else:
        print("\n===== 推荐日程 =====")
        print(plan.strip())


if __name__ == "__main__":
    main()
