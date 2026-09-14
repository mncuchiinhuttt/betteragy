"""Disk cache for conversation token metrics to enable sub-50ms CLI queries."""

import json
import os
from pathlib import Path
from typing import Optional

from ..core.config import ensure_config_dir
from ..core.constants import AG_CLI_CONVERSATIONS_DIR, USAGE_CACHE_FILE
from ..core.models import ConversationMetrics
from .usage_scanner import parse_conversation_db, load_conversation_summaries


class UsageCache:
    """Manages incremental cache of parsed conversation metrics."""

    @staticmethod
    def load_cache() -> dict[str, dict]:
        """Read usage cache from disk."""
        if not USAGE_CACHE_FILE.exists():
            return {}
        try:
            with open(USAGE_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def save_cache(cache_data: dict[str, dict]) -> None:
        """Write usage cache to disk."""
        ensure_config_dir()
        try:
            with open(USAGE_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
        except Exception:
            pass

    @classmethod
    def get_incremental_metrics(cls, force_refresh: bool = False) -> list[ConversationMetrics]:
        """Read all metrics, parsing only new or modified conversation files."""
        if not AG_CLI_CONVERSATIONS_DIR.exists():
            return []

        cache = {} if force_refresh else cls.load_cache()
        summaries = load_conversation_summaries()
        updated_cache: dict[str, dict] = {}
        all_metrics: list[ConversationMetrics] = []

        try:
            db_files = list(AG_CLI_CONVERSATIONS_DIR.glob("*.db"))
        except Exception:
            return []

        for db_file in db_files:
            cid = db_file.stem
            try:
                stat = os.stat(db_file)
                mtime = stat.st_mtime
                size = stat.st_size
            except OSError:
                continue

            cached_item = cache.get(cid)
            if (
                cached_item
                and not force_refresh
                and cached_item.get("mtime") == mtime
                and cached_item.get("size") == size
            ):
                metrics = ConversationMetrics.model_validate(cached_item["metrics"])
                all_metrics.append(metrics)
                updated_cache[cid] = cached_item
            else:
                title, step_count, last_mod = summaries.get(cid, ("Untitled", 0, ""))
                metrics = parse_conversation_db(db_file, title, step_count, last_mod)
                if metrics:
                    all_metrics.append(metrics)
                    updated_cache[cid] = {
                        "mtime": mtime,
                        "size": size,
                        "metrics": metrics.model_dump(),
                    }

        cls.save_cache(updated_cache)
        return all_metrics
