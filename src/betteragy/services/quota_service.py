"""Quota service: queries Google Cloud Code Assist APIs for live model limits."""

import json
import time
from typing import Optional
import urllib.error
import urllib.request
from datetime import datetime, timezone

from ..core.constants import (
    HTTP_TIMEOUT_SECONDS,
    LOAD_CODE_ASSIST_ENDPOINTS,
    QUOTA_API_ENDPOINTS,
    USER_AGENT,
)
from ..core.models import AccountQuota, QuotaBucket
from .model_catalog import humanize_model_id


def format_reset_time(iso_str: str) -> tuple[str, str]:
    """Parse ISO resetTime into local formatted time (HH:MM) and countdown string."""
    if not iso_str:
        return "", ""
    try:
        clean_iso = iso_str.replace("Z", "+00:00")
        reset_dt = datetime.fromisoformat(clean_iso)
        local_time_str = reset_dt.astimezone().strftime("%H:%M")

        now_ts = time.time()
        diff_sec = reset_dt.timestamp() - now_ts
        if diff_sec <= 0:
            countdown = "Ready"
        elif diff_sec < 3600:
            mins = int(diff_sec // 60)
            countdown = f"in {mins}m"
        elif diff_sec < 86400:
            hrs = int(diff_sec // 3600)
            mins = int((diff_sec % 3600) // 60)
            countdown = f"in {hrs}h {mins}m"
        else:
            days = int(diff_sec // 86400)
            countdown = f"in {days}d"
        return local_time_str, countdown
    except Exception:
        return iso_str, ""


def post_json(endpoint: str, data: dict, access_token: str) -> dict:
    """Send authenticated JSON POST request to CloudCode API."""
    body_bytes = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body_bytes,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode("utf-8"))


class QuotaService:
    """Fetches and parses user quotas from Google Cloud Code Assist."""

    def load_project_info(self, access_token: str) -> tuple[str, str | None, str | None]:
        """Fetch project ID, paid tier, and current tier name."""
        project_id = "cloudaicompanion-enterprise"
        tier_id = None
        tier_name = None

        for ep in LOAD_CODE_ASSIST_ENDPOINTS:
            try:
                res = post_json(ep, {"metadata": {"ideType": "ANTIGRAVITY"}}, access_token)
                project_id = res.get("cloudaicompanionProject", project_id)
                paid = res.get("paidTier") or {}
                curr = res.get("currentTier") or {}
                tier_id = paid.get("id") or curr.get("id")
                tier_name = paid.get("name") or curr.get("name")
                break
            except Exception:
                continue

        return project_id, tier_id, tier_name

    def fetch_quota(self, email: str, access_token: str) -> AccountQuota:
        """Retrieve live quota buckets for an account."""
        project_id, tier_id, tier_name = self.load_project_info(access_token)
        quota_data = None
        last_err = ""

        for ep in QUOTA_API_ENDPOINTS:
            try:
                quota_data = post_json(ep, {"project": project_id}, access_token)
                break
            except urllib.error.HTTPError as e:
                last_err = f"HTTP {e.code}: {e.reason}"
                if e.code == 403:
                    return AccountQuota(
                        email=email, project_id=project_id, tier=tier_id,
                        tier_name=tier_name, is_forbidden=True
                    )
                if e.code == 401:
                    return AccountQuota(
                        email=email, project_id=project_id, tier=tier_id,
                        tier_name=tier_name, is_error=True, error_message="Unauthorized (401)"
                    )
            except Exception as e:
                last_err = str(e)
                continue

        if not quota_data:
            return AccountQuota(
                email=email, project_id=project_id, tier=tier_id,
                tier_name=tier_name, is_error=True, error_message=last_err or "Failed to connect"
            )

        raw_buckets = quota_data.get("buckets", [])
        parsed_buckets: list[QuotaBucket] = []

        for b in raw_buckets:
            model_id = b.get("modelId", "")
            if not model_id:
                continue

            fraction = float(b.get("remainingFraction") or b.get("remaining_fraction") or 0.0)
            reset_time_raw = b.get("resetTime", "")
            time_str, countdown = format_reset_time(reset_time_raw)
            display_name = humanize_model_id(model_id)

            parsed_buckets.append(
                QuotaBucket(
                    model_id=model_id,
                    display_name=display_name,
                    remaining_fraction=fraction,
                    percentage=round(fraction * 100),
                    reset_time_raw=reset_time_raw,
                    reset_time_str=time_str,
                    reset_countdown=countdown,
                )
            )

        parsed_buckets.sort(key=lambda x: x.display_name)
        return AccountQuota(
            email=email,
            project_id=project_id,
            tier=tier_id,
            tier_name=tier_name,
            buckets=parsed_buckets,
        )


def detect_quota_resets(old_quota: Optional[AccountQuota], new_quota: Optional[AccountQuota]) -> list[str]:
    """Detect if any exhausted or low model quotas were restored/reset.

    Returns a list of model display names that were restored.
    """
    if not old_quota or not new_quota or old_quota.is_error or new_quota.is_error:
        return []
    restored: list[str] = []
    old_map = {b.model_id: b.percentage for b in old_quota.buckets}
    for b in new_quota.buckets:
        old_pct = old_map.get(b.model_id, 100)
        # If model was low/exhausted (<= 20%) and has recovered significantly (>= 50%)
        if old_pct <= 20 and (b.percentage >= 50 or (b.percentage - old_pct) >= 30):
            restored.append(b.display_name or b.model_id)
    return restored
