"""Token pricing catalog and estimated cost calculator in USD."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RatePerMillion:
    """Pricing rates per 1,000,000 tokens."""
    input_usd: float
    output_usd: float
    cache_read_usd: float = 0.0
    cache_write_usd: float = 0.0
    reasoning_usd: float = 0.0


# Standard pricing table per 1M tokens ($ USD)
PRICING_TABLE: dict[str, RatePerMillion] = {
    # Claude models
    "claude-opus-4-6-thinking": RatePerMillion(15.00, 75.00, 1.50, 18.75, 75.00),
    "claude-opus-4-5-thinking": RatePerMillion(15.00, 75.00, 1.50, 18.75, 75.00),
    "claude-opus": RatePerMillion(15.00, 75.00, 1.50, 18.75, 75.00),
    "claude-sonnet-4-6": RatePerMillion(3.00, 15.00, 0.30, 3.75, 15.00),
    "claude-sonnet-3-7": RatePerMillion(3.00, 15.00, 0.30, 3.75, 15.00),
    "claude-sonnet-3-5": RatePerMillion(3.00, 15.00, 0.30, 3.75, 15.00),
    "claude-sonnet": RatePerMillion(3.00, 15.00, 0.30, 3.75, 15.00),
    "claude-haiku": RatePerMillion(0.25, 1.25, 0.025, 0.30, 1.25),
    # Gemini models
    "gemini-3.1-pro-high": RatePerMillion(1.25, 5.00, 0.3125, 1.56, 5.00),
    "gemini-3.1-pro-low": RatePerMillion(1.25, 5.00, 0.3125, 1.56, 5.00),
    "gemini-3.1-pro": RatePerMillion(1.25, 5.00, 0.3125, 1.56, 5.00),
    "gemini-2.5-pro": RatePerMillion(1.25, 5.00, 0.3125, 1.56, 5.00),
    "gemini-pro": RatePerMillion(1.25, 5.00, 0.3125, 1.56, 5.00),
    "gemini-3-flash": RatePerMillion(0.075, 0.30, 0.01875, 0.09375, 0.30),
    "gemini-3.8-flash": RatePerMillion(0.075, 0.30, 0.01875, 0.09375, 0.30),
    "gemini-2.5-flash": RatePerMillion(0.075, 0.30, 0.01875, 0.09375, 0.30),
    "gemini-flash": RatePerMillion(0.075, 0.30, 0.01875, 0.09375, 0.30),
    # GPT-OSS models
    "gpt-oss-120b-medium": RatePerMillion(0.30, 1.20, 0.075, 0.375, 1.20),
    "gpt-oss": RatePerMillion(0.30, 1.20, 0.075, 0.375, 1.20),
}

DEFAULT_RATE = RatePerMillion(1.00, 3.00, 0.25, 1.25, 3.00)


def match_pricing(model_name: str) -> RatePerMillion:
    """Find matching pricing rate for a given model name."""
    clean = model_name.lower().strip()
    if clean in PRICING_TABLE:
        return PRICING_TABLE[clean]

    for key, rate in PRICING_TABLE.items():
        if key in clean or clean in key:
            return rate

    if "opus" in clean:
        return PRICING_TABLE["claude-opus"]
    if "sonnet" in clean:
        return PRICING_TABLE["claude-sonnet"]
    if "flash" in clean:
        return PRICING_TABLE["gemini-flash"]
    if "pro" in clean:
        return PRICING_TABLE["gemini-pro"]

    return DEFAULT_RATE


def calculate_cost(
    model_name: str,
    inp: int = 0,
    out: int = 0,
    cache_read: int = 0,
    cache_write: int = 0,
    reasoning: int = 0,
) -> float:
    """Calculate estimated USD cost for token usage."""
    rate = match_pricing(model_name)
    cost = (
        (inp * rate.input_usd)
        + (out * rate.output_usd)
        + (cache_read * rate.cache_read_usd)
        + (cache_write * rate.cache_write_usd)
        + (reasoning * rate.reasoning_usd)
    ) / 1_000_000.0
    return round(cost, 4)
