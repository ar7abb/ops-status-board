import importlib.util
from pathlib import Path
import unittest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_project_state.py"
)
SPEC = importlib.util.spec_from_file_location("validate_project_state", SCRIPT_PATH)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


VALID_BLUEPRINT = """---
blueprint_version: "2.2.0"
project_state_schema: 2
last_revised_utc: "2026-08-04"
technical_scope: "frozen"
---

# Test Blueprint

## Milestone 1 — Workstation

### Tasks

1. **M01-T01 — Test task:** Sanitized task for validator tests.
"""


VALID_STATE = """---
state_schema: 2
blueprint_version: "2.2.0"
updated_at_utc: "2026-08-04T12:00:00Z"
current_release: "v0.1"
current_milestone: 1
milestone_status: "In progress"
active_task_id: "M01-T01"
active_task_status: "In Progress"
required_blueprint_sections: "1, 3, 9, Milestone 1"
estimated_sessions: 1
actual_sessions: 1
attempt_count: 1
highest_assistance_level: "L2"
confidence_before: 2
confidence_after: 0
active_branch: "codex/example"
last_verified_commit: "abc1234"
working_tree_at_update: "dirty"
last_state_verified_by: "learner-and-codex"
---

# Project State

## Resume Summary

Sanitized validator fixture with no connection to a real environment.

## Exact Next Action

Run `python3 -m unittest discover -s tests -v` and expect all tests to pass.

## Active Task Card

- Task ID: M01-T01
- Release: v0.1
- Milestone: 1 — Workstation
- Title: Test task
- Learning goal: Understand validation.
- Why this matters: Prevent malformed resume state.
- Prerequisite task IDs: none
- Estimated sessions: 1
- Actual sessions: 1
- Confidence before (1–5): 2
- Confidence after (1–5): 0 — in progress
- Attempt count: 1
- Highest assistance level: L2
- Learner’s first action: Explain the expected validator result.
- Codex assistance boundary: Use only sanitized fixtures.
- Implementation steps: Implement one focused validator.
- Verification: Run positive and negative tests.
- Required evidence: Sanitized test output.
- Risk: Accepting malformed state.
- Recovery/checkpoint: Revert the uncommitted fixture.
- Definition of Done: All required tests pass.
- Status: In Progress

## Current Milestone Checklist

- [ ] M01-T01 — Test task

## Last Verified Results

| Check | Result |
|---|---|
| Fixture | Sanitized |

## Environment State

- Test-only environment: none

## AWS and Cost State

- Account plan: not configured

## Decisions Since Last Milestone

- None.

## Known Problems or Blockers

- None.

## Uncommitted or Partial Work

- Sanitized fixture only.

## Evidence Added

- Unit-test result.

## Session Handoff

- Exact next action is recorded above.

## Milestone Ledger

| Milestone | Status |
|---|---|
| 1 | In progress |
"""


