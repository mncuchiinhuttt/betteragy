"""Single-width ASCII tree formatter for Betteragy task plans and delegation."""

from typing import Any, Dict, List, Tuple


def check_dependencies(task: Dict[str, Any], all_tasks: List[Dict[str, Any]]) -> Tuple[bool, List[int]]:
    """Check whether all prerequisite tasks in depends_on are completed."""
    dep_str = str(task.get("depends_on", "")).strip()
    if not dep_str:
        return True, []

    # Parse comma/space separated dependency IDs
    dep_ids: List[int] = []
    for token in dep_str.replace(";", ",").replace(" ", ",").split(","):
        token = token.strip().lstrip("#")
        if token.isdigit():
            dep_ids.append(int(token))

    completed_ids = {t["id"] for t in all_tasks if t.get("status") == "completed"}
    unmet = [did for did in dep_ids if did not in completed_ids]
    return len(unmet) == 0, unmet


def format_tasks_ascii_tree(
    goal: str,
    tasks: List[Dict[str, Any]],
    project_name: str = "",
    use_color: bool = False,
) -> str:
    """Format tasks as a clean single-width ASCII tree checklist with delegation badges."""
    total, done = len(tasks), sum(1 for t in tasks if t.get("status") == "completed")
    proj_str = f" ({project_name})" if project_name else ""
    header_goal = goal if goal else "Active Tasks"

    G, Y, R, D = ("\033[1;32m", "\033[1;33m", "\033[1;31m", "\033[0;90m") if use_color else ("", "", "", "")
    C, W, M, RST = ("\033[1;36m", "\033[1;37m", "\033[1;35m", "\033[0m") if use_color else ("", "", "", "")

    lines = [f"{C}TODO{RST}", f"  {D}|--{RST} {W}{header_goal}{proj_str}{RST} · {C}{done}/{total}{RST}"]
    if not tasks:
        lines.append(f"  {D}|  '--{RST} {D}[ ] No tasks scheduled{RST}")
    else:
        for i, t in enumerate(tasks):
            is_last = (i == total - 1)
            branch = f"  {D}|  '--{RST}" if is_last else f"  {D}|  |--{RST}"
            st = t.get("status", "pending")
            m, s = (
                (f"{G}[x]{RST}", G) if st == "completed" else
                (f"{Y}[>]{RST}", Y) if st == "in_progress" else
                (f"{R}[!]{RST}", R) if st == "blocked" else
                (f"{D}[ ]{RST}", D)
            )

            # Suffix info: assignment & dependencies
            badges = []
            if t.get("assigned_to"):
                badges.append(f"{M}@{t['assigned_to']}{RST}")
            if t.get("depends_on"):
                badges.append(f"{D}needs #{t['depends_on']}{RST}")

            badge_str = f" ({' | '.join(badges)})" if badges else ""
            st_suffix = f" {Y}(in_progress){RST}" if st == "in_progress" else (f" {R}(blocked){RST}" if st == "blocked" else "")

            lines.append(f"{branch} {m} {s}#{t['id']} {t.get('title', '')}{RST}{badge_str}{st_suffix}")

            indent = "     " if is_last else f"  {D}|  {RST}"
            # Check dependency warnings
            deps_ok, unmet = check_dependencies(t, tasks)
            if not deps_ok and st in ("pending", "in_progress"):
                unmet_str = ", ".join(f"#{u}" for u in unmet)
                lines.append(f"{indent}  {R}[!] Blocked by pending: {unmet_str}{RST}")

            if t.get("evidence"):
                lines.append(f"{indent}  {D}Evidence: {t['evidence']}{RST}")

    lines.append(f"  {D}`-----{RST}")
    return "\n".join(lines)


def format_tasks_diff(
    goal: str,
    tasks: List[Dict[str, Any]],
    project_name: str = "",
) -> str:
    """Format tasks into a clean diff codeblock for 100% native markdown color rendering."""
    total, done = len(tasks), sum(1 for t in tasks if t.get("status") == "completed")
    proj = f" ({project_name})" if project_name else ""
    lines = [f"# TODO: {goal or 'Active Tasks'}{proj} [{done}/{total}]"]
    if not tasks:
        lines.append("  [ ] No tasks scheduled")
    else:
        for t in tasks:
            st = t.get("status", "pending")
            pfx = "+" if st == "completed" else ("!" if st == "in_progress" else ("-" if st == "blocked" else " "))
            m = "[x]" if st == "completed" else ("[>]" if st == "in_progress" else ("[!]" if st == "blocked" else "[ ]"))
            badges = []
            if t.get("assigned_to"):
                badges.append(f"@{t['assigned_to']}")
            if t.get("depends_on"):
                badges.append(f"needs #{t['depends_on']}")
            b_str = f" ({' | '.join(badges)})" if badges else ""
            st_sfx = f" ({st})" if st in ("in_progress", "blocked") else ""
            lines.append(f"{pfx} {m} #{t['id']} {t.get('title', '')}{b_str}{st_sfx}")
            deps_ok, unmet = check_dependencies(t, tasks)
            if not deps_ok and st in ("pending", "in_progress"):
                unmet_str = ", ".join(f"#{u}" for u in unmet)
                lines.append(f"  - [!] Blocked by pending: {unmet_str}")
            if t.get("evidence"):
                lines.append(f"    Evidence: {t['evidence']}")
    return "\n".join(lines)

