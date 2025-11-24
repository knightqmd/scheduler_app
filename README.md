## AI 日程规划演示

该项目展示了一个最小可行的“AI 基于日程规划”流程：

1. 用户输入新的日程诉求；
2. 系统整理出“用户需求 + 既有日程”；
3. 将整理后的上下文发给大模型（默认对接字节火山引擎 Doubao/Ark）；
4. 输出模型返回的日程安排。

### 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install openai
export ARK_API_KEY=your_key_here
python main.py
```

如果没有配置 `ARK_API_KEY`，程序会自动给出 mock 日程，便于本地演示。

### 调试模式

运行 `python main.py --debug` 或设置 `SCHEDULER_DEBUG=1` 可输出详细日志，方便排查模型调用和 prompt 拼装过程。输入需求时支持多行，直接按一次回车留空行即可结束。

### 代码结构

- `scheduler_app/models.py`：日程与条目数据模型。
- `scheduler_app/model_client.py`：封装与模型的交互。
- `scheduler_app/scheduler.py`：负责组织 prompt 并调用模型。
- `main.py`：简单 CLI 流程，串联用户输入、已有日程和模型输出。

你可以根据业务需要扩展 `load_existing_schedule` 从真实日历系统取数，或在 `DoubaoModelClient` 中换用自己的模型。
