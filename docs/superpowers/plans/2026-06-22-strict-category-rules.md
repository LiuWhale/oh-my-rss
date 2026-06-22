# Strict Category Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make paper category labels precision-first so broad keywords and stale generated labels do not push papers into unrelated feeds.

**Architecture:** Keep the existing lightweight rule-based classifier, but route broad categories through explicit matcher functions with required context pairs. Production uses the same behavior in the NAS monolithic script, followed by a backed-up state reclassification and feed republish.

**Tech Stack:** Python 3.11+, pytest, ruff, setuptools build, NAS Python script on `10.147.18.177`.

---

### Task 1: Repository Classifier Tests

**Files:**
- Modify: `tests/test_domains.py`

- [ ] **Step 1: Add failing negative and positive examples**

Add tests showing that medical segmentation is vision-only, ordinary benchmark/evaluation text is not safety, ordinary LLM reasoning is not embodied AI, generic trajectory prediction is not robot policy/control, and true VLA, CBF, dataset, and robot policy papers still classify correctly.

- [ ] **Step 2: Run focused tests**

Run: `.venv/bin/pytest tests/test_domains.py -q`

Expected before implementation: at least one test fails due overly broad category matching.

### Task 2: Repository Classifier Implementation

**Files:**
- Modify: `src/oh_my_rss/domains.py`

- [ ] **Step 1: Add category-specific matcher functions**

Implement explicit matchers for robot learning, safety/control, benchmark/dataset, embodied/foundation, navigation/planning, and VLA.

- [ ] **Step 2: Keep broad feed labels as fallback only**

Ensure `feed_names` and generated category names do not participate in semantic matching.

- [ ] **Step 3: Run focused and full verification**

Run:

```bash
.venv/bin/pytest tests/test_domains.py -q
.venv/bin/ruff check .
.venv/bin/pytest -q
```

Expected: all commands pass.

### Task 3: Version, Release, and Production Sync

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/oh_my_rss/__init__.py`
- Modify: `CHANGELOG.md`
- Modify on NAS: `/var/services/homes/liuwhale/bin/arxiv_codex_summary.py`

- [ ] **Step 1: Bump package to the next patch version**

Update package metadata and changelog.

- [ ] **Step 2: Build and publish**

Run:

```bash
.venv/bin/python -m build
git commit -m "fix: tighten category classification"
git tag v0.1.8
git push origin main
git push origin v0.1.8
```

- [ ] **Step 3: Sync production classifier**

Back up the NAS script, copy the updated classifier behavior into production, compile it, reclassify `state.json`, republish category feeds, and verify public RSS outputs.
