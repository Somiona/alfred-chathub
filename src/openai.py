from llm_service import *

class OpenaiService(LLMService):
    def construct_curl_command(self, max_tokens, messages, stream_file) -> list:
        """
        message here:
        [
            {"role": "system", "content": "You are a chatbot."},
            {"role": "user", "content": "hello, there!"},
            {"role": "assistant", "content": "Hello! How can I help you today?"}
        ]
        """
        data = {
            "model": self.model,
            "messages": messages,
            "stream": True
        }

        return [
            "curl",
            f"{self.api_endpoint}/v1/chat/completions",
            "--speed-limit", "0", "--speed-time", "5",  # Abort stalled connection after a few seconds
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

        raw_chunks = []
        for line in stream_string.split("\n"):
            if not line.startswith("data: "):
                continue
            data_str = line[len("data: "):].strip()
            if data_str == "[DONE]":
                continue
            try:
                raw_chunks.append(json.loads(data_str))
            except json.JSONDecodeError:
                continue

        # 兼容性处理：部分 OpenAI 兼容服务会发送不含 choices 的心跳/统计事件。
        valid_chunks = []
        for obj in raw_chunks:
            choices = obj.get("choices")
            if isinstance(choices, list) and len(choices) > 0:
                valid_chunks.append(obj)

        response_text = "".join(
            c["choices"][0].get("delta", {}).get("content", "") for c in valid_chunks
        )

        finish_reason = None
        if valid_chunks:
            finish_reason = valid_chunks[-1]["choices"][0].get("finish_reason")

        error_message = None
        has_stopped = False

        if finish_reason is None:
            has_stopped = False
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
