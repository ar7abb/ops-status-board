#!/usr/bin/env python3
"""Validate the private Ops Status Board state against its private blueprint.

This validator checks document structure and internal consistency only. It does
not prove that Git, Docker, virtual machines, AWS, or any other external system
matches the recorded state.
"""

from argparse import ArgumentParser
from pathlib import Path
import re
from sys import stderr


REQUIRED_STATE_FIELDS = (
    "state_schema",
    "blueprint_version",
    "updated_at_utc",
    "current_release",
    "current_milestone",
    "milestone_status",
    "active_task_id",
    "active_task_status",
    "required_blueprint_sections",
    "estimated_sessions",
    "actual_sessions",
    "attempt_count",
    "highest_assistance_level",
    "confidence_before",
    "confidence_after",
    "active_branch",
    "last_verified_commit",
    "working_tree_at_update",
    "last_state_verified_by",
)

REQUIRED_BLUEPRINT_FIELDS = (
    "blueprint_version",
    "project_state_schema",
    "last_revised_utc",
    "technical_scope",
)

REQUIRED_STATE_SECTIONS = (
    "Resume Summary",
    "Exact Next Action",
    "Active Task Card",
    "Current Milestone Checklist",
    "Last Verified Results",
    "Environment State",
    "AWS and Cost State",
    "Decisions Since Last Milestone",
    "Known Problems or Blockers",
    "Uncommitted or Partial Work",
    "Evidence Added",
    "Session Handoff",
    "Milestone Ledger",
)

REQUIRED_TASK_CARD_FIELDS = (
    "Task ID",
    "Release",
    "Milestone",
    "Title",
    "Learning goal",
    "Why this matters",
    "Prerequisite task IDs",
    "Estimated sessions",
    "Actual sessions",
    "Confidence before (1–5)",
    "Confidence after (1–5)",
    "Attempt count",
    "Highest assistance level",
    "Learner’s first action",
    "Codex assistance boundary",
    "Implementation steps",
    "Verification",
    "Required evidence",
    "Risk",
    "Recovery/checkpoint",
    "Definition of Done",
    "Status",
)

MILESTONE_STATUSES = {"Not started", "In progress", "Blocked", "Complete"}
TASK_STATUSES = {
    "Backlog",
    "Ready",
    "In Progress",
    "Verification",
    "Blocked",
    "Done",
    "Cancelled",
}
ASSISTANCE_LEVELS = {f"L{number}" for number in range(6)}
WORKING_TREE_STATUSES = {"clean", "dirty"}
RELEASES = {"v0.1", "v0.2", "v0.3", "v0.4", "v0.5", "v0.9", "v1.0"}

TASK_ID_PATTERN = re.compile(r"^M(?:0[0-9]|1[0-9])-T[0-9]{2}$")
UTC_TIMESTAMP_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
SAFE_FIELD_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
MILESTONE_HEADING_PATTERN = re.compile(r"^## Milestone ([0-9]+)\b")
CATALOG_TASK_PATTERN = re.compile(
    r"^(?P<ordinal>[0-9]+)\.\s+\*\*(?P<task_id>M[0-1][0-9]-T[0-9]{2})\s+—"
)
SECRET_LINE_PATTERN = re.compile(
    r"^\s*(?:[-*]\s*)?"
    r"(?P<label>password|passwd|secret|token|api[_ -]?key|private[_ -]?key|"
    r"access[_ -]?key|client[_ -]?secret|credential|aws[_ -]?account[_ -]?id|"
    r"account[_ -]?id)\s*[:=]\s*(?P<value>.*)$",
    re.IGNORECASE,
)

PLACEHOLDER_VALUES = {
    "",
    "none",
    "not set",
    "not configured",
    "redacted",
    "<redacted>",
    "placeholder",
    "n/a",
    "unknown",
    "private record only",
    "never stored",
}

GENERIC_NEXT_ACTIONS = {
    "continue",
    "continue the project",
    "keep going",
    "next task",
    "do the next task",
    "work on the project",
}

ACTION_VERBS = (
    "add",
    "build",
    "check",
    "commit",
    "configure",
    "copy",
    "create",
    "delete",
    "deploy",
    "edit",
    "inspect",
    "install",
    "merge",
    "open",
    "push",
    "remove",
    "review",
    "run",
    "test",
    "update",
    "verify",
)


