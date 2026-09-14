# Betteragy Code Standards & Guidelines

## General Principles
- **KISS** (Keep It Simple, Stupid): Prioritize clarity and direct implementations over complex abstractions.
- **YAGNI** (You Aren't Gonna Need It): Build only what is needed for the functionality specified.
- **DRY** (Don't Repeat Yourself): Consolidate shared utilities in `core` and `services`.

## File & Code Size Management
- **200-Line Limit**: Every single code file MUST remain under 200 lines.
- **Single Responsibility**: Split large files into focused submodules (e.g. subcommands in `commands/`, discrete services in `services/`).
- **Descriptive Naming**: Use clear, descriptive module names that state their exact domain and purpose.

## Security & Secrets
- **No Secrets in Repo**: Never commit tokens, credentials, or private configuration files.
- **Secure File Permissions**: Always write sensitive files (e.g. `~/.config/betteragy/accounts.json`) with `0o600` permissions and atomic replacement via temporary files.
- **Keyring Hygiene**: Inject only the minimal envelope required by `agy`.

## Testing Standards
- All core services (keyring, quota, protobuf decoding, pricing, rotation) must have unit tests.
- Run `pytest -v` before committing code changes.
- Ensure all tests pass without skipping or using mock cheats.
