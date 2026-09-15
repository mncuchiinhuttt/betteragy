"""HUD service: extracts real-time token telemetry and task duration for Antigravity statusLine."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import time
from typing import Optional

from ..core.constants import AG_CLI_BRAIN_DIR, AG_CLI_CONVERSATIONS_DIR
from .protobuf_decoder import extract_tokens_from_gen_metadata


def format_token_count(count: int) -> str:
    """Format token count into compact human-readable representation."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}k"
    return str(count)


def get_latest_turn_tokens(conversation_id: str) -> tuple[int, int, int, int]:
    """Extract (input, output, cache, reasoning) tokens from latest turn in conversation DB."""
    if not conversation_id:
        return 0, 0, 0, 0

    db_path = AG_CLI_CONVERSATIONS_DIR / f"{conversation_id}.db"
    if not db_path.exists():
        return 0, 0, 0, 0

    try:
        con = sqlite3.connect(str(db_path), timeout=0.2)
        cur = con.cursor()
        cur.execute("SELECT data FROM gen_metadata ORDER BY idx DESC LIMIT 1")
        row = cur.fetchone()
        con.close()
        if row and row[0]:
            extracted = extract_tokens_from_gen_metadata(row[0])
            if extracted:
                return extracted[1], extracted[2], extracted[3], extracted[4]
    except Exception:
        pass
    return 0, 0, 0, 0


def get_prompt_duration(conversation_id: str, transcript_hint: Optional[str] = None, agent_state: str = "") -> float:
    """Calculate execution duration of the current prompt in seconds from transcript log."""
    tpath = None
    if transcript_hint:
        p = Path(transcript_hint)
        if p.exists():
            tpath = p
        else:
            # Check ~/.gemini/antigravity-cli/brain/<id>/...
            fixed = Path(str(p).replace("/antigravity/", "/antigravity-cli/"))
            if fixed.exists():
                tpath = fixed

    if not tpath and conversation_id:
        candidate = AG_CLI_BRAIN_DIR / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"
        if candidate.exists():
            tpath = candidate

    if not tpath or not tpath.exists():
        return 0.0

    try:
        with open(tpath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        last_user_iso = None
        last_model_iso = None
        for line in reversed(lines[-25:]):
            if not line.strip():
                continue
            entry = json.loads(line)
            etype = entry.get("type")
            if not last_model_iso and etype in ("PLANNER_RESPONSE", "TOOL_CALL", "MODEL_RESPONSE"):
                last_model_iso = entry.get("created_at")
            if etype == "USER_INPUT":
                last_user_iso = entry.get("created_at")
                break

        if last_user_iso:
            user_dt = datetime.fromisoformat(last_user_iso.replace("Z", "+00:00"))
            if agent_state == "working" or not last_model_iso:
                now_dt = datetime.now(timezone.utc)
                return max(0.0, (now_dt - user_dt).total_seconds())
            else:
                model_dt = datetime.fromisoformat(last_model_iso.replace("Z", "+00:00"))
                return max(0.0, (model_dt - user_dt).total_seconds())
    except Exception:
        pass
    return 0.0


def render_statusline_hud(payload: dict) -> str:
    """Render high-contrast, compact ANSI statusline HUD from agy payload."""
    model_info = payload.get("model") or {}
    model_name = model_info.get("display_name") or model_info.get("id") or "Gemini"
    short_model = model_name.replace("Gemini ", "Gemini-").replace("Claude ", "Claude-")
    effort = model_info.get("effort")

    cid = payload.get("conversation_id") or payload.get("session_id") or ""
    transcript_path = payload.get("transcript_path")
    agent_state = payload.get("agent_state") or ""

    # 1. Tokens
    inp, out, cache, reas = get_latest_turn_tokens(cid)

    # 2. Duration
    dur = get_prompt_duration(cid, transcript_path, agent_state)

    # 3. Quota
    quota_info = payload.get("quota") or {}
    quota_5h = quota_info.get("gemini-5h") or quota_info.get("3p-5h") or {}
    remaining_pct = int(quota_5h.get("remaining_fraction", 1.0) * 100)

    # ANSI Colors
    CYAN = "\033[1;36m"
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    MAGENTA = "\033[1;35m"
    WHITE = "\033[1;37m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    parts = []

    # Model pill
    effort_str = f"/{effort}" if effort else ""
    parts.append(f"{CYAN}[{short_model}{effort_str}]{RESET}")

    # Duration pill
    if dur > 0:
        dur_color = GREEN if dur < 5.0 else (YELLOW if dur < 15.0 else "\033[1;31m")
        parts.append(f"{dur_color}⚡ {dur:.1f}s{RESET}")

    # Token pill
    if inp > 0 or out > 0 or cache > 0:
        cache_ratio = f" ({int(cache / (cache + inp) * 100)}%)" if (cache + inp) > 0 and cache > 0 else ""
        token_str = (
            f"{DIM}In:{RESET}{WHITE}{format_token_count(inp)}{RESET} "
            f"{DIM}Out:{RESET}{WHITE}{format_token_count(out)}{RESET} "
            f"{DIM}Cache:{RESET}{GREEN}{format_token_count(cache)}{cache_ratio}{RESET}"
        )
        if reas > 0:
            token_str += f" {MAGENTA}🧠 {format_token_count(reas)}{RESET}"
        parts.append(token_str)

    # Quota pill
    q_color = GREEN if remaining_pct >= 50 else (YELLOW if remaining_pct >= 20 else "\033[1;31m")
    parts.append(f"{DIM}5h:{RESET}{q_color}{remaining_pct}%{RESET}")

    # Separator
    return f" {DIM}|{RESET} ".join(parts)
