import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import config


class TavilyService:
    endpoint = config.tavily_search_url

    def search(self, query: str) -> list[dict]:
        if not config.tavily_api_key:
            raise RuntimeError("Tavily API key is not configured.")

        payload = json.dumps(
            {
                "api_key": config.tavily_api_key,
                "query": query,
                "max_results": config.tavily_max_results,
                "search_depth": config.tavily_search_depth,
            }
        ).encode("utf-8")
        request = Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=config.search_timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"Tavily search failed: {exc}") from exc

        results = data.get("results", [])
        return [
            {
                "title": item.get("title", ""),
                "snippet": item.get("content", ""),
                "url": item.get("url", ""),
            }
            for item in results
        ]
