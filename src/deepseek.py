#!/usr/bin/env python3

import json
from typing import Tuple
from llm_service import LLMService
import tempfile
import time


class DeepseekService(LLMService):
    def construct_curl_command(self, max_tokens, messages, stream_file) -> list:
        max_tokens = min(max(1, max_tokens), 8192)  # deepseek limit up to 8192

        data = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "max_tokens": max_tokens
        }

        return [
            "curl",
            f"{self.api_endpoint}/v1/chat/completions",
            "--speed-limit", "0", "--speed-time", "5",
            "--silent", "--no-buffer",
            "--header", f"User-Agent: {self.user_agent}",
            "--header", "Content-Type: application/json",
            "--header", f"Authorization: Bearer {self.api_key}",
            "--data", json.dumps(data),
            "--output", stream_file
        ] + self.proxy_option

    def parse_stream_response(self, stream_string) -> Tuple[str, str, bool]:
        if stream_string.startswith("{"):
            try:
                error_message = json.loads(stream_string).get("error", {}).get("message")
                return "", error_message, True
            except:
                return "", "Response body is not valid json.", True

        chunks = []

        for line in stream_string.split("\n"):
            if line.startswith("data: "):
                data_str = line[len("data: "):]
                try:
                    chunks.append(json.loads(data_str))
                except json.JSONDecodeError:
                    pass

        response_text = "".join(
            item["choices"][0].get("delta", {}).get("content", "") for item in chunks
        )

        finish_reason = chunks[-1]["choices"][0]["finish_reason"] if chunks else None
        error_message = None
        has_stopped = False

        if finish_reason is None:
            pass
        elif finish_reason == "stop":
            has_stopped = True
        elif finish_reason == "length":
            has_stopped = True
            error_message = "The response reached the maximum token limit."
        elif finish_reason == "content_filter":
            has_stopped = True
            error_message = "The response was flagged by the content filter."
        else:
            has_stopped = True
            error_message = "Unknown Error"

        return response_text, error_message, has_stopped


def test_deepseek():
    api_endpoint = "https://api.deepseek.com"
    api_key = "your_api_key"
    model = "deepseek-chat"

    service = DeepseekService(api_endpoint, api_key, model, "", "")

    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as stream_file, \
            tempfile.NamedTemporaryFile(mode='w+', delete=False) as pid_file:

        messages = [
            {"role": "user", "content": "Hello, can you tell me about yourself?"}
        ]

        service.start_stream(1000, "", messages, stream_file.name, pid_file.name)

        print("Waiting for response...")
        while True:
            with open(stream_file.name, 'r', encoding='utf-8') as f:
                response = f.read()
                if response:
                    response_text, error_message, has_stopped = service.parse_stream_response(response)
                    if error_message:
                        print(f"Error: {error_message}")
                        break
                    if has_stopped:
                        print(f"Response: {response_text}")
                        break
            time.sleep(0.1)

        import os
        os.unlink(stream_file.name)
        os.unlink(pid_file.name)


if __name__ == "__main__":
    test_deepseek()