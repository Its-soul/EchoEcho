import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..config import config


class BraveSearchService:
    endpoint = config.brave_search_url

    def search(self, query: str) -> list[dict]:
        if not config.brave_api_key:
            raise RuntimeError("Brave API key is not configured.")

        url = f"{self.endpoint}?{urlencode({'q': query, 'count': config.brave_search_count})}"
        request = Request(
            url,
            headers={
                "X-Subscription-Token": config.brave_api_key,
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=config.search_timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"Brave search failed: {exc}") from exc

        results = data.get("web", {}).get("results", [])
        return [
            {
                "title": item.get("title", ""),
                "snippet": item.get("description", ""),
                "url": item.get("url", ""),
            }
            for item in results
        ]
