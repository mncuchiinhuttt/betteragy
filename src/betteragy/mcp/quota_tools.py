"""Quota and Account intelligence tools for Betteragy MCP engine."""

from typing import Any, Dict, List, Optional

from betteragy.services.account_service import AccountService
from betteragy.services.quota_aggregator import QuotaAggregator
from betteragy.services.quota_service import QuotaService

QUOTA_TOOL_DEFINITIONS = [
    {
        "name": "quota_status",
        "description": "Inspect live AI model quota percentages, tier, and reset countdowns for current or specified account.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Optional account email. Defaults to active account."},
                "color": {"type": "boolean", "description": "Enable colored ANSI output."},
            },
        },
    },
    {
        "name": "account_list",
        "description": "List all configured Google accounts in Betteragy with their active status and tiers.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "account_switch",
        "description": "Switch the active Antigravity account to rotate quota and prevent 429 rate limits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Target email or 1-based index from account_list."},
            },
            "required": ["identifier"],
        },
    },
]


def format_quota_report(quota: Any, use_color: bool = False) -> str:
    """Format AccountQuota object into single-width ASCII report."""
    G, Y, R, D = ("\033[1;32m", "\033[1;33m", "\033[1;31m", "\033[0;90m") if use_color else ("", "", "", "")
    C, W, RST = ("\033[1;36m", "\033[1;37m", "\033[0m") if use_color else ("", "", "")

    tier = quota.tier_name or quota.tier or "Standard"
    lines = [
        f"{C}=== AI Model Quota: {W}{quota.email}{C} (Tier: {W}{tier}{C}) ==={RST}",
    ]

    if quota.is_forbidden:
        lines.append(f"  {R}[!] Account is forbidden (403). Re-authentication required.{RST}")
        return "\n".join(lines)
    if quota.is_error:
        lines.append(f"  {R}[!] Failed to retrieve quota: {quota.error_message}{RST}")
        return "\n".join(lines)

    if not quota.buckets:
        lines.append(f"  {D}[ ] No active model quota buckets found.{RST}")
        return "\n".join(lines)

    low_quota_models = []
    for b in quota.buckets:
        pct = int(b.percentage)
        pct_color = G if pct >= 50 else (Y if pct >= 20 else R)
        tag = f"{G}[ok]{RST}" if pct >= 50 else (f"{Y}[~]{RST}" if pct >= 20 else f"{R}[!]{RST}")
        reset_info = f"{D}(resets {b.reset_countdown}){RST}" if b.reset_countdown else ""
        mname = getattr(b, "display_name", "") or getattr(b, "model_id", "Unknown")
        lines.append(f"  {tag} {W}{mname:<30}{RST} {pct_color}{pct:>3}%{RST} {reset_info}")
        if pct < 20:
            low_quota_models.append(mname)

    if low_quota_models:
        lines.append(f"\n  {R}[!] Low Quota Advisory:{RST} Models ({', '.join(low_quota_models)}) < 20%.")
        lines.append(f"      Use 'account_switch' to rotate to another account with fresh quota.")
    else:
        lines.append(f"\n  {G}[ok] All model quotas healthy.{RST}")

    return "\n".join(lines)


def handle_quota_status(args: Dict[str, Any]) -> Dict[str, Any]:
    acc_svc = AccountService()
    email = args.get("email")
    if not email:
        active = acc_svc.get_active_account()
        if not active:
            return {"content": [{"type": "text", "text": "No accounts configured in Betteragy."}]}
        email = active.email

    aggregator = QuotaAggregator(acc_svc, QuotaService())
    quota = aggregator.fetch_single_account(email)
    use_color = bool(args.get("color", False))
    return {"content": [{"type": "text", "text": format_quota_report(quota, use_color=use_color)}]}


def handle_account_list(args: Dict[str, Any]) -> Dict[str, Any]:
    acc_svc = AccountService()
    accounts = acc_svc.get_accounts()
    active = acc_svc.get_active_account()
    active_email = active.email.lower() if active else ""

    lines = ["=== Betteragy Accounts Pool ==="]
    if not accounts:
        lines.append("No accounts found. Use 'betteragy account add' to link an account.")
    else:
        for idx, acc in enumerate(accounts, start=1):
            is_active = acc.email.lower() == active_email
            marker = "[*] ACTIVE" if is_active else "[ ]       "
            tier = acc.tier_name or acc.tier or "Standard"
            lines.append(f"  {marker} #{idx:<2} {acc.email:<32} (Tier: {tier})")
    lines.append("\nTip: Call 'account_switch' with index or email to switch active account.")
    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


def handle_account_switch(args: Dict[str, Any]) -> Dict[str, Any]:
    ident = args.get("identifier", "").strip()
    if not ident:
        return {"content": [{"type": "text", "text": "Error: 'identifier' parameter is required."}], "isError": True}

    acc_svc = AccountService()
    ok, msg = acc_svc.switch_account(ident)
    if ok:
        active = acc_svc.get_active_account()
        active_email = active.email if active else ident
        text = f"[ok] Successfully switched active account to: {active_email}\n{msg}"
        return {"content": [{"type": "text", "text": text}]}
    return {"content": [{"type": "text", "text": f"[!] Switch failed: {msg}"}], "isError": True}
