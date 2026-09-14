# Phase 04: Offline SQLite & LS Usage Scanner & Cost Calculator

## Overview
- **Priority**: P0 (Key Feature requested by user)
- **Current Status**: Planned
- **Description**: Read conversation history from `~/.gemini/antigravity-cli/conversations/*.db` and `conversation_summaries.db` (plus Antigravity IDE paths if present), extract token telemetry (Input, Output, Cache Read/Write, Reasoning), apply LiteLLM pricing, and compute aggregations.

## Key Insights
- CLI conversations are stored in SQLite files (`<uuid>.db`) with tables `gen_metadata` and `steps`.
- Protobuf payload contains exact token fields:
  - Input tokens
  - Cache read tokens
  - Output tokens
  - Reasoning / thinking tokens
  - Model name / enum
- Offline SQLite parsing allows 100% offline usage calculation with ZERO dependence on running IDE or servers.
- Dynamic LiteLLM pricing catalog maps models to costs per 1M tokens, calculating estimated USD cost.
- Incremental mtime disk caching ensures lightning-fast queries (<50ms).

## Architecture & Data Flow
```
~/.gemini/antigravity-cli/conversations/*.db & conversation_summaries.db
                               │
                               ▼
                    SQLite / Protobuf Parser
                               │
                               ▼
                     Token Telemetry Extractor
                               │
                               ▼
                   LiteLLM Pricing Matcher ($)
                               │
                               ▼
             Timeframe Aggregator (24h / 7d / 30d / all-time)
                               │
                               ▼
                     Disk Cache (~/.config/betteragy/cache.json)
```

## Related Code Files
- [NEW] `src/betteragy/services/protobuf_decoder.py`
- [NEW] `src/betteragy/services/pricing_service.py`
- [NEW] `src/betteragy/services/usage_scanner.py`
- [NEW] `src/betteragy/services/usage_aggregator.py`
- [NEW] `src/betteragy/services/usage_cache.py`

## Implementation Steps
1. Create `protobuf_decoder.py`: Lightweight standalone wire-format varint/length-delimited parser to extract token usage fields from SQLite BLOBs.
2. Create `pricing_service.py`: LiteLLM pricing catalog with local fallback rates for Gemini and Claude models.
3. Create `usage_scanner.py`: Scan conversation SQLite databases and summary index; extract token counts and conversation metadata.
4. Create `usage_aggregator.py`: Aggregate tokens and costs by model, timeframe, and top conversations.
5. Create `usage_cache.py`: Cache processed conversation statistics with mtime invalidation.

## Todo List
- [ ] Implement lightweight Protobuf wire decoder
- [ ] Implement Model Pricing Engine
- [ ] Implement Local SQLite Conversation Scanner
- [ ] Implement Token & Cost Aggregator (timeline, models, ranking)
- [ ] Implement Incremental Disk Cache