def parse_args():
    parser = ArgumentParser(
        description="Validate a schema-2 project state against its blueprint."
    )
    parser.add_argument("state_path", type=Path)
    parser.add_argument("blueprint_path", type=Path)
    return parser.parse_args()


def read_text(path, label):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        print(f"ERROR: {label}: cannot read UTF-8 text", file=stderr)
        return None


def add_error(errors, field, message):
    errors.append(f"ERROR: {field}: {message}")


def add_warning(warnings, field, message):
    warnings.append(f"WARNING: {field}: {message}")


def display_field(raw_field):
    field = raw_field.strip()
    if SAFE_FIELD_PATTERN.fullmatch(field):
        return field
    return "metadata"


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_front_matter(text, label, errors):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        add_error(errors, label, "missing opening front-matter delimiter")
        return None

    metadata = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return metadata

        key, separator, value = line.partition(":")
        if not separator:
            add_error(errors, label, "contains a malformed metadata line")
            return None

        key = key.strip()
        safe_key = display_field(key)
        if safe_key == "metadata":
            add_error(errors, label, "contains an invalid metadata field name")
            return None
        if key in metadata:
            add_error(errors, safe_key, "duplicate metadata field")
            return None

        metadata[key] = unquote(value)

    add_error(errors, label, "missing closing front-matter delimiter")
    return None


