# Claude.md — GRC Control Crosswalk Project Context

## Project Goal

Build an open-source CLI tool and web interface that maps security and AI governance controls across five major frameworks: NIST CSF 2.0, ISO 27001:2022, ISO/IEC 42001, NIST AI RMF 1.0, and the EU AI Act.

## Target User

GRC analysts, TPRM specialists, AI governance leads, and compliance professionals who currently maintain framework crosswalks in spreadsheets.

## Project Owner

Breck Agyekum — GRC and AI Governance Analyst, Ottawa, ON. ISO 27001 Lead Auditor, with hands-on experience in:
- Fensis Limited ISO 27001 ISMS implementation
- Oscorp NIST CSF 2.0 gap analysis
- Microsoft Copilot NIST AI RMF vendor assessment
- ATD Project — assessed 60+ AI logistics vendors

## Folder Structure

- /data — YAML files, one per framework, plus mappings.yaml linking them
- /src — Python CLI code
- /web — HTML/JS interface
- /docs — Screenshots, methodology docs, and additional documentation

## Coding Conventions

- Python 3.10+ for CLI
- Use PyYAML for YAML parsing
- Vanilla HTML/CSS/JS for web interface (no frameworks)
- Click library for CLI structure
- All control IDs match official framework documentation exactly

## Build Order

1. Populate framework YAML files with seed data (Days 1–3)
2. Build mappings.yaml (Day 3)
3. Build core CLI lookup function (Day 4)
4. Add reverse search and framework filtering (Day 4)
5. Build web interface (Day 5)
6. Deploy to Vercel/GitHub Pages (Day 5)
7. Polish, document, launch (Day 6)

## Style Guide

- Code should be readable by GRC professionals, not just engineers
- README and docs should explain why a mapping exists, not just that it exists
- Confidence indicators (Direct / Related / Partial) help users judge mapping strength
- Avoid academic jargon — write for working practitioners