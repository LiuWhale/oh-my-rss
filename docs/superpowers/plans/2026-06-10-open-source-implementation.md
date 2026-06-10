# Open Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package the FreshRSS arXiv Codex summarization workflow as a reusable open-source Python CLI.

**Architecture:** The project is split into focused modules for FreshRSS data access, arXiv de-duplication, PDF extraction, prompt generation, Codex invocation, static rendering, publishing, and CLI orchestration. The CLI reads YAML config and keeps runtime state outside source control.

**Tech Stack:** Python 3.11, SQLite, PyYAML, Poppler `pdftotext`, Codex CLI, pytest.

---

- [x] Create failing tests for core behavior.
- [x] Implement core library modules.
- [x] Add CLI and config loading.
- [x] Add Docker, examples, and deployment docs.
- [x] Run verification.
