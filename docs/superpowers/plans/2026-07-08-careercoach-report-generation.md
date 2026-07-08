# Career Coach Report Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a complete Word-format completion report for the current Career Coach project using real repository evidence and clear figure placeholders.

**Architecture:** Build the report from local project artifacts, synthesize a chaptered long-form manuscript, and generate the `.docx` deliverable with a Python-based document writer. Keep the report content separate from generation logic so later edits remain easy.

**Tech Stack:** Markdown source notes, Python, `python-docx`

---

### Task 1: Freeze report scope and chapter structure

**Files:**
- Create: `docs/superpowers/specs/2026-07-08-careercoach-report-design.md`
- Create: `docs/superpowers/plans/2026-07-08-careercoach-report-generation.md`

- [ ] **Step 1: Save the approved report scope**

Write a short spec that locks the report goal, structure, figure placeholders, and output filename.

- [ ] **Step 2: Save the execution plan**

Write a concise plan that covers evidence gathering, manuscript drafting, document generation, and verification.

### Task 2: Gather implementation evidence from the repository

**Files:**
- Read: `README.md`
- Read: `设计文档.md`
- Read: `功能逻辑详情.md`
- Read: `数据库设计.md`
- Read: `接口文档.md`
- Read: `main.py`
- Read: `api/*.py`
- Read: `services/*.py`
- Read: `ai/workflow/pipeline.py`
- Read: `ai/agents/career_coach.py`
- Read: `ai/vectorstore/jd_store.py`
- Read: `frontend/src/views/*.vue`

- [ ] **Step 1: Extract system facts**

Capture the implemented modules, architecture, storage choices, AI pipeline, page flows, and operational constraints from the codebase.

- [ ] **Step 2: Reconcile design docs with actual code**

Prefer implemented behavior over aspirational wording when the design document is broader than the current code.

### Task 3: Draft the report manuscript in a reusable source file

**Files:**
- Create: `report_source.md`

- [ ] **Step 1: Write the full chaptered manuscript**

Draft a long-form report in Chinese with complete sections, substantial technical detail, and explicit image placeholders like `[图 4-1：数据库 ER 图（待补）]`.

- [ ] **Step 2: Ensure the report reflects the current project**

Make sure references to FastAPI, Vue 3, MySQL, Redis Stack, OSS, LangGraph, LangSmith, SSE, and the quiz subsystem align with the repository.

### Task 4: Create the document generator

**Files:**
- Create: `generate_report_docx.py`
- Read: `report_source.md`

- [ ] **Step 1: Implement a Python generator**

Create a script that reads the Markdown source, maps headings and paragraphs into a Word document, and saves `CareerCoach项目结项报告-完整版.docx`.

- [ ] **Step 2: Add basic formatting**

Apply a readable title page, heading hierarchy, paragraph spacing, and page breaks between major sections where useful.

### Task 5: Generate and verify the deliverable

**Files:**
- Create: `CareerCoach项目结项报告-完整版.docx`

- [ ] **Step 1: Run the generator**

Execute the Python script in the workspace and produce the final `.docx`.

- [ ] **Step 2: Verify the output exists and is readable**

Confirm the file is present and inspect key paragraph headings from the generated document to make sure the structure rendered correctly.
