import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import config


class SerperService:
    endpoint = config.serper_search_url

    def search(self, query: str) -> list[dict]:
        if not config.serper_api_key:
            raise RuntimeError("Serper API key is not configured.")

        payload = json.dumps({"q": query, "num": config.serper_search_count}).encode("utf-8")
        request = Request(
            self.endpoint,
            data=payload,
            headers={
                "X-API-KEY": config.serper_api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=config.search_timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"Serper search failed: {exc}") from exc

        results = data.get("organic", [])
        return [
            {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("link", ""),
            }
            for item in results
        ]
