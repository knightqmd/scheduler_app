from __future__ import annotations

"""Lightweight HTTP server to bridge the static frontend with the scheduler backend."""

import json
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Iterable

from scheduler_app import ScheduleItem, ScheduleService, WeekSchedule
from scheduler_app.model_client import DoubaoModelClient
from scheduler_app.storage import ScheduleStorage
from main import update_schedule_from_model_output

WEB_DIR = Path(__file__).parent / "web"
logger = logging.getLogger("serve")
STORAGE = ScheduleStorage()


def item_to_dict(item: ScheduleItem) -> Dict[str, str]:
    return {
        "title": item.title,
        "start": item.start,
        "end": item.end,
        "location": item.location or "",
        "notes": item.notes or "",
        "tag": item.tag or "",
    }


def schedule_to_dict(schedule: WeekSchedule) -> Dict[str, Iterable[Dict[str, str]]]:
    return {
        "owner": schedule.owner,
        "days": {day: [item_to_dict(it) for it in items] for day, items in schedule.days.items()},
        "free_text": schedule.free_text or "",
        "long_term_plan": STORAGE.get_long_term_plan(),
    }


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _handle_schedule(self) -> None:
        schedule = STORAGE.load()
        self._send_json({"schedule": schedule_to_dict(schedule)})

    def _handle_plan(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"error": "无效的 JSON 请求体"}, status=400)
            return
        user_request = (payload.get("request") or "").strip()
        mode = (payload.get("mode") or "smart").lower()
        long_term_plan = (payload.get("long_term_plan") or "").strip()
        if long_term_plan:
            STORAGE.save_long_term_plan(long_term_plan)

        if mode == "save":
            # 仅保存长期计划，不调用模型
            schedule = STORAGE.load()
            schedule.free_text = long_term_plan or schedule.free_text
            STORAGE.save(schedule)
            return self._send_json({"raw": "", "schedule": schedule_to_dict(schedule)})

        if not user_request:
            self._send_json({"error": "request 字段不能为空"}, status=400)
            return
        existing = STORAGE.load()
        service = ScheduleService(DoubaoModelClient())
        try:
            raw = service.plan(user_request, existing, long_term_plan=long_term_plan)
            update_schedule_from_model_output(existing, raw)
            STORAGE.save(existing)
        except Exception as exc:
            logger.exception("生成日程失败：%s", exc)
            self._send_json({"error": f"生成日程失败: {exc}"}, status=500)
            return
        self._send_json({"raw": raw, "schedule": schedule_to_dict(existing)})

    def do_OPTIONS(self):  # noqa: N802 - match base signature
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):  # noqa: N802 - match base signature
        if self.path.startswith("/api/schedule"):
            return self._handle_schedule()
        return super().do_GET()

    def do_POST(self):  # noqa: N802 - match base signature
        if self.path.startswith("/api/plan"):
            return self._handle_plan()
        return self._send_json({"error": "未知路径"}, status=404)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    logger.info("启动本地服务，目录：%s", WEB_DIR)
    server: HTTPServer = ThreadingHTTPServer((host, port), AppHandler)
    logger.info("Listening on http://%s:%d", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("已收到中断信号，准备退出")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