class ProjectStateValidatorTests(unittest.TestCase):
    def validate(self, state=VALID_STATE, blueprint=VALID_BLUEPRINT):
        return validator.validate_documents(state, blueprint)

    def messages(self, state=VALID_STATE, blueprint=VALID_BLUEPRINT):
        errors, warnings = self.validate(state, blueprint)
        return errors + warnings

    def test_valid_state_passes(self):
        errors, warnings = self.validate()
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_missing_required_key_fails(self):
        state = VALID_STATE.replace("attempt_count: 1\n", "", 1)
        messages = self.messages(state)
        self.assertTrue(any("attempt_count" in message for message in messages))

    def test_missing_required_section_fails(self):
        state = VALID_STATE.replace("## Evidence Added", "### Evidence Added", 1)
        messages = self.messages(state)
        self.assertTrue(any("Evidence Added" in message for message in messages))

    def test_invalid_status_fails(self):
        state = VALID_STATE.replace(
            'active_task_status: "In Progress"',
            'active_task_status: "Doing"',
            1,
        )
        messages = self.messages(state)
        self.assertTrue(any("active_task_status" in message for message in messages))

    def test_unknown_task_id_fails(self):
        state = VALID_STATE.replace("M01-T01", "M01-T99")
        messages = self.messages(state)
        self.assertTrue(any("active_task_id" in message for message in messages))

    def test_duplicate_task_id_fails(self):
        blueprint = VALID_BLUEPRINT + (
            "\n## Milestone 2 — Application\n\n### Tasks\n\n"
            "1. **M01-T01 — Duplicate:** Duplicate test task.\n"
        )
        messages = self.messages(blueprint=blueprint)
        self.assertTrue(any("duplicate task ID" in message for message in messages))

    def test_nonsequential_task_id_fails(self):
        blueprint = VALID_BLUEPRINT.replace("M01-T01", "M01-T02", 1)
        state = VALID_STATE.replace("M01-T01", "M01-T02")
        messages = self.messages(state, blueprint)
        self.assertTrue(any("non-sequential" in message for message in messages))

    def test_vague_next_action_fails(self):
        state = VALID_STATE.replace(
            "Run `python3 -m unittest discover -s tests -v` and expect all tests to pass.",
            "Continue the project.",
            1,
        )
        messages = self.messages(state)
        self.assertTrue(any("Exact Next Action" in message for message in messages))

    def test_multi_action_next_action_fails(self):
        state = VALID_STATE.replace(
            "Run `python3 -m unittest discover -s tests -v` and expect all tests to pass.",
            "Run the tests and edit the README; expect both actions to succeed.",
            1,
        )
        messages = self.messages(state)
        self.assertTrue(any("more than one action" in message for message in messages))

    def test_out_of_range_confidence_fails(self):
        state = VALID_STATE.replace("confidence_before: 2", "confidence_before: 6", 1)
        messages = self.messages(state)
        self.assertTrue(any("confidence_before" in message for message in messages))

    def test_done_requires_confidence_after(self):
        state = VALID_STATE.replace(
            'active_task_status: "In Progress"', 'active_task_status: "Done"', 1
        ).replace("- Status: In Progress", "- Status: Done", 1)
        messages = self.messages(state)
        self.assertTrue(any("confidence_after" in message for message in messages))

    def test_schema_mismatch_fails(self):
        state = VALID_STATE.replace("state_schema: 2", "state_schema: 3", 1)
        messages = self.messages(state)
        self.assertTrue(any("state_schema" in message for message in messages))

    def test_version_mismatch_warns_without_values(self):
        state = VALID_STATE.replace(
            'blueprint_version: "2.2.0"', 'blueprint_version: "9.9.9"', 1
        )
        errors, warnings = self.validate(state)
        rendered = "\n".join(errors + warnings)
        self.assertTrue(any("blueprint_version" in message for message in warnings))
        self.assertNotIn("9.9.9", rendered)
        self.assertNotIn("2.2.0", rendered)

    def test_multiple_in_progress_tasks_fail(self):
        state = VALID_STATE.replace(
            "- Status: In Progress",
            "- Status: In Progress\n- Status: In Progress",
            1,
        )
        messages = self.messages(state)
        self.assertTrue(any("more than one task" in message for message in messages))

    def test_secret_like_value_fails_without_printing_value(self):
        secret_value = "NeverPrintThisValue123"
        state = VALID_STATE.replace(
            "- Account plan: not configured",
            f"- Account plan: not configured\n- password: {secret_value}",
            1,
        )
        rendered = "\n".join(self.messages(state))
        self.assertIn("password", rendered)
        self.assertNotIn(secret_value, rendered)

    def test_task_release_mismatch_fails(self):
        state = VALID_STATE.replace("current_release: \"v0.1\"", "current_release: \"v0.2\"", 1)
        messages = self.messages(state)
        self.assertTrue(any("current_release" in message for message in messages))

    def test_working_tree_status_is_controlled(self):
        state = VALID_STATE.replace(
            'working_tree_at_update: "dirty"',
            'working_tree_at_update: "one untracked file"',
            1,
        )
        messages = self.messages(state)
        self.assertTrue(any("working_tree_at_update" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
