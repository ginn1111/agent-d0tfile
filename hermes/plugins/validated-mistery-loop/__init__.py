"""validated-mistery-loop plugin."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import shlex

DEFAULT_VML_ROOT = Path("/Users/gin/dev/validated-mastery-loop")


@dataclass
class CapabilityRecord:
    name: str
    status: str
    evidence: str
    last_validated: str


@dataclass
class GoalRecord:
    slug: str
    path: Path
    goal_title: str
    capabilities: list[CapabilityRecord]
    kanban_text: str


def _ensure_root(vml_root: Path | str) -> Path:
    root = Path(vml_root)
    if not root.exists():
        raise FileNotFoundError(f"Missing VML root: {root}")
    return root


def _extract_first(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else default


def _extract_capability_blocks(text: str) -> list[str]:
    matches = list(re.finditer(r"^##\s+(.+)$", text, re.MULTILINE))
    blocks = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append(text[start:end].strip())
    return blocks


def _parse_capabilities(text: str) -> list[CapabilityRecord]:
    capabilities = []
    for block in _extract_capability_blocks(text):
        header = re.match(r"^##\s+(.+)$", block, re.MULTILINE)
        if not header:
            continue
        name = header.group(1).strip()
        if name == "Capability Map (VML)":
            continue
        capabilities.append(
            CapabilityRecord(
                name=name,
                status=_extract_first(r"^- \*\*Status:\*\*\s*(.+)$", block),
                evidence=_extract_first(r"^- \*\*Evidence:\*\*\s*(.*)$", block),
                last_validated=_extract_first(r"^- \*\*Last validated:\*\*\s*(.*)$", block),
            )
        )
    return capabilities


def _extract_section(text: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\n(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


def _parse_cards(section_text: str) -> list[dict]:
    lines = section_text.splitlines()
    cards: list[dict] = []
    current: dict | None = None
    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.startswith("- **"):
            if current:
                cards.append(current)
            title_match = re.match(r"- \*\*(.+?)\*\*\s+`([^`]+)`", line)
            title = title_match.group(1).strip() if title_match else line[2:].strip()
            current = {"title": title, "raw": [line], "acceptance": "", "evidence": "", "capability": _card_capability(title)}
        elif current and line.startswith("  - **Acceptance:**"):
            current["acceptance"] = line.split("**Acceptance:**", 1)[1].strip()
            current["raw"].append(line)
        elif current and line.startswith("  - **Evidence:**"):
            current["evidence"] = line.split("**Evidence:**", 1)[1].strip()
            current["raw"].append(line)
        elif current:
            current["raw"].append(line)
    if current:
        cards.append(current)
    return cards


def _card_capability(title: str) -> str:
    if "|" in title:
        return title.split("|", 1)[1].strip()
    return title.strip()


def _parse_goal(goal_dir: Path) -> GoalRecord:
    goal_text = (goal_dir / "goal.md").read_text(encoding="utf-8")
    capability_text = (goal_dir / "capability-map.md").read_text(encoding="utf-8")
    kanban_text = (goal_dir / "kanban.md").read_text(encoding="utf-8")
    title = _extract_first(r"^# Goal:\s*(.+)$", goal_text)
    return GoalRecord(
        slug=goal_dir.name,
        path=goal_dir,
        goal_title=title,
        capabilities=_parse_capabilities(capability_text),
        kanban_text=kanban_text,
    )


def discover_goals(vml_root: Path | str = DEFAULT_VML_ROOT) -> list[GoalRecord]:
    root = _ensure_root(vml_root)
    goals_dir = root / "goals"
    results = []
    for goal_dir in sorted(goals_dir.iterdir()):
        if not goal_dir.is_dir() or goal_dir.name.startswith("_"):
            continue
        required = [goal_dir / "goal.md", goal_dir / "capability-map.md", goal_dir / "kanban.md", goal_dir / "knowledge.md"]
        if all(path.exists() for path in required):
            results.append(_parse_goal(goal_dir))
    return results


def build_check_report(vml_root: Path | str = DEFAULT_VML_ROOT) -> dict:
    issues: list[str] = []
    for goal in discover_goals(vml_root):
        goal_text = (goal.path / "goal.md").read_text(encoding="utf-8")
        capability_text = (goal.path / "capability-map.md").read_text(encoding="utf-8")
        knowledge_text = (goal.path / "knowledge.md").read_text(encoding="utf-8")
        if "[[capability-map]]" not in goal_text:
            issues.append(f"{goal.slug}: missing [[capability-map]] in goal.md")
        if "[[goal]]" not in capability_text:
            issues.append(f"{goal.slug}: missing [[goal]] in capability-map.md")
        in_progress_cards = _parse_cards(_extract_section(goal.kanban_text, "In Progress"))
        if len(in_progress_cards) > 1:
            issues.append(f"{goal.slug}: multiple In Progress cards")
        done_cards = _parse_cards(_extract_section(goal.kanban_text, "Done"))
        for card in done_cards:
            if not card["evidence"]:
                issues.append(f"{goal.slug}: done card missing Evidence: {card['title']}")
        for capability in goal.capabilities:
            if capability.status == "Demonstrated" and not capability.evidence:
                issues.append(f"{goal.slug}: demonstrated capability missing evidence: {capability.name}")
            if capability.status == "Demonstrated" and f"[[{capability.name}]]" not in knowledge_text:
                issues.append(f"{goal.slug}: knowledge missing backlink for {capability.name}")
    return {"ok": not issues, "issues": issues}


def build_review_report(vml_root: Path | str = DEFAULT_VML_ROOT) -> dict:
    goals = discover_goals(vml_root)
    active_goal = None
    in_progress: list[dict] = []
    statuses: dict[str, list[str]] = {}
    for goal in goals:
        cards = _parse_cards(_extract_section(goal.kanban_text, "In Progress"))
        if cards and active_goal is None:
            active_goal = goal.slug
            in_progress = cards
        for capability in goal.capabilities:
            statuses.setdefault(capability.status, []).append(capability.name)
    return {
        "active_goal": active_goal,
        "in_progress": in_progress,
        "capability_statuses": statuses,
    }


def _replace_section(text: str, heading: str, new_body: str) -> str:
    pattern = rf"(^##\s+{re.escape(heading)}\n)(.*?)(?=^##\s+|\Z)"
    replacement = rf"\1{new_body}"
    return re.sub(pattern, replacement, text, count=1, flags=re.MULTILINE | re.DOTALL)


def _render_cards(cards: list[dict]) -> str:
    if not cards:
        return ""
    return "\n".join("\n".join(card["raw"]).rstrip() for card in cards).rstrip() + "\n"


def _find_capability(goal: GoalRecord, capability_name: str) -> CapabilityRecord:
    matches = [cap for cap in goal.capabilities if cap.name == capability_name]
    if len(matches) != 1:
        raise ValueError(f"Ambiguous or missing capability: {capability_name}")
    return matches[0]


def _find_goal_and_card(vml_root: Path | str, capability_name: str) -> tuple[GoalRecord, dict]:
    for goal in discover_goals(vml_root):
        all_cards = []
        for heading in ("Backlog", "Next", "In Progress", "Blocked", "Review", "Done"):
            all_cards.extend(_parse_cards(_extract_section(goal.kanban_text, heading)))
        for card in all_cards:
            if card["capability"] == capability_name:
                return goal, card
    raise ValueError(f"Capability card not found: {capability_name}")


def start_capability(vml_root: Path | str, capability_name: str) -> dict:
    goal, _ = _find_goal_and_card(vml_root, capability_name)
    _find_capability(goal, capability_name)
    kanban_path = goal.path / "kanban.md"
    text = kanban_path.read_text(encoding="utf-8")
    sections = {name: _parse_cards(_extract_section(text, name)) for name in ("Backlog", "Next", "In Progress", "Blocked", "Review", "Done")}
    selected = None
    for name, cards in sections.items():
        for index, card in enumerate(cards):
            if card["capability"] == capability_name:
                selected = card
                del cards[index]
                break
        if selected:
            break
    if selected is None:
        raise ValueError(f"Capability card not found: {capability_name}")
    ponytail = sections["In Progress"]
    if ponytail:
        raise ValueError("Another card already In Progress")
    sections["In Progress"].append(selected)
    for name, cards in sections.items():
        text = _replace_section(text, name, _render_cards(cards))
    kanban_path.write_text(text, encoding="utf-8")
    template = (goal.path / "sessions" / "_session-template.md").read_text(encoding="utf-8")
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    session_path = goal.path / "sessions" / f"{stamp}-{capability_name.lower().replace(' ', '-').replace('/', '-')}.md"
    session_text = template.replace("{{capability}}", capability_name).replace("{{date}}", datetime.now().strftime("%Y-%m-%d"))
    session_path.write_text(session_text, encoding="utf-8")
    return {"goal": goal.slug, "session_path": str(session_path)}


def _active_goal(vml_root: Path | str) -> GoalRecord:
    for goal in discover_goals(vml_root):
        if _parse_cards(_extract_section(goal.kanban_text, "In Progress")):
            return goal
    raise ValueError("No active goal")


def _split_acceptance(text: str) -> list[str]:
    if not text:
        return []
    pieces = [piece.strip() for piece in text.split(";") if piece.strip()]
    if len(pieces) <= 1 and ";" not in text:
        pieces = [piece.strip() for piece in re.split(r"(?<=\w)\s+(?=`|[A-Za-z0-9_-])", text) if piece.strip()]
    return pieces


def validate_active_goal(vml_root: Path | str, output_text: str, evidence_ref: str) -> dict:
    goal = _active_goal(vml_root)
    in_progress = _parse_cards(_extract_section(goal.kanban_text, "In Progress"))
    if len(in_progress) != 1:
        raise ValueError("Need exactly one In Progress card")
    card = in_progress[0]
    checks = []
    for criterion in _split_acceptance(card["acceptance"]):
        criterion_words = [word.lower() for word in re.findall(r"[A-Za-z0-9_-]+", criterion) if len(word) > 2]
        matched = sum(1 for word in criterion_words if word in output_text.lower())
        threshold = 1 if len(criterion_words) <= 3 else 2
        passed = matched >= threshold or criterion.lower() in output_text.lower()
        checks.append({"criterion": criterion, "passed": passed, "evidence": evidence_ref if passed else ""})
    if not all(item["passed"] for item in checks):
        return {"checks": checks, "updated": False}
    kanban_path = goal.path / "kanban.md"
    text = kanban_path.read_text(encoding="utf-8")
    review_cards = _parse_cards(_extract_section(text, "Review"))
    done_cards = _parse_cards(_extract_section(text, "Done"))
    in_progress_cards = _parse_cards(_extract_section(text, "In Progress"))
    finished = in_progress_cards.pop(0)
    finished["evidence"] = evidence_ref
    finished["raw"] = [line if not line.startswith("  - **Evidence:**") else f"  - **Evidence:** {evidence_ref}" for line in finished["raw"]]
    if not any(line.startswith("  - **Evidence:**") for line in finished["raw"]):
        finished["raw"].append(f"  - **Evidence:** {evidence_ref}")
    done_cards.append(finished)
    text = _replace_section(text, "In Progress", _render_cards(in_progress_cards))
    text = _replace_section(text, "Review", _render_cards(review_cards))
    text = _replace_section(text, "Done", _render_cards(done_cards))
    kanban_path.write_text(text, encoding="utf-8")

    capability_map_path = goal.path / "capability-map.md"
    capability_text = capability_map_path.read_text(encoding="utf-8")
    block_pattern = rf"(##\s+{re.escape(card['capability'])}\n.*?)(?=^##\s+|\Z)"
    block_match = re.search(block_pattern, capability_text, re.MULTILINE | re.DOTALL)
    if block_match:
        block = block_match.group(1)
        block = re.sub(r"^- \*\*Status:\*\*\s*.*$", "- **Status:** Demonstrated", block, flags=re.MULTILINE)
        block = re.sub(r"^- \*\*Evidence:\*\*\s*.*$", f"- **Evidence:** {evidence_ref}", block, flags=re.MULTILINE)
        block = re.sub(r"^- \*\*Last validated:\*\*\s*.*$", f"- **Last validated:** {datetime.now().strftime('%Y-%m-%d')}", block, flags=re.MULTILINE)
        capability_text = capability_text[:block_match.start(1)] + block + capability_text[block_match.end(1):]
        capability_map_path.write_text(capability_text, encoding="utf-8")

    knowledge_path = goal.path / "knowledge.md"
    with knowledge_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n- [[{card['capability']}]] evidence: {evidence_ref}\n")
    return {"checks": checks, "updated": True}


def build_stress_questions(capability_name: str, output_text: str) -> list[str]:
    return [
        f"Explain core idea behind {capability_name} from this output: {output_text}",
        f"Apply {capability_name} to slightly different requirement. What changes first?",
        f"What edge case or failure mode would break {capability_name} here?",
    ]


def build_follow_up_question(capability_name: str, answer_text: str) -> str:
    answer = answer_text.strip().lower()
    if len(answer.split()) < 5 or "not sure" in answer:
        return f"What does {capability_name} change in concrete terms? Give one exact mechanism."
    return f"What trade-off would make you avoid {capability_name}, and what alternative would you pick?"


def parse_vml_command(text: str) -> dict:
    parts = shlex.split(text)
    if len(parts) < 2 or parts[0] != "vml":
        return {"command": None, "argument": None}
    return {"command": parts[1], "argument": parts[2] if len(parts) > 2 else None}


def _format_check_report(report: dict) -> str:
    if report.get("ok"):
        return "VML check: OK"
    issues = "\n".join(f"- {item}" for item in report.get("issues", []))
    return f"VML check:\n{issues}"


def _format_review_report(report: dict) -> str:
    lines = [f"Active goal: {report.get('active_goal') or 'none'}"]
    for card in report.get("in_progress", []):
        lines.append(f"In Progress: {card.get('capability')}")
    for status, names in sorted(report.get("capability_statuses", {}).items()):
        lines.append(f"{status}: {', '.join(names)}")
    return "\n".join(lines)


def _format_validate_report(report: dict) -> str:
    lines = []
    for item in report.get("checks", []):
        state = "PASS" if item.get("passed") else "FAIL"
        lines.append(f"{state}: {item.get('criterion')}")
    if report.get("updated"):
        lines.append("Updated VML files.")
    return "\n".join(lines) or "No validation checks run."


def _command_check(raw_args: str) -> str:
    vml_root = Path(raw_args.strip()) if raw_args.strip() else DEFAULT_VML_ROOT
    return _format_check_report(build_check_report(vml_root))


def _command_review(raw_args: str) -> str:
    vml_root = Path(raw_args.strip()) if raw_args.strip() else DEFAULT_VML_ROOT
    return _format_review_report(build_review_report(vml_root))


def _command_start(raw_args: str) -> str:
    capability_name = raw_args.strip()
    if not capability_name:
        return "Usage: /vml-start <capability>"
    result = start_capability(DEFAULT_VML_ROOT, capability_name)
    return f"Started {capability_name}\nSession: {result['session_path']}"


def _command_validate(raw_args: str) -> str:
    parts = [part.strip() for part in raw_args.split("|")]
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return "Usage: /vml-validate <output> | <evidence>"
    report = validate_active_goal(DEFAULT_VML_ROOT, parts[0], parts[1])
    return _format_validate_report(report)


def _command_stress(raw_args: str) -> str:
    capability_name = raw_args.strip() or "active capability"
    questions = build_stress_questions(capability_name, "current output")
    follow_up = build_follow_up_question(capability_name, "not sure")
    lines = [f"Stress target: {capability_name}"]
    lines.extend(f"Q{i+1}: {q}" for i, q in enumerate(questions))
    lines.append(f"Follow-up: {follow_up}")
    return "\n".join(lines)


def _register_plugin_commands(ctx):
    ctx.register_command("vml-check", _command_check, "Run VML consistency checks")
    ctx.register_command("vml-review", _command_review, "Review active VML goal and capability statuses")
    ctx.register_command("vml-start", _command_start, "Start a capability and create its session note", args_hint="<capability>")
    ctx.register_command("vml-validate", _command_validate, "Validate active VML work against acceptance criteria", args_hint="<output> | <evidence>")
    ctx.register_command("vml-stress", _command_stress, "Stress-test understanding with follow-up questions", args_hint="[capability]")


def _noop(*_args, **_kwargs):
    return None


def _register_bundled_skills(ctx):
    skills_dir = Path(__file__).parent / "skills"
    if not skills_dir.exists():
        return
    for child in sorted(skills_dir.iterdir()):
        skill_md = child / "SKILL.md"
        if child.is_dir() and skill_md.exists():
            ctx.register_skill(child.name, skill_md)


def register(ctx):
    _register_bundled_skills(ctx)
    _register_plugin_commands(ctx)
    ctx.register_hook("pre_llm_call", _noop)
