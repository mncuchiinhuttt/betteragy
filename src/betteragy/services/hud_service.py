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
    """Render a premium Powerline pill-style statusline HUD with ANSI 24-bit TrueColor."""
    model_info = payload.get("model") or {}
    model_name = model_info.get("display_name") or model_info.get("id") or "Gemini"
    short_model = model_name.replace("Gemini ", "Gemini-").replace("Claude ", "Claude-")
    effort = model_info.get("effort")

    cid = payload.get("conversation_id") or payload.get("session_id") or ""
    transcript_path = payload.get("transcript_path")
    agent_state = payload.get("agent_state") or ""

    inp, out, cache, reas = get_latest_turn_tokens(cid)
    dur = get_prompt_duration(cid, transcript_path, agent_state)

    quota_info = payload.get("quota") or {}
    quota_5h = quota_info.get("gemini-5h") or quota_info.get("3p-5h") or {}
    remaining_pct = int(quota_5h.get("remaining_fraction", 1.0) * 100)

    # TrueColor ANSI Powerline Badges
    # Model pill: Deep Indigo background with white text
    effort_suffix = f":{effort}" if effort else ""
    model_badge = f"\033[48;2;30;41;59m\033[38;2;241;245;249m\033[1m ◉ {short_model}{effort_suffix} \033[0m"

    # Duration pill
    if dur > 0:
        dur_bg = "48;2;16;185;129m" if dur < 5.0 else ("48;2;217;119;6m" if dur < 15.0 else "48;2;239;68;68m")
        dur_badge = f"\033[{dur_bg}\033[38;2;15;23;42m\033[1m ⚡ {dur:.1f}s \033[0m"
    else:
        dur_badge = ""

    # Tokens pill
    if inp > 0 or out > 0 or cache > 0:
        cache_str = f"|C:{format_token_count(cache)}" if cache > 0 else ""
        reas_str = f"|🧠{format_token_count(reas)}" if reas > 0 else ""
        tok_badge = f"\033[48;2;15;23;42m\033[38;2;148;163;184m ↑{format_token_count(inp)} ↓{format_token_count(out)}{cache_str}{reas_str} \033[0m"
    else:
        tok_badge = ""

    # Active task progress pill (from tasks.db)
    task_badge = ""
    try:
        from ..mcp.task_db import TaskDB
        db = TaskDB()
        sess = db.get_active_session()
        if sess:
            total_t = sess.get("total_tasks") or 0
            comp_t = sess.get("completed_tasks") or 0
            tasks = db.get_tasks(session_id=sess["id"])
            # Find in_progress task or first pending
            curr = next((t for t in tasks if t.get("status") == "in_progress"), None)
            if not curr and tasks:
                curr = next((t for t in tasks if t.get("status") == "pending"), None)
            if curr:
                t_title = curr["title"][:22] + ".." if len(curr["title"]) > 22 else curr["title"]
                ratio = f"[{comp_t}/{total_t}]" if total_t > 0 else ""
                task_badge = f"\033[48;2;24;24;27m\033[38;2;245;158;11m\033[1m ◼ {ratio} {t_title} \033[0m"
    except Exception:
        pass

    # Quota pill
    q_color = "\033[38;2;52;211;153m" if remaining_pct >= 50 else ("\033[38;2;251;191;36m" if remaining_pct >= 20 else "\033[38;2;248;113;113m")
    quota_badge = f"\033[48;2;30;41;59m {q_color}\033[1m5h:{remaining_pct}%\033[0m\033[48;2;30;41;59m \033[0m"

    pills = [p for p in [model_badge, dur_badge, tok_badge, task_badge, quota_badge] if p]
    return " ".join(pills)
