# Phase 1: Architecture Trade-Offs & Specification

## Context Links
- Master Plan: [plan.md](file:///Users/vominhlong/betteragy/plans/260914-2140-agy-deep-thinking-and-todo-harness/plan.md)
- System Architecture: [system-architecture.md](file:///Users/vominhlong/betteragy/docs/system-architecture.md)
- Development Roadmap: [development-roadmap.md](file:///Users/vominhlong/betteragy/docs/development-roadmap.md)

## Overview
- **Priority**: High
- **Current Status**: In Progress
- **Brief Description**: Comprehensive evaluation of 3 architectural paradigms (MitM Network Proxy, Native MCP + Rule Harness, and Interactive Subprocess Orchestrator) to establish the optimal technical foundation for upgrading `agy` through `betteragy`.

## Key Insights
1. **Network MitM Proxy (`HTTP_PROXY`)**:
   - `agy` respects `HTTP_PROXY` and `HTTPS_PROXY`.
   - Intercepting `daily-cloudcode-pa.googleapis.com` requires installing a custom Root CA certificate into macOS Keychain (`security add-trusted-cert`).
   - Fragile when Google updates SSE framing, gRPC transport, or protobuf serialization.
2. **Native Rule Harness + MCP Protocol**:
   - `agy` reads `~/.gemini/config/rules/*.md` and `~/.gemini/GEMINI.md` as `<RULE[user_global]>`.
   - `agy` supports native MCP servers via `~/.gemini/settings.json` and `mcp_config.json`.
   - Zero TLS certificate friction, zero network latency overhead, and 100% native LLM function-calling support.
3. **Outer Super-Harness / Agent Wrapper**:
   - Running `betteragy agent` allows wrapping `agy` execution with `--effort high`, while streaming live tasks onto a pinned ASCII header or split dashboard.

## Requirements
### Functional Requirements
- Evaluate architectural trade-offs between MitM Proxy and Native MCP/Harness.
- Specify data contracts for thinking budget enhancement, verification checklist, and task state tracking.
- Provide a clear recommendation aligned with YAGNI, KISS, and DRY.

### Non-Functional Requirements
- Maintain zero-latency overhead during streaming.
- No invasive patching of binary `/Users/vominhlong/.local/bin/agy`.
- Complete compatibility across macOS and Linux.

## Architecture & Trade-Off Matrix

| Dimension | Option A: MitM Network Proxy | Option B: Native MCP + Rule Harness (Recommended) | Option C: Outer Super-Harness CLI |
|---|---|---|---|
| **Mechanism** | Intercepts HTTPS `/v1internal:streamGenerateContent` | Injects rule files into `~/.gemini/config/rules` + registers MCP server | Spawns `agy` in pseudo-terminal with pinned task panel |
| **TLS / SSL Requirement** | Requires local Root CA in Keychain | None (0 certs required) | None |
| **Reliability** | Medium (vulnerable to API schema shifts) | Very High (standard MCP & native rule loading) | Very High (process wrapper) |
| **To-Do Functionality** | Requires synthetic tool mocking in stream | Native tool calling (`todo_create`, `todo_update`) | Native tool calling + ASCII visualizer |
| **Thinking Budget** | Injected via JSON payload modification | Configured via `--effort high` + prompt instructions | Configured via `--effort high` + prompt instructions |
| **Complexity** | High (mitmproxy/TLS engine) | Low-Medium (clean Python MCP server) | Medium (Rich PTY wrapper) |

### Recommended Hybrid Strategy: "Tri-Shield Architecture"
1. **Layer 1: Rule & Prompt Harness**: Inject strict chain-of-thought, verification checklist, and falsification rules into `~/.gemini/config/rules/betteragy-harness.md`.
2. **Layer 2: Betteragy MCP Task Server**: Lightweight JSON-RPC stdio MCP server exposing `todo_create`, `todo_update`, `todo_list`, backed by SQLite (`~/.config/betteragy/tasks.db`).
3. **Layer 3: Interactive Super-Harness (`betteragy agent`)**: Wrapper CLI that launches `agy` with `--effort high` and renders a live ASCII task progress board.

## Related Code Files
- Files to create:
  - `src/betteragy/harness/__init__.py`
  - `src/betteragy/harness/prompt_templates.py`
  - `src/betteragy/harness/harness_manager.py`
- Files to modify:
  - `docs/system-architecture.md`
  - `docs/development-roadmap.md`

## Implementation Steps
1. Formalize specification for prompt directives and verification gates.
2. Define JSON schema for MCP To-Do tools (`todo_create`, `todo_update`, `todo_list`).
3. Document hybrid architecture in `docs/system-architecture.md`.

## Todo List
- [x] Analyze `agy` binary network and configuration hooks
- [x] Compare MitM Proxy vs Native MCP Harness
- [ ] Define MCP tool contracts and JSON schemas
- [ ] Finalize hybrid architecture documentation

## Success Criteria
- Clear, unassailable trade-off comparison presented to user.
- Zero-TLS-friction approach chosen as primary path.

## Risk Assessment
- **Risk**: User explicitly wants network-level proxy.
- **Mitigation**: Keep proxy as an optional plugin (`betteragy proxy --start`) for packet inspection and dynamic header overrides, while using MCP for To-Do operations.

## Security Considerations
- Prevent arbitrary script injection in prompt templates.
- Ensure SQLite task database is scoped to `0600` permissions.

## Next Steps
- Implement Phase 2: Deep Thinking Harness & Rules.
