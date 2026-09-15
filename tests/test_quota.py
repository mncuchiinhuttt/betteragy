"""Unit tests for model catalog and quota formatters."""

import time
from datetime import datetime, timezone
from betteragy.services.model_catalog import humanize_model_id
from betteragy.services.quota_service import format_reset_time


def test_humanize_model_id():
    assert humanize_model_id("gemini-3.1-pro-high") == "Gemini 3.1 Pro (High)"
    assert humanize_model_id("gemini-3-flash") == "Gemini 3 Flash"
    assert humanize_model_id("claude-opus-4-6-thinking") == "Claude Opus 4.6 (Thinking)"
    assert humanize_model_id("claude-sonnet-4-6") == "Claude Sonnet 4.6"
    assert humanize_model_id("gpt-oss-120b-medium") == "GPT-OSS 120B (Medium)"
    assert humanize_model_id("unknown-custom-model-thinking") == "Unknown Custom Model (Thinking)"


def test_format_reset_time():
    now = time.time()
    # 2 hours in the future
    future_dt = datetime.fromtimestamp(now + 7200, timezone.utc)
    time_str, countdown = format_reset_time(future_dt.isoformat())
    assert time_str != ""
    assert "in 1h" in countdown or "in 2h" in countdown

    # Past time -> Ready
    past_dt = datetime.fromtimestamp(now - 300, timezone.utc)
    _, countdown_past = format_reset_time(past_dt.isoformat())
    assert countdown_past == "Ready"

    # Empty
    assert format_reset_time("") == ("", "")


def test_render_progress_bar():
    """Verify render_progress_bar creates smooth solid block bar with right-aligned %."""
    from rich.console import Console
    from betteragy.ui.theme import render_progress_bar

    console = Console(record=True, width=80)

    # 100% (green, 10 '█')
    bar_100 = render_progress_bar(100, width=10)
    assert "100%" in bar_100
    assert "█" * 10 in bar_100
    console.print(bar_100)
    out_100 = console.export_text()
    assert "██████████ 100%" in out_100

    from betteragy.ui.theme_manager import get_theme_manager
    th = get_theme_manager().get_active_theme()

    # 50% (quota_high >= 50%)
    bar_50 = render_progress_bar(50, width=10)
    assert "50%" in bar_50
    assert th.quota_high in bar_50
    assert "█" * 5 in bar_50
    assert "░" * 5 in bar_50

    # 49% (quota_mid < 50%)
    bar_49 = render_progress_bar(49, width=10)
    assert "49%" in bar_49
    assert th.quota_mid in bar_49

    # 28% (quota_mid, 3 '█', 7 '░')
    bar_28 = render_progress_bar(28, width=10)
    assert "28%" in bar_28
    assert th.quota_mid in bar_28
    assert "█" * 3 in bar_28
    assert "░" * 7 in bar_28

    # 19% (quota_low < 20%)
    bar_19 = render_progress_bar(19, width=10)
    assert "19%" in bar_19
    assert th.quota_low in bar_19

    # 0% (quota_low, 0 '█', 10 '░')
    bar_0 = render_progress_bar(0, width=10)
    assert "0%" in bar_0
    assert th.quota_low in bar_0
    assert th.quota_low_track in bar_0
    assert "░" * 10 in bar_0

    # Clamping tests (< 0 and > 100)
    assert "0%" in render_progress_bar(-10)
    assert "100%" in render_progress_bar(150)
