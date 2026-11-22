import json
from collections.abc import Callable
from typing import Any

from google import genai
from google.genai import types
from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _tool_schemas() -> list[dict[str, Any]]:
    """OpenAI/OpenRouter-compatible function schemas matching diagnostics, intervention & screenshot tools."""
    return [
        {
            "type": "function",
            "function": {
                "name": "check_system_metrics",
                "description": "Return CPU utilization per core, load averages, RAM usage, and top CPU processes.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "inspect_process_or_logs",
                "description": "Inspect a process by PID or fetch recent systemd journal entries for a service.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pid": {"type": "integer", "description": "Target process ID (> 0 to inspect)."},
                        "service_name": {"type": "string", "description": "Systemd unit name (e.g. nginx.service)."},
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "execute_intervention",
                "description": "Execute a remediation shell command only after user approval.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "shell_command": {"type": "string", "description": "Linux remediation shell command."},
                        "reason": {"type": "string", "description": "Why this remediation is needed."},
                    },
                    "required": ["shell_command", "reason"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "take_screenshot",
                "description": "Capture a screenshot of the Ubuntu desktop and return file path + base64 encoded PNG image.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
    ]


class OpenRouterSession:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_instruction: str,
        tool_map: dict[str, Callable[..., Any]],
        site_url: str = "",
        app_name: str = "sys-stability-agent",
    ) -> None:
        headers: dict[str, str] = {}
        if site_url:
            headers["HTTP-Referer"] = site_url
        if app_name:
            headers["X-OpenRouter-Title"] = app_name

        self.client = OpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            default_headers=headers or None,
        )
        self.model = model
        self.tool_map = tool_map
        self.tools = _tool_schemas()
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_instruction}
        ]

    def send_message(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,  # type: ignore[arg-type]
                tools=self.tools,  # type: ignore[arg-type]
                temperature=0.1,
            )
            msg = response.choices[0].message
            tool_calls = msg.tool_calls or []

            if not tool_calls:
                final_text = msg.content or ""
                self.messages.append({"role": "assistant", "content": final_text})
                return final_text

            # Record assistant tool call turn before appending tool results
            self.messages.append(
                {
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,  # type: ignore[union-attr]
                                "arguments": tc.function.arguments,  # type: ignore[union-attr]
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            )

            for tc in tool_calls:
                fn_name = tc.function.name  # type: ignore[union-attr]
                raw_args = tc.function.arguments or "{}"  # type: ignore[union-attr]
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {}

                fn = self.tool_map.get(fn_name)
                if fn is None:
                    result: Any = f"Error: unknown tool '{fn_name}'"
                else:
                    try:
                        result = fn(**args)
                    except Exception as exc:  # noqa: BLE001
                        result = f"Tool error ({fn_name}): {exc}"

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result if isinstance(result, str) else json.dumps(result),
                    }
                )


class GeminiSession:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_instruction: str,
        tools: list[Callable[..., Any]],
    ) -> None:
        client = genai.Client(api_key=api_key or None)
        self._chat = client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
tools=tools,  # type: ignore[arg-type]
                temperature=0.1,
            ),
        )

    def send_message(self, user_text: str) -> str:
        resp = self._chat.send_message(user_text)
        return resp.text or ""


def create_agent_session(
    provider: str,
    system_instruction: str,
    tools: list[Callable[..., Any]],
    openrouter_api_key: str,
    openrouter_model: str,
    gemini_api_key: str,
    gemini_model: str,
    site_url: str = "",
    app_name: str = "sys-stability-agent",
) -> OpenRouterSession | GeminiSession:
    normalized = provider.strip().lower()
    if normalized == "openrouter":
        tool_map = {fn.__name__: fn for fn in tools}
        return OpenRouterSession(
            api_key=openrouter_api_key,
            model=openrouter_model,
            system_instruction=system_instruction,
            tool_map=tool_map,
            site_url=site_url,
            app_name=app_name,
        )
    if normalized == "gemini":
        return GeminiSession(
            api_key=gemini_api_key,
            model=gemini_model,
            system_instruction=system_instruction,
            tools=tools,
        )
    raise ValueError(f"Unsupported LLM_PROVIDER '{provider}'. Use 'openrouter' or 'gemini'.")
