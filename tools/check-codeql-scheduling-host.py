#!/usr/bin/env python3
"""Static security scan configuration invariants; no scanner impersonation."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
workflow = (root/'.github/workflows/codeql-advanced.yml').read_text()
config = (root/'.github/codeql/codeql-config.yml').read_text()
assert "workflow_dispatch:" in workflow and "schedule:" in workflow
assert "github.event_name == 'schedule' && 'scheduled-main' || github.ref" in workflow
assert "cancel-in-progress: ${{ github.event_name != 'schedule' }}" in workflow
assert "security-events: write" in workflow and "contents: read" in workflow
assert "config-file: ./.github/codeql/codeql-config.yml" in workflow
for lang in ("actions","python","c-cpp"):
    assert f"- language: {lang}" in workflow
for required in ("  - .github","  - headless","  - src","  - tools","  - vendor/encore-active"):
    assert required in config.split("paths-ignore:",1)[0],required
assert "  - 'vendor/encore-active/**'" not in config.split("paths-ignore:",1)[-1]
assert workflow.count("'docs/EDEN_OPTIMIZATION_COVERAGE_2026-10-20.json'")==1
assert workflow.count("'docs/EDEN_NATIVE_STARTUP_DIAGNOSTIC_REVIEW_2026-10-21.md'")==1
print("CODEQL_SCHEDULED_ANALYSIS_ISOLATED_AND_ACTIVE_SOURCE_SCANNED")
