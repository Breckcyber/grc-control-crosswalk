
> # GRC Control Crosswalk Tool

> Open-source CLI and web tool mapping security and AI governance controls across five major frameworks: NIST CSF 2.0, ISO/IEC 27001:2022, ISO/IEC 42001:2023, NIST AI RMF 1.0, and the EU AI Act. Designed to reduce manual cross-framework mapping from hours to seconds.

[![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-orange)](https://anthropic.com/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## The Problem

GRC teams routinely spend hours — sometimes days — manually mapping security controls across multiple frameworks. A single ISO 27001 control might map to NIST CSF, NIST AI RMF, ISO/IEC 42001, and the EU AI Act, but most teams maintain these mappings in fragile spreadsheets that go stale fast.

This tool solves that.

## What It Does

Takes a control from any of five frameworks and instantly returns the equivalent or related controls across the others.

## Frameworks Covered

| Framework | Version | Status | Items |
|-----------|---------|--------|-------|
| NIST CSF | 2.0 | Complete | 106 subcategories |
| ISO/IEC 27001 | 2022 | Complete | 93 Annex A controls |
| NIST AI RMF | 1.0 | In progress | — |
| ISO/IEC 42001 | 2023 | In progress | — |
| EU AI Act | 2024 | In progress | — |

## Who This Is For

- GRC analysts conducting cross-framework gap assessments
- TPRM teams evaluating vendors against multiple standards
- AI governance specialists aligning ISO 42001 with NIST AI RMF
- Compliance leads building unified control libraries

## Roadmap

- [x] NIST CSF 2.0
- [x] ISO/IEC 27001:2022
- [ ] NIST AI RMF 1.0
- [ ] ISO/IEC 42001:2023
- [ ] EU AI Act key articles
- [ ] Cross-framework mappings file
- [ ] CLI lookup tool
- [ ] Public web interface

## About

Built by Breck Agyekum, GRC and AI Governance Analyst based in Lethbridge, AB. This project demonstrates the intersection of GRC framework expertise and modern AI-augmented tooling.

## License

MIT License — free to use, modify, and distribute.