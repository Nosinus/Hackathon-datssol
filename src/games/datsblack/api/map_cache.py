from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

from games.datsblack.models.raw import MapResponse


@dataclass
class MapCache:
    base_dir: Path

    def cache_map_from_response(
        self, response: MapResponse, *, timeout_seconds: float = 5.0
    ) -> Path | None:
        map_url = response.mapUrl
        if not map_url:
            return None

        self.base_dir.mkdir(parents=True, exist_ok=True)
        parsed = urlparse(map_url)
        extension = Path(parsed.path).suffix or ".bin"
        digest = hashlib.sha256(map_url.encode("utf-8")).hexdigest()[:16]
        out = self.base_dir / f"map_{digest}{extension}"

        if out.exists():
            return out

        with httpx.Client(timeout=timeout_seconds) as client:
            blob = client.get(map_url)
            blob.raise_for_status()
            out.write_bytes(blob.content)
        return out
