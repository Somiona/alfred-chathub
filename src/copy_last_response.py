#!/usr/bin/env python3

from helper import env_var, read_chat


def run():
    chat_file = f"{env_var('alfred_workflow_data')}/chat.json"
    messages = read_chat(chat_file)
    last_assistant = next((m for m in reversed(messages) if m.get("role") == "assistant"), None)
    content = last_assistant.get("content") if last_assistant else None
    if not content:
        return ""
    # 历史兼容：旧版本可能把带有标题的渲染文本写入存档，这里只在匹配到明确前缀时才去除，避免误截断正常内容
    legacy_prefixes = ("#### Assistant\n", "**Assistant:**\n\n")
    for prefix in legacy_prefixes:
        if content.startswith(prefix):
            content = content[len(prefix):]
            break
    return content


if __name__ == "__main__":
    print(run())
