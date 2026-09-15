"""Unit tests for the real-time Antigravity statusline HUD service and CLI."""

import json
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from betteragy.cli import app
from betteragy.services.hud_service import (
    format_token_count,
    get_latest_turn_tokens,
    get_prompt_duration,
    render_statusline_hud,
)

runner = CliRunner()


def test_format_token_count():
    """Verify compact token formatting."""
    assert format_token_count(42) == "42"
    assert format_token_count(999) == "999"
    assert format_token_count(1000) == "1.0k"
    assert format_token_count(1500) == "1.5k"
    assert format_token_count(29141) == "29.1k"
    assert format_token_count(1_200_000) == "1.2M"


def test_render_statusline_hud_minimal():
    """Verify statusline HUD renders model and quota even without conversation tokens."""
    payload = {
        "model": {"display_name": "Gemini 3.8 Flash (High)", "effort": "high"},
        "quota": {"gemini-5h": {"remaining_fraction": 0.85}},
    }
    hud = render_statusline_hud(payload)
    assert "Gemini-3.8-Flash" in hud or "Gemini-3.8" in hud
    assert "5h:" in hud
    assert "85%" in hud


def test_render_statusline_hud_with_tokens_and_duration():
    """Verify statusline HUD renders token breakdown and duration."""
    payload = {
        "model": {"id": "claude-sonnet-4-6", "display_name": "Claude Sonnet 4.6"},
        "conversation_id": "test-convo-123",
        "quota": {"3p-5h": {"remaining_fraction": 0.50}},
    }
    with patch("betteragy.services.hud_service.get_latest_turn_tokens", return_value=(1500, 200, 28000, 50)), \
         patch("betteragy.services.hud_service.get_prompt_duration", return_value=3.4):
        hud = render_statusline_hud(payload)
        assert "Claude-Sonnet" in hud
        assert "3.4s" in hud
        assert "In:" in hud and "1.5k" in hud
        assert "Out:" in hud and "200" in hud
        assert "Cache:" in hud and "28.0k" in hud
        assert "50%" in hud


def test_get_prompt_duration_from_transcript(tmp_path):
    """Verify duration extraction from transcript.jsonl."""
    log_dir = tmp_path / "brain" / "cid-123" / ".system_generated" / "logs"
    log_dir.mkdir(parents=True)
    transcript = log_dir / "transcript.jsonl"
    transcript.write_text(
        json.dumps({"type": "USER_INPUT", "created_at": "2026-09-15T12:00:00Z"}) + "\n" +
        json.dumps({"type": "PLANNER_RESPONSE", "created_at": "2026-09-15T12:00:05Z"}) + "\n",
        encoding="utf-8",
    )
    with patch("betteragy.services.hud_service.AG_CLI_BRAIN_DIR", tmp_path / "brain"):
        dur = get_prompt_duration("cid-123", agent_state="idle")
        assert dur == 5.0


def test_hud_cli_commands(tmp_path):
    """Verify betteragy hud enable, disable, and status commands."""
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{}", encoding="utf-8")

    with patch("betteragy.commands.hud_cmd.SETTINGS_PATH", settings_file):
        # 1. Enable HUD
        res = runner.invoke(app, ["hud", "enable"])
        assert res.exit_code == 0
        assert "ENABLED" in res.output
        data = json.loads(settings_file.read_text(encoding="utf-8"))
        assert data["statusLine"]["enabled"] is True
        assert "betteragy hud" in data["statusLine"]["command"]

        # 2. Status HUD
        res_status = runner.invoke(app, ["hud", "status"])
        assert res_status.exit_code == 0
        assert "ACTIVE" in res_status.output

        # 3. Disable HUD
        res_dis = runner.invoke(app, ["hud", "disable"])
        assert res_dis.exit_code == 0
        assert "disabled" in res_dis.output
        data2 = json.loads(settings_file.read_text(encoding="utf-8"))
        assert data2["statusLine"]["enabled"] is False
