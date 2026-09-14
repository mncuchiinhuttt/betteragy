"""Unit tests for model pricing and cost calculation."""

from betteragy.services.pricing_service import calculate_cost, match_pricing


def test_match_pricing():
    rate_opus = match_pricing("claude-opus-4-6-thinking")
    assert rate_opus.input_usd == 15.00
    assert rate_opus.output_usd == 75.00

    rate_sonnet = match_pricing("claude-sonnet-4-6")
    assert rate_sonnet.input_usd == 3.00

    rate_flash = match_pricing("gemini-3.8-flash")
    assert rate_flash.input_usd == 0.75
    assert rate_flash.output_usd == 3.75
    assert rate_flash.reasoning_usd == 3.75

    rate_pro = match_pricing("gemini-3.1-pro")
    assert rate_pro.input_usd == 2.00
    assert rate_pro.output_usd == 12.00


def test_calculate_cost():
    # 1,000,000 input tokens of Sonnet 4.6 should be $3.00
    cost = calculate_cost("claude-sonnet-4-6", inp=1_000_000)
    assert cost == 3.0

    # 1,000,000 output tokens of Opus 4.6 should be $75.00
    cost_opus = calculate_cost("claude-opus-4-6-thinking", out=1_000_000)
    assert cost_opus == 75.0

    # Gemini 3.8 Flash with 1M in, 100k out, 900k reasoning
    # (1M * 0.75 + 100k * 3.75 + 900k * 3.75) / 1M = 0.75 + 0.375 + 3.375 = 4.5
    cost_flash = calculate_cost("gemini-3.8-flash", inp=1_000_000, out=100_000, reasoning=900_000)
    assert cost_flash == 4.5
