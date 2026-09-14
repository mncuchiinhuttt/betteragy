"""Update checker service for Betteragy via GitHub Releases/Tags API with local caching."""

import json
import re
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from .. import __version__
from ..core.constants import CONFIG_DIR

DEFAULT_CACHE_PATH = CONFIG_DIR / "update_cache.json"
CACHE_TTL_SECONDS = 14400  # 4 hours
GITHUB_REPO = "mncuchiinhuttt/betteragy"
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_API_TAGS = f"https://api.github.com/repos/{GITHUB_REPO}/tags"


def parse_semver(version_str: str) -> Tuple[int, int, int]:
    """Extract (major, minor, patch) integer tuple from a version string."""
    clean = re.sub(r"^v", "", version_str.strip())
    match = re.match(r"^(\d+)\.(\d+)(?:\.(\d+))?", clean)
    if not match:
        return (0, 0, 0)
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3)) if match.group(3) is not None else 0
    return (major, minor, patch)


@dataclass
class UpdateInfo:
    current_version: str
    latest_version: str
    is_newer: bool
    release_url: str = ""
    checked_at: str = ""


class UpdateService:
    """Manages low-latency update checks with caching to avoid rate limits."""

    def __init__(self, cache_path: Path = DEFAULT_CACHE_PATH, timeout_secs: float = 2.0):
        self.cache_path = Path(cache_path)
        self.timeout_secs = timeout_secs

    def _read_cache(self) -> Optional[dict]:
        try:
            if not self.cache_path.exists():
                return None
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            last_ts = data.get("timestamp", 0)
            if time.time() - last_ts < CACHE_TTL_SECONDS:
                return data
        except Exception:
            pass
        return None

    def _write_cache(self, latest_version: str, release_url: str) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "timestamp": time.time(),
                "latest_version": latest_version,
                "release_url": release_url,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            self.cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass

    def check_for_updates(self, force: bool = False) -> Optional[UpdateInfo]:
        """Check for newer release on GitHub. Returns None on offline/timeout."""
        if not force:
            cached = self._read_cache()
            if cached and cached.get("latest_version"):
                latest = cached["latest_version"]
                url = cached.get("release_url", "")
                is_newer = parse_semver(latest) > parse_semver(__version__)
                return UpdateInfo(
                    current_version=__version__,
                    latest_version=latest,
                    is_newer=is_newer,
                    release_url=url,
                    checked_at=cached.get("checked_at", ""),
                )

        # Query GitHub API
        headers = {"User-Agent": f"betteragy-cli/{__version__}", "Accept": "application/vnd.github.v3+json"}
        latest_ver: Optional[str] = None
        release_url = f"https://github.com/{GITHUB_REPO}"

        try:
            req = urllib.request.Request(GITHUB_API_LATEST, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout_secs) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    latest_ver = payload.get("tag_name", "").lstrip("v")
                    release_url = payload.get("html_url", release_url)
        except Exception:
            pass

        # Fallback to tags if no official release published yet
        if not latest_ver:
            try:
                req = urllib.request.Request(GITHUB_API_TAGS, headers=headers)
                with urllib.request.urlopen(req, timeout=self.timeout_secs) as resp:
                    if resp.status == 200:
                        tags = json.loads(resp.read().decode("utf-8"))
                        if tags and isinstance(tags, list):
                            latest_ver = tags[0].get("name", "").lstrip("v")
            except Exception:
                pass

        if latest_ver:
            self._write_cache(latest_ver, release_url)
        else:
            latest_ver = __version__

        is_newer = parse_semver(latest_ver) > parse_semver(__version__)

        return UpdateInfo(
            current_version=__version__,
            latest_version=latest_ver,
            is_newer=is_newer,
            release_url=release_url,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )
