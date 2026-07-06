import os
import logging

import httpx

logger = logging.getLogger("vivify.integrations.soc_adapter")

SOC_GATEWAY_URL = os.getenv("SOC_GATEWAY_URL", "http://localhost:3333")
DEFAULT_MODEL = os.getenv("CAMEL_MODEL", "qwen2.5:3b")
REQUEST_TIMEOUT = 120.0


class SOCGatewayError(Exception):
    pass


class SOCAdapter:
    def __init__(self, base_url: str | None = None, timeout: float = REQUEST_TIMEOUT):
        self.base_url = (base_url or SOC_GATEWAY_URL).rstrip("/")
        self.timeout = timeout

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                return {
                    "success": True,
                    "content": content,
                    "usage": data.get("usage", {}),
                    "model": data.get("model", model),
                }
        except httpx.HTTPStatusError as e:
            logger.warning("SOC Gateway HTTP %s: %s", e.response.status_code, e.response.text[:200])
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except httpx.TimeoutException:
            logger.warning("SOC Gateway timeout after %ss", self.timeout)
            return {"success": False, "error": f"Timeout after {self.timeout}s"}
        except Exception as e:
            logger.error("SOC Gateway error: %s", e)
            return {"success": False, "error": str(e)}

    async def achat(
        self,
        messages: list[dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> dict:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                return {
                    "success": True,
                    "content": content,
                    "usage": data.get("usage", {}),
                    "model": data.get("model", model),
                }
        except httpx.HTTPStatusError as e:
            logger.warning("SOC Gateway HTTP %s: %s", e.response.status_code, e.response.text[:200])
            return {"success": False, "error": f"HTTP {e.response.status_code}"}
        except httpx.TimeoutException:
            logger.warning("SOC Gateway timeout after %ss", self.timeout)
            return {"success": False, "error": f"Timeout after {self.timeout}s"}
        except Exception as e:
            logger.error("SOC Gateway error: %s", e)
            return {"success": False, "error": str(e)}

    def health_check(self) -> bool:
        try:
            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{self.base_url}/health")
                return resp.status_code == 200
        except Exception:
            return False
