# Phase 03: Live AI Quotas, Tier Resolver & Reset Timers

## Overview
- **Priority**: P0 (Key Feature)
- **Current Status**: Planned
- **Description**: Connect directly to Google Cloud Code Assist API to retrieve live quotas, model buckets, tier names, and reset countdowns for individual accounts and across the entire account pool.

## Key Insights
- Quota API requires two steps:
  1. `loadCodeAssist`: retrieves `cloudaicompanionProject` and `paidTier`/`currentTier`.
  2. `retrieveUserQuota`: retrieves `buckets[]` containing `modelId`, `remainingFraction` (0.0 to 1.0), and `resetTime` (ISO string).
- Models must be humanized (e.g., `gemini-3.1-pro-high` → `Gemini 3.1 Pro (High)`, `claude-opus-4-6-thinking` → `Claude Opus 4.6 (Thinking)`).
- Visual progress bar and reset countdown (e.g. `1h 45m remaining`) should be calculated in local timezone.

## Architecture & Data Flow
```
Account Access Token
       │
       ▼
Google Cloud Code Assist API (loadCodeAssist & retrieveUserQuota)
       │
       ▼
Model Catalog & Humanizer
       │
       ▼
Quota Bucket Parser & Reset Countdown Calculator
       │
       ▼
Multi-Account Quota Aggregator
```

## Related Code Files
- [NEW] `src/betteragy/services/model_catalog.py`
- [NEW] `src/betteragy/services/quota_service.py`
- [NEW] `src/betteragy/services/quota_aggregator.py`

## Implementation Steps
1. Create `model_catalog.py`: Map model slugs and aliases to human-readable names with variant tags (`Thinking`, `High`, `Low`).
2. Create `quota_service.py`: Query `loadCodeAssist` and `retrieveUserQuota`, parse JSON buckets, calculate reset countdowns (`parse_reset_time`).
3. Create `quota_aggregator.py`: Fetch quotas concurrently across all tracked accounts with timeout and error resilience (e.g. 401 handling with auto-refresh).

## Todo List
- [ ] Implement Model Catalog & Slug Normalizer
- [ ] Implement Quota API Client (`loadCodeAssist` + `retrieveUserQuota`)
- [ ] Implement Reset Time & Countdown Calculator
- [ ] Implement Multi-Account Parallel Quota Fetcher
- [ ] Verify against real Google Cloud endpoints