def extract_section(text, section_name):
    pattern = re.compile(
        rf"^## {re.escape(section_name)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if match is None:
        return None
    return match.group("body").strip()


def validate_required_fields(metadata, required_fields, label, errors):
    valid = True
    for field in required_fields:
        if field not in metadata:
            add_error(errors, field, f"missing required {label} field")
            valid = False
    return valid


def parse_integer(metadata, field, errors, minimum=None, maximum=None):
    value = metadata.get(field)
    if value is None:
        return None
    try:
        number = int(value)
    except ValueError:
        add_error(errors, field, "must be an integer")
        return None

    if minimum is not None and number < minimum:
        add_error(errors, field, f"must be at least {minimum}")
        return None
    if maximum is not None and number > maximum:
        add_error(errors, field, f"must be at most {maximum}")
        return None
    return number


def release_for_milestone(milestone):
    if 0 <= milestone <= 2:
        return "v0.1"
    if 3 <= milestone <= 4:
        return "v0.2"
    if 5 <= milestone <= 8:
        return "v0.3"
    if 9 <= milestone <= 11:
        return "v0.4"
    if 12 <= milestone <= 13:
        return "v0.5"
    if milestone == 14:
        return "v0.9"
    if 15 <= milestone <= 16:
        return "v1.0"
    return None


def parse_blueprint_catalog(blueprint_text, errors):
    catalog = {}
    tasks_by_milestone = {}
    current_milestone = None

    for line in blueprint_text.splitlines():
        heading_match = MILESTONE_HEADING_PATTERN.match(line)
        if heading_match:
            current_milestone = int(heading_match.group(1))
            continue

        task_match = CATALOG_TASK_PATTERN.match(line)
        if task_match is None:
            continue

        task_id = task_match.group("task_id")
        ordinal = int(task_match.group("ordinal"))
        if current_milestone is None:
            add_error(errors, "blueprint task catalog", "task appears outside a milestone")
            continue

        if task_id in catalog:
            add_error(errors, "blueprint task catalog", f"duplicate task ID {task_id}")
            continue

        expected_index = len(tasks_by_milestone.get(current_milestone, [])) + 1
        expected_id = f"M{current_milestone:02d}-T{expected_index:02d}"
        if ordinal != expected_index or task_id != expected_id:
            add_error(
                errors,
                "blueprint task catalog",
                f"non-sequential task ID near {task_id}",
            )

        catalog[task_id] = current_milestone
        tasks_by_milestone.setdefault(current_milestone, []).append(task_id)

    if not catalog:
        add_error(errors, "blueprint task catalog", "no catalog task IDs found")
    return catalog


def parse_task_card(state_text, errors):
    section = extract_section(state_text, "Active Task Card")
    if section is None:
        return None

    card = {}
    for line in section.splitlines():
        if not line.startswith("- "):
            continue
        label, separator, value = line[2:].partition(":")
        if not separator:
            continue
        label = label.strip()
        if label in card:
            add_error(errors, label, "duplicate Active Task Card field")
            continue
        card[label] = value.strip()

    for field in REQUIRED_TASK_CARD_FIELDS:
        if field not in card or not card[field]:
            add_error(errors, field, "missing or blank Active Task Card field")
    return card


def validate_sections(state_text, errors):
    if re.search(r"^# Project State\s*$", state_text, re.MULTILINE) is None:
        add_error(errors, "Project State", "missing required level-one heading")

    for section_name in REQUIRED_STATE_SECTIONS:
        section = extract_section(state_text, section_name)
        if section is None:
            add_error(errors, section_name, "missing required section")
        elif not section:
            add_error(errors, section_name, "required section is blank")


def validate_metadata_values(state, blueprint, errors, warnings):
    if state.get("state_schema") != "2":
        add_error(errors, "state_schema", "must be 2")
    if blueprint.get("project_state_schema") != "2":
        add_error(errors, "project_state_schema", "must be 2")
    if state.get("blueprint_version") != blueprint.get("blueprint_version"):
        add_warning(
            warnings,
            "blueprint_version",
            "state and blueprint versions differ; stop and inspect migration history",
        )

    if state.get("milestone_status") not in MILESTONE_STATUSES:
        add_error(errors, "milestone_status", "contains an undocumented status")
    if state.get("active_task_status") not in TASK_STATUSES:
        add_error(errors, "active_task_status", "contains an undocumented status")
    if state.get("highest_assistance_level") not in ASSISTANCE_LEVELS:
        add_error(errors, "highest_assistance_level", "must be L0 through L5")
    if state.get("working_tree_at_update") not in WORKING_TREE_STATUSES:
        add_error(errors, "working_tree_at_update", "must be clean or dirty")
    if state.get("current_release") not in RELEASES:
        add_error(errors, "current_release", "contains an undocumented release")
    if blueprint.get("technical_scope") != "frozen":
        add_error(errors, "technical_scope", "must be frozen")

    if not UTC_TIMESTAMP_PATTERN.fullmatch(state.get("updated_at_utc", "")):
        add_error(errors, "updated_at_utc", "must use YYYY-MM-DDTHH:MM:SSZ")
    if not DATE_PATTERN.fullmatch(blueprint.get("last_revised_utc", "")):
        add_error(errors, "last_revised_utc", "must use YYYY-MM-DD")


def validate_numbers_and_confidence(state, errors):
    current_milestone = parse_integer(state, "current_milestone", errors, 0, 16)
    estimated_sessions = parse_integer(state, "estimated_sessions", errors, 1)
    parse_integer(state, "actual_sessions", errors, 0)
    parse_integer(state, "attempt_count", errors, 0)
    confidence_before = parse_integer(state, "confidence_before", errors, 0, 5)
    confidence_after = parse_integer(state, "confidence_after", errors, 0, 5)

    if estimated_sessions is not None and estimated_sessions != 1:
        add_error(errors, "estimated_sessions", "must equal 1 for the active task")

    active_status = state.get("active_task_status")
    if (
        confidence_before is not None
        and active_status in TASK_STATUSES - {"Backlog"}
        and confidence_before == 0
    ):
        add_error(
            errors,
            "confidence_before",
            "must be 1 through 5 after the task leaves Backlog",
        )
    if active_status == "Done" and confidence_after == 0:
        add_error(
            errors,
            "confidence_after",
            "must be 1 through 5 when the active task is Done",
        )
    return current_milestone


def validate_task_relationships(state, state_text, catalog, card, milestone, errors):
    active_task_id = state.get("active_task_id", "")
    if not TASK_ID_PATTERN.fullmatch(active_task_id):
        add_error(errors, "active_task_id", "must match M[0-1][0-9]-T[0-9][0-9]")
        return

    catalog_milestone = catalog.get(active_task_id)
    if catalog_milestone is None:
        add_error(errors, "active_task_id", "is not present in the blueprint task catalog")
        return

    if milestone is not None and catalog_milestone != milestone:
        add_error(errors, "active_task_id", "does not map to current_milestone")

    expected_release = release_for_milestone(catalog_milestone)
    if state.get("current_release") != expected_release:
        add_error(errors, "current_release", "does not match the active task milestone")

    required_sections = state.get("required_blueprint_sections", "")
    if f"Milestone {catalog_milestone}" not in required_sections:
        add_error(
            errors,
            "required_blueprint_sections",
            "does not include the active task milestone",
        )

    if card is not None:
        if card.get("Task ID") != active_task_id:
            add_error(errors, "Task ID", "does not match active_task_id")
        if card.get("Release") != state.get("current_release"):
            add_error(errors, "Release", "does not match current_release")
        card_milestone_match = re.match(r"^([0-9]+)\b", card.get("Milestone", ""))
        if card_milestone_match is None:
            add_error(errors, "Milestone", "must begin with the milestone number")
        elif int(card_milestone_match.group(1)) != catalog_milestone:
            add_error(errors, "Milestone", "does not match the active task ID")
        if card.get("Status") != state.get("active_task_status"):
            add_error(errors, "Status", "does not match active_task_status")
        if card.get("Estimated sessions") != state.get("estimated_sessions"):
            add_error(errors, "Estimated sessions", "does not match metadata")

    in_progress_count = len(
        re.findall(r"^- Status:\s*In Progress\s*$", state_text, re.MULTILINE)
    )
    if in_progress_count > 1:
        add_error(errors, "Status", "more than one task is marked In Progress")
    if state.get("active_task_status") == "In Progress" and in_progress_count != 1:
        add_error(errors, "Status", "active In Progress task card is missing")


def validate_exact_next_action(state_text, errors):
    action = extract_section(state_text, "Exact Next Action")
    if action is None:
        return

    normalized = " ".join(action.split())
    lowered = normalized.lower().strip(". ")
    if not normalized:
        add_error(errors, "Exact Next Action", "must not be blank")
        return
    if len(normalized) < 20 or lowered in GENERIC_NEXT_ACTIONS:
        add_error(errors, "Exact Next Action", "is too vague")

    action_word_pattern = "|".join(ACTION_VERBS)
    follow_on = re.compile(
        rf"\b(?:and|then|after that|followed by)\s+(?:{action_word_pattern})\b",
        re.IGNORECASE,
    )
    if follow_on.search(normalized) or ";" in normalized:
        add_error(errors, "Exact Next Action", "contains more than one action")

    if "expect" not in lowered and "expected" not in lowered:
        add_error(errors, "Exact Next Action", "must state the expected result")


def normalize_placeholder(value):
    return value.strip().strip('"\'`').lower()


def validate_secret_like_content(text, document_label, errors):
    for line in text.splitlines():
        match = SECRET_LINE_PATTERN.match(line)
        if match is None:
            continue
        label = re.sub(r"[ _-]+", "_", match.group("label").lower())
        value = normalize_placeholder(match.group("value"))
        if value not in PLACEHOLDER_VALUES:
            add_error(
                errors,
                label,
                f"{document_label} contains a suspected non-placeholder secret value",
            )


def validate_documents(state_text, blueprint_text):
    errors = []
    warnings = []

    state = parse_front_matter(state_text, "state file", errors)
    blueprint = parse_front_matter(blueprint_text, "blueprint file", errors)

    validate_sections(state_text, errors)
    validate_exact_next_action(state_text, errors)
    validate_secret_like_content(state_text, "state file", errors)
    validate_secret_like_content(blueprint_text, "blueprint file", errors)

    catalog = parse_blueprint_catalog(blueprint_text, errors)
    card = parse_task_card(state_text, errors)

    if state is None or blueprint is None:
        return errors, warnings

    state_complete = validate_required_fields(
        state, REQUIRED_STATE_FIELDS, "state", errors
    )
    blueprint_complete = validate_required_fields(
        blueprint, REQUIRED_BLUEPRINT_FIELDS, "blueprint", errors
    )

    if not state_complete or not blueprint_complete:
        return errors, warnings

    validate_metadata_values(state, blueprint, errors, warnings)
    milestone = validate_numbers_and_confidence(state, errors)
    validate_task_relationships(
        state,
        state_text,
        catalog,
        card,
        milestone,
        errors,
    )
    return errors, warnings


def main():
    args = parse_args()
    state_text = read_text(args.state_path, "state file")
    blueprint_text = read_text(args.blueprint_path, "blueprint file")
    if state_text is None or blueprint_text is None:
        return 1

    errors, warnings = validate_documents(state_text, blueprint_text)
    for diagnostic in errors + warnings:
        print(diagnostic, file=stderr)

    if errors or warnings:
        return 1

    print(
        "OK: state structure and internal blueprint consistency passed; "
        "external reality is not verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
