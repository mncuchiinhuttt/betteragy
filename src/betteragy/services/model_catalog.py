"""Model catalog: humanizing model slugs and resolving display labels."""

from ..core.constants import MODEL_DISPLAY_NAMES

VARIANT_QUALIFIERS = {"high", "low", "medium", "fast", "thinking", "lite", "experimental", "preview"}
ACRONYMS = {"gpt", "oss", "llm", "tts", "api"}


def humanize_model_id(slug: str) -> str:
    """Transform raw model slug into human-readable label with proper casing and variant tags."""
    if not slug:
        return "Unknown"

    clean_id = slug.split("/")[-1]
    if clean_id in MODEL_DISPLAY_NAMES:
        return MODEL_DISPLAY_NAMES[clean_id]
    if slug in MODEL_DISPLAY_NAMES:
        return MODEL_DISPLAY_NAMES[slug]

    parts = clean_id.split("-")
    variant = ""
    if len(parts) > 1 and parts[-1].lower() in VARIANT_QUALIFIERS:
        variant = parts.pop()

    capitalized: list[str] = []
    for part in parts:
        lower = part.lower()
        if lower in ACRONYMS:
            capitalized.append(lower.upper())
        else:
            capitalized.append(part.capitalize())

    base = " ".join(capitalized)
    if variant:
        return f"{base} ({variant.capitalize()})"
    return base
