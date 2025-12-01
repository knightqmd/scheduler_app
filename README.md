## AI 日程规划演示

该项目展示了一个最小可行的“AI 基于日程规划”流程：

1. 用户输入新的日程诉求；
2. 系统自动从用户日程表读取“既有日程”，整理出“用户需求 + 既有日程”；
3. 将整理后的上下文发给大模型（默认对接字节火山引擎 Doubao/Ark）；
4. 输出模型返回的日程安排。

### 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install openai
export ARK_API_KEY=your_key_here
python main.py
# 或使用 --request 传入字符串，便于自动化运行：
# python main.py --request "帮我安排下周的健身和学习时间"
```

如果没有配置 `ARK_API_KEY`，程序会自动返回内置 mock 日程，便于本地演示或调试；配置好密钥后会自动切换为远端模型调用。

### 自动获取已有日程

程序启动时会自动加载用户的已有日程，无需手动输入。默认会使用内置示例；若希望对接真实的日程表，可将 JSON 文件路径写入环境变量 `SCHEDULE_FILE`，格式示例：

```json
{
  "days": {
    "周一": [{"title": "周会", "start": "09:30", "end": "10:30"}],
    "周三": [{"title": "对外会议", "start": "15:00", "end": "16:00", "location": "线上"}]
  },
  "free_text": "来自日历系统的备注"
}
```

### 调试模式

运行 `python main.py --debug` 或设置 `SCHEDULER_DEBUG=1` 可输出详细日志，方便排查模型调用和 prompt 拼装过程。输入需求时支持多行，直接按一次回车留空行即可结束。

### 代码结构

- `scheduler_app/models.py`：日程与条目数据模型。
- `scheduler_app/model_client.py`：封装与模型的交互。
- `scheduler_app/scheduler.py`：负责组织 prompt 并调用模型。
- `main.py`：简单 CLI 流程，串联用户输入、已有日程和模型输出。

你可以根据业务需要扩展 `load_existing_schedule` 从真实日历系统取数，或在 `DoubaoModelClient` 中换用自己的模型。
