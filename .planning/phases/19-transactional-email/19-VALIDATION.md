---
phase: 19
slug: transactional-email
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-11
audited: 2026-03-12
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property               | Value                                                        |
| ---------------------- | ------------------------------------------------------------ |
| **Framework**          | pytest + pytest-django (existing)                            |
| **Config file**        | `apps/api/pyproject.toml` ([tool.pytest.ini_options])        |
| **Quick run command**  | `cd apps/api && python -m pytest tests/notifications/ -x -q` |
| **Full suite command** | `cd apps/api && python -m pytest --tb=short -q`              |
| **Estimated runtime**  | ~15 seconds                                                  |

---

## Sampling Rate

- **After every task commit:** Run `cd apps/api && python -m pytest tests/notifications/ -x -q`
- **After every plan wave:** Run `cd apps/api && python -m pytest --tb=short -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID  | Plan | Wave | Requirement  | Test Type   | Automated Command                                                                                                | File Exists | Status   |
| -------- | ---- | ---- | ------------ | ----------- | ---------------------------------------------------------------------------------------------------------------- | ----------- | -------- |
| 19-01-01 | 01   | 0    | EMAIL-01..05 | setup       | `ls tests/notifications/`                                                                                        | ✅          | ✅ green |
| 19-02-01 | 02   | 1    | EMAIL-01     | unit        | `pytest tests/notifications/test_utils.py::TestSendEmailQueuesTask::test_send_email_queues_task -x`              | ✅          | ✅ green |
| 19-02-02 | 02   | 1    | EMAIL-01     | unit        | `pytest tests/notifications/test_settings.py::TestEmailBackendSelection::test_email_backend_selection -x`        | ✅          | ✅ green |
| 19-02-03 | 02   | 1    | EMAIL-02     | unit        | `pytest tests/notifications/test_utils.py::TestSendEmailOnCommitRollback::test_send_email_on_commit_rollback -x` | ✅          | ✅ green |
| 19-03-01 | 03   | 2    | EMAIL-03     | unit        | `pytest tests/notifications/test_tasks.py::TestCssIsInlined::test_css_is_inlined -x`                             | ✅          | ✅ green |
| 19-03-02 | 03   | 2    | EMAIL-04     | unit        | `pytest tests/notifications/test_settings.py::TestNoApiKeyUsesConsole::test_no_api_key_uses_console -x`          | ✅          | ✅ green |
| 19-04-01 | 04   | 3    | EMAIL-05     | integration | `pytest tests/test_scaffolder_email_removal.py -x`                                                               | ✅          | ✅ green |

_Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky_

---

## Wave 0 Requirements

- [x] `apps/api/tests/notifications/__init__.py` — package init
- [x] `apps/api/tests/notifications/test_utils.py` — EMAIL-01, EMAIL-02 (3 tests)
- [x] `apps/api/tests/notifications/test_tasks.py` — EMAIL-03 (2 tests)
- [x] `apps/api/tests/notifications/test_settings.py` — EMAIL-01, EMAIL-04 (3 tests)
- [x] `apps/api/tests/test_scaffolder_email_removal.py` — EMAIL-05 (1 test)

---

## Manual-Only Verifications

| Behavior                                                      | Requirement | Why Manual                             | Test Instructions                                      |
| ------------------------------------------------------------- | ----------- | -------------------------------------- | ------------------------------------------------------ |
| HTML email renders without broken styles in real email client | EMAIL-03    | Requires actual email client rendering | Send to Mailtrap/Mailhog, inspect HTML in email client |
| Console backend logs email content visibly in local dev       | EMAIL-04    | Terminal output inspection             | Run dev server, trigger an email, check stdout         |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s (actual: 3.05s for 9 tests)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ✅ 2026-03-12 — 9/9 tests passing

---

## Validation Audit 2026-03-12

| Metric        | Count |
| ------------- | ----- |
| Gaps found    | 0     |
| Resolved      | 0     |
| Escalated     | 0     |
| Tests run     | 9     |
| Tests passing | 9     |
