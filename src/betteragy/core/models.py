"""Pydantic data models for accounts, quotas, and token usage."""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class AccountRecord(BaseModel):
    """Represents a tracked Google/Antigravity account."""
    email: str
    name: str = ""
    picture: str = ""
    refresh_token: str
    access_token: str = ""
    expiry: str = ""
    tier: Optional[str] = None
    tier_name: Optional[str] = None
    last_used: float = 0.0
    cooldown_until: float = 0.0
    disabled: bool = False


class AccountsStorage(BaseModel):
    """Storage container for all accounts and switcher preferences."""
    active_email: Optional[str] = None
    rotate_strategy: Literal["round-robin", "random", "sticky", "least-used"] = "round-robin"
    accounts: list[AccountRecord] = Field(default_factory=list)


class QuotaBucket(BaseModel):
    """Model quota bucket returned from Google Cloud Code Assist."""
    model_id: str
    display_name: str
    remaining_fraction: float = 1.0
    percentage: int = 100
    reset_time_raw: str = ""
    reset_time_str: str = ""
    reset_countdown: str = ""


class AccountQuota(BaseModel):
    """Full quota profile for an account."""
    email: str
    project_id: str = "cloudaicompanion-enterprise"
    tier: Optional[str] = None
    tier_name: Optional[str] = None
    buckets: list[QuotaBucket] = Field(default_factory=list)
    is_forbidden: bool = False
    is_error: bool = False
    error_message: str = ""


class TokenUsage(BaseModel):
    """Telemetry token counts and calculated costs."""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0
    calls_count: int = 0
    cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_read_tokens
            + self.cache_write_tokens
            + self.reasoning_tokens
        )


class ModelUsageSummary(BaseModel):
    """Usage aggregate for a specific AI model."""
    model_name: str
    display_name: str
    usage: TokenUsage


class ConversationMetrics(BaseModel):
    """Token usage and metadata for a single conversation."""
    conversation_id: str
    title: str = "Untitled"
    step_count: int = 0
    last_modified: str = ""
    usage: TokenUsage


class DeepUsageReport(BaseModel):
    """Aggregated token usage report across all conversations."""
    total_usage: TokenUsage
    date_range_from: str = ""
    date_range_to: str = ""
    conversations_count: int = 0
    models: list[ModelUsageSummary] = Field(default_factory=list)
    top_conversations: list[ConversationMetrics] = Field(default_factory=list)
