---
description: Run the financial engine's tests, find gaps, and add tests for them.
argument-hint: "[optional: module or path to focus on]"
allowed-tools: Read, Grep, Glob, Edit, Write, Bash, Agent
---

Test the financial engine. Focus: $ARGUMENTS (all modules if empty).

Use the `qa-engineer` agent and the `testing` skill.

1. Find and run the existing test suite. Record pass, fail, and skip counts.
2. Map the focus area's calculations to their tests. List untested formulas, thresholds, effective dates, and edge cases.
3. Add tests for the top gaps, with expected values from independent sources cited in each test.
4. Run the suite again.

Report: baseline vs. new counts, tests added, and every failure with input, expected, actual, and likely cause. Do not change calculation code to make tests pass.
