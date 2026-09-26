from __future__ import annotations
import json
import urllib.error
import urllib.request


class ProviderError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class OpenRouter:
    BASE = "https://openrouter.ai/api/v1"

    def __init__(self, key, model, max_tokens=12000):
        self.key, self.model, self.max_tokens = key.strip(), model.strip(), max_tokens
        if not self.key or not self.model:
            raise ProviderError("Enter your OpenRouter key and a model ID in Settings.")

    def request(self, endpoint, payload=None):
        headers = {"Authorization": "Bearer " + self.key, "Content-Type": "application/json",
                   "X-Title": "Driod local assistant"}
        request = urllib.request.Request(self.BASE + endpoint, headers=headers,
                   data=json.dumps(payload).encode() if payload is not None else None)
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=90) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            hints = {401: "Invalid OpenRouter key.", 402: "OpenRouter credits or budget are insufficient.",
                     404: "Model unavailable; choose another tool-capable model.",
                     429: "Rate limit reached. Wait a moment and try again."}
            detail = exc.read(3000).decode("utf-8", "replace").replace(self.key, "[REDACTED]")
            raise ProviderError(hints.get(exc.code, f"OpenRouter HTTP {exc.code}") + "\n" + detail) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ProviderError("Could not reach OpenRouter. Check your connection and try again.") from exc
        if "error" in result:
            raise ProviderError(json.dumps(result["error"]).replace(self.key, "[REDACTED]"))
        return result

    def models(self):
        return sorted(m["id"] for m in self.request("/models")["data"]
                      if "tools" in m.get("supported_parameters", []))

    def complete(self, messages, tools):
        data = self.request("/chat/completions", {
            "model": self.model, "messages": messages, "tools": tools,
            "tool_choice": "auto", "max_tokens": self.max_tokens,
            "provider": {"require_parameters": True}
        })
        try:
            choice = data["choices"][0]
            if choice.get("finish_reason") == "length":
                raise ProviderError("Model response hit the output limit. Ask for smaller files or raise Max output tokens.")
            msg = choice["message"]
            # Preserve provider reasoning metadata/signatures required for some models.
            allowed = {"role", "content", "tool_calls", "reasoning", "reasoning_details"}
            msg = {k: v for k, v in msg.items() if k in allowed}
            msg["role"] = "assistant"
            return msg, data.get("usage", {})
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Unexpected API response; try another tool-capable model.") from exc
