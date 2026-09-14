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
