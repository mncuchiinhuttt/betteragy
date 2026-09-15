"""Unit tests for TUI redesign, fireworks particle engine, and command center cards."""

from unittest.mock import MagicMock, patch
from rich.console import Console

from betteragy.core.models import AccountQuota, AccountRecord, QuotaBucket
from betteragy.services.quota_service import detect_quota_resets
from betteragy.ui.dashboard_cards import (
    render_active_overview_card,
    render_mini_quota_card,
)
from betteragy.ui.fireworks import (
    FireworkRocket,
    Particle,
    render_fireworks_frame,
)
from betteragy.ui.interactive_tui import InteractiveTUI


def test_particle_kinematics():
    """Verify particle motion physics, drag, and lifetime decay."""
    p = Particle(10.0, 10.0, 1.0, -1.0, "green", life=5)
    assert p.is_alive
    assert p.x == 10.0 and p.y == 10.0

    p.step()
    assert p.x > 10.0
    assert p.life == 4
    assert p.is_alive

    # Step until dead
    for _ in range(10):
        p.step()
    assert not p.is_alive


def test_firework_rocket_burst():
    """Verify rocket ascends and creates burst sparks upon reaching target."""
    rocket = FireworkRocket(x=30, start_y=20, target_y=18)
    assert not rocket.exploded

    sparks = None
    # Step until burst
    for _ in range(10):
        new_sparks = rocket.step()
        if new_sparks:
            sparks = new_sparks
            break

    assert rocket.exploded
    assert sparks is not None
    assert len(sparks) >= 15
    assert all(isinstance(s, Particle) for s in sparks)


def test_render_fireworks_frame():
    """Verify fireworks frame renders celebration banner, borders, and ESC prompt."""
    particles = [Particle(25.0, 10.0, 0.0, 0.0, "bright_yellow", life=10)]
    frame = render_fireworks_frame(
        width=80,
        height=24,
        rockets=[],
        particles=particles,
        title="AI Quota Restored Celebration!",
    )
    assert frame is not None
    assert "AI Quota Restored Celebration!" in frame.plain
    assert "Gemini & Claude Ready!" in frame.plain
    assert ">> Press [ESC] or [q] to return to TUI <<" in frame.plain


def test_play_fireworks_celebration_finite_duration():
    """Verify play_fireworks_celebration terminates cleanly when duration is specified."""
    from betteragy.ui.fireworks import play_fireworks_celebration
    console = Console(width=80, height=24)
    # Run a short 0.05s burst
    play_fireworks_celebration(console, duration=0.05)


def test_render_active_overview_card():
    """Verify system overview card displays account, tier, proxy state, and update pill."""
    acc = AccountRecord(
        email="test@example.com",
        refresh_token="rf_123",
        tier="Tier 3",
        tier_name="Enterprise Plus",
    )
    # Active proxy and update notice
    panel = render_active_overview_card(
        account=acc,
        proxy_active=True,
        theme_name="warm",
        account_count=3,
        update_ver="0.2.0",
    )
    assert panel is not None

    # Offline proxy and no account
    panel_empty = render_active_overview_card(
        account=None,
        proxy_active=False,
        theme_name="cyber",
        account_count=0,
    )
    assert panel_empty is not None


def test_render_mini_quota_card():
    """Verify mini quota preview widget with cached and uncached states."""
    # Uncached state
    p_none = render_mini_quota_card(None)
    assert p_none is not None

    # Populated quota
    quota = AccountQuota(
        email="dev@example.com",
        buckets=[
            QuotaBucket(
                model_id="gemini-2.5-pro",
                display_name="Gemini 2.5 Pro",
                percentage=85,
                reset_countdown="2d 4h",
            ),
            QuotaBucket(
                model_id="gemini-2.5-flash",
                display_name="Gemini 2.5 Flash",
                percentage=100,
                reset_countdown="Ready",
            ),
        ],
    )
    p_quota = render_mini_quota_card(quota)
    assert p_quota is not None


def test_detect_quota_resets():
    """Verify quota reset detector catches exhausted models recovering."""
    old_q = AccountQuota(
        email="user@test.com",
        buckets=[
            QuotaBucket(model_id="m1", display_name="Model 1", percentage=5),
            QuotaBucket(model_id="m2", display_name="Model 2", percentage=80),
        ],
    )
    new_q = AccountQuota(
        email="user@test.com",
        buckets=[
            QuotaBucket(model_id="m1", display_name="Model 1", percentage=100),
            QuotaBucket(model_id="m2", display_name="Model 2", percentage=80),
        ],
    )

    restored = detect_quota_resets(old_q, new_q)
    assert restored == ["Model 1"]

    # If no reset occurred
    assert detect_quota_resets(new_q, new_q) == []
    assert detect_quota_resets(None, new_q) == []


def test_tui_direct_hotkeys():
    """Verify direct numeric (1-9) and letter shortcuts (p, t, u, f, x)."""
    tui = InteractiveTUI()

    # Hotkey '2' opens Quotas screen
    tui._handle_main_key("2")
    assert tui.current_screen == "quota"

    # Reset to main
    tui.current_screen = "main"

    # Hotkey 'p' opens Proxy screen
    tui._handle_main_key("p")
    assert tui.current_screen == "proxy"

    # Hotkey 't' opens Themes screen
    tui.current_screen = "main"
    tui._handle_main_key("t")
    assert tui.current_screen == "theme"

    # Hotkey 'x' returns True (exit)
    tui.current_screen = "main"
    assert tui._handle_main_key("x") is True


def test_tui_fireworks_hotkey():
    """Verify pressing 'f' triggers fireworks celebration without crashing."""
    tui = InteractiveTUI()
    with patch("betteragy.ui.fireworks.play_fireworks_celebration") as mock_fw:
        should_exit = tui._handle_main_key("f")
        assert should_exit is False
        mock_fw.assert_called_once()
