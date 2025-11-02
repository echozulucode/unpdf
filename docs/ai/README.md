# AI-Generated Plans and Documents

This directory contains AI-generated planning documents, implementation strategies, and other AI-assisted artifacts for the unpdf project.

---

## Document Naming Convention

All planning documents follow this naming pattern:
```
plan-NNN-description.md
```

Where:
- `NNN` is a zero-padded sequence number (001, 002, 003, etc.)
- `description` is a kebab-case description of the plan

**Examples:**
- `plan-001-implementation.md` - Initial 11-week implementation plan
- `plan-002-testing-strategy.md` - Comprehensive testing strategy (future)
- `plan-003-plugin-system.md` - Plugin architecture design (future)

---

## Current Plans

### Active Plans

| Plan | Description | Status | Created |
|------|-------------|--------|---------|
| [plan-001-implementation.md](plan-001-implementation.md) | 11-week phased implementation roadmap | 📋 Active | 2025-11-02 |

### Archived Plans

None yet.

---

## Plan Template

When creating a new plan, use this structure:

```markdown
# [Plan Title]

**Plan ID:** plan-NNN-description  
**Created:** YYYY-MM-DD  
**Status:** Draft | Active | Completed | Superseded  
**Author:** AI Agent / Human Name

---

## Overview

Brief summary of what this plan covers.

## Goals

- Goal 1
- Goal 2
- Goal 3

## Phases/Sections

### Phase 1: [Name]
...

### Phase 2: [Name]
...

## Success Criteria

- Criteria 1
- Criteria 2

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1 | Week 1 | Description |

---

**Last Updated:** YYYY-MM-DD
```

---

## Other Documents

### Supporting Documents

| Document | Description |
|----------|-------------|
| [PROJECT_SETUP_COMPLETE.md](PROJECT_SETUP_COMPLETE.md) | Project initialization summary |
| [Plan for a PDF-to-Markdown Converter.pdf](Plan%20for%20a%20PDF-to-Markdown%20Converter.pdf) | Original planning document (source) |

---

## Guidelines

### When to Create a New Plan

Create a new plan when:
- Starting a major feature (v2.0 features, plugin system, etc.)
- Pivoting strategy or architecture
- Planning a significant refactor
- Documenting a complex investigation

### When to Update Existing Plan

Update an existing plan when:
- Adjusting timelines
- Adding/removing phases
- Clarifying requirements
- Documenting progress

### Versioning Plans

If a plan needs major revision:
1. Mark original as "Superseded"
2. Create new plan with next sequence number
3. Reference previous plan in new document

**Example:**
- `plan-001-implementation.md` (original)
- `plan-005-implementation-revised.md` (replaces plan-001)

---

## Usage with AI Agents

When instructing AI agents:

**Reference plans explicitly:**
```
"Implement Phase 2 from plan-001-implementation.md"
"Create a new testing plan as plan-002-testing-strategy.md"
```

**Always use relative paths:**
```
See docs/ai/plan-001-implementation.md
```

**Keep plans updated:**
- Update status when starting/completing phases
- Add notes for deviations from plan
- Document lessons learned

---

## Archive Policy

Plans are archived when:
- Completed successfully
- Superseded by newer plan
- Cancelled or abandoned

Archived plans remain in this directory for historical reference with status updated to `Archived` or `Superseded`.

---

**Last Updated:** 2025-11-02
