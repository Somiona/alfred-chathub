#!/usr/bin/env python3

import json
from helper import env_var


def provider_items():
    providers = [
        ("openai", "OpenAI", env_var("openai_model")),
        ("anthropic", "Anthropic", env_var("anthropic_model")),
        ("gemini", "Gemini", env_var("gemini_model")),
        ("qwen", "Qwen", env_var("qwen_model")),
        ("ollama", "Ollama", env_var("ollama_model")),
        ("deepseek", "DeepSeek", env_var("deepseek_model")),
    ]

    current = env_var("selected_llm_service") or ""
    items = []

    for key, label, model in providers:
        suffix = " (current)" if key == current else ""
        title = f"{label}{suffix}"
        subtitle = model or ""
        items.append({
            "title": title,
            "subtitle": subtitle,
            "arg": key,
            "icon": {"path": "icon.png"}
        })

    return items


def main():
    data = {"items": provider_items()}
    print(json.dumps(data))


if __name__ == "__main__":
    main()

