"""
Summary generation gateway.
Supports rule-based summaries (default), a local HTTP endpoint, or a cloud HTTP endpoint.
"""
import requests
from core.config import Config
from reasoning.rules import generate_text


class SummaryModelGateway(object):
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class RulesGateway(SummaryModelGateway):
    def generate(self, bundle) -> str:
        # Deterministic rule-based output on structured bundle
        if isinstance(bundle, dict) and bundle.get("bundle"):
            return generate_text(bundle["bundle"])
        if isinstance(bundle, dict):
            return generate_text(bundle)
        return generate_text({})


class LocalLLMGateway(SummaryModelGateway):
    """
    Calls a locally hosted model over HTTP (e.g., Hugging Face TGI for Qwen).
    """
    def __init__(self, endpoint: str, model: str, backend: str):
        self.endpoint = endpoint
        self.model = model
        self.backend = (backend or "tgi").lower()

    def generate(self, prompt: str) -> str:
        if not self.endpoint:
            raise RuntimeError("LOCAL_SUMMARY_ENDPOINT is not configured")
        if self.backend == "ollama":
            payload = {
                "model": self.model or "qwen2.5",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": Config.SUMMARY_MAX_TOKENS,
                },
            }
        else:
            payload = {
                # TGI-compatible schema
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": Config.SUMMARY_MAX_TOKENS,
                    "temperature": 0.0,
                    "do_sample": False,
                }
            }
            if self.model:
                payload["model"] = self.model

        resp = requests.post(self.endpoint, json=payload, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError("Local LLM returned {}: {}".format(resp.status_code, resp.text[:200]))
        data = resp.json()
        # TGI returns generated_text; Ollama returns response
        return data.get("generated_text") or data.get("response") or data.get("text") or ""


class CloudLLMGateway(SummaryModelGateway):
    """
    Calls a cloud model endpoint (generic HTTP JSON with bearer token).
    Defaults align with OpenAI-style chat completions.
    """
    def __init__(self, endpoint: str, api_key: str, model: str):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> str:
        if not self.endpoint or not self.api_key:
            raise RuntimeError("Cloud summary endpoint or API key is not configured")
        headers = {
            "Authorization": "Bearer {}".format(self.api_key),
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": Config.SUMMARY_MAX_TOKENS,
            "temperature": 0.0,
        }
        resp = requests.post(self.endpoint, json=body, headers=headers, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError("Cloud LLM returned {}: {}".format(resp.status_code, resp.text[:200]))
        data = resp.json()
        # OpenAI-style choice extraction fallback
        choices = data.get("choices") or []
        if choices and "message" in choices[0]:
            return choices[0]["message"].get("content", "")
        return data.get("text") or ""


def _select_gateway():
    mode = (Config.SUMMARY_MODEL or "rules").lower()
    if mode == "local":
        return LocalLLMGateway(Config.LOCAL_SUMMARY_ENDPOINT, Config.LOCAL_SUMMARY_MODEL, Config.LOCAL_SUMMARY_BACKEND)
    if mode == "cloud":
        return CloudLLMGateway(
            Config.CLOUD_SUMMARY_ENDPOINT,
            Config.CLOUD_SUMMARY_API_KEY,
            Config.CLOUD_SUMMARY_MODEL,
        )
    return RulesGateway()


def summarize(bundle):
    gateway = _select_gateway()
    mode = (Config.SUMMARY_MODEL or "rules").lower()
    if mode == "rules":
        return gateway.generate(bundle)
    # local/cloud expect a prompt string in bundle["prompt"]
    prompt = ""
    if isinstance(bundle, dict):
        prompt = bundle.get("prompt", "")
    else:
        prompt = str(bundle)
    return gateway.generate(prompt)


def generate_from_prompt(prompt: str) -> str:
    """
    Send a raw prompt through the configured gateway (local/cloud). For rules mode, just echo.
    """
    mode = (Config.SUMMARY_MODEL or "rules").lower()
    if mode == "rules":
        return prompt
    gateway = _select_gateway()
    return gateway.generate(prompt)
