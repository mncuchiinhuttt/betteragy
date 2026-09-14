# Phase 06: Testing, Hardening & Verification

## Overview
- **Priority**: P1 (Verification & Quality)
- **Current Status**: Planned
- **Description**: Implement comprehensive unit and integration tests, verify Keychain and CloudCode API calls, test rate-limit rotations, and validate CLI build.

## Requirements
- Comprehensive test coverage for:
  - Account configuration & keyring payload encoding/decoding.
  - Protobuf token extractor & SQLite scanning.
  - Quota API bucket parsing and countdown calculation.
  - Pricing calculation and date range filtering.
  - Rotation strategies (round-robin, least-used, sticky).
- CLI binary packaging verification.

## Related Code Files
- [NEW] `tests/test_keyring.py`
- [NEW] `tests/test_quota.py`
- [NEW] `tests/test_usage.py`
- [NEW] `tests/test_rotation.py`
- [NEW] `tests/test_cli.py`

## Implementation Steps
1. Write unit tests for Keyring encoding/decoding (`go-keyring-base64`).
2. Write unit tests for Quota parsing with real bucket mock fixtures.
3. Write unit tests for Protobuf wire decoder and token aggregation.
4. Write unit tests for Rotation strategies and Cooldown expiration logic.
5. Run automated test suite via `pytest`.
6. Perform end-to-end verification of `betteragy account list`, `betteragy quota`, `betteragy usage`.

## Todo List
- [ ] Write Unit Tests for Core Services
- [ ] Test Quota Client against Mock & Live API
- [ ] Test SQLite Usage Scanner with Real Local DBs
- [ ] Verify Pre-commit Linting and Compilability
- [ ] Package CLI binary / entry point
