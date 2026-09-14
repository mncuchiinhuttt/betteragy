"""Offline SQLite conversation scanner to extract token telemetry directly from disk."""

import os
import sqlite3
from pathlib import Path
from typing import Optional

from ..core.constants import AG_CLI_CONVERSATIONS_DIR, AG_CLI_SUMMARIES_DB
from ..core.models import ConversationMetrics, TokenUsage
from .pricing_service import calculate_cost
from .protobuf_decoder import extract_tokens_from_gen_metadata


def load_conversation_summaries() -> dict[str, tuple[str, int, str]]:
    """Load (title, step_count, last_modified) map from conversation_summaries.db."""
    mapping: dict[str, tuple[str, int, str]] = {}
    if not AG_CLI_SUMMARIES_DB.exists():
        return mapping

    try:
        con = sqlite3.connect(str(AG_CLI_SUMMARIES_DB))
        cur = con.cursor()
        cur.execute(
            "SELECT conversation_id, title, step_count, last_modified_time FROM conversation_summaries"
        )
        for cid, title, step_count, mtime in cur.fetchall():
            clean_title = title.strip() if title else f"Conversation {cid[:8]}"
            mapping[cid] = (clean_title, step_count or 0, mtime or "")
        con.close()
    except Exception:
        pass
    return mapping


def parse_conversation_db(db_path: Path, title: str, step_count: int, mtime: str) -> Optional[ConversationMetrics]:
    """Parse gen_metadata table of a conversation SQLite database."""
    if not db_path.exists():
        return None

    cid = db_path.stem
    total_inp = 0
    total_out = 0
    total_cache = 0
    total_reas = 0
    total_cost = 0.0
    calls = 0

    try:
        con = sqlite3.connect(str(db_path))
        cur = con.cursor()
        cur.execute("SELECT data FROM gen_metadata ORDER BY idx ASC")
        rows = cur.fetchall()
        con.close()

        for (blob,) in rows:
            if not blob:
                continue
            extracted = extract_tokens_from_gen_metadata(blob)
            if extracted:
                model, inp, out, cache, reas = extracted
                total_inp += inp
                total_out += out
                total_cache += cache
                total_reas += reas
                total_cost += calculate_cost(model, inp, out, cache, 0, reas)
                calls += 1

        usage = TokenUsage(
            input_tokens=total_inp,
            output_tokens=total_out,
            cache_read_tokens=total_cache,
            cache_write_tokens=0,
            reasoning_tokens=total_reas,
            calls_count=calls,
            cost_usd=round(total_cost, 4),
        )
        final_title = title.strip() if (title and title.strip() and title != "Untitled") else f"Conversation {cid[:8]}"
        return ConversationMetrics(
            conversation_id=cid,
            title=final_title,
            step_count=step_count,
            last_modified=mtime,
            usage=usage,
        )
    except Exception:
        return None


class UsageScanner:
    """Scans all Antigravity CLI conversations on disk."""

    def scan_all_conversations(self) -> list[ConversationMetrics]:
        """Scan all conversation databases and return metrics."""
        if not AG_CLI_CONVERSATIONS_DIR.exists():
            return []

        summaries = load_conversation_summaries()
        metrics_list: list[ConversationMetrics] = []

        try:
            db_files = list(AG_CLI_CONVERSATIONS_DIR.glob("*.db"))
        except Exception:
            return []

        for db_file in db_files:
            cid = db_file.stem
            title, step_count, mtime = summaries.get(cid, ("Untitled", 0, ""))
            if not mtime:
                try:
                    mtime_ts = os.path.getmtime(db_file)
                    mtime = str(mtime_ts)
                except Exception:
                    pass

            metrics = parse_conversation_db(db_file, title, step_count, mtime)
            if metrics and metrics.usage.total_tokens > 0:
                metrics_list.append(metrics)

        return metrics_list
