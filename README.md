# grc-control-crosswalk
# GRC Control Crosswalk Tool

> Open-source CLI and web tool mapping 200+ security and AI governance controls across five major frameworks. Reduces manual control mapping from hours to seconds.

[![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-orange)](https://anthropic.com/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## The Problem

GRC teams routinely spend hours — sometimes days — manually mapping security controls across multiple frameworks. A single ISO 27001 control might map to NIST CSF, NIST AI RMF, ISO/IEC 42001, and the EU AI Act, but most teams maintain these mappings in fragile spreadsheets that go stale fast.

This tool solves that.

## What It Does

Takes a control from any of five frameworks and instantly returns the equivalent or related controls across the others.

## Frameworks Covered

| Framework | Version | Status | Controls Loaded |
|-----------|---------|--------|----------------|
| NIST CSF | 2.0 | Complete | 106 |
| ISO/IEC 27001 | 2022 | Complete | 93 |
| ISO/IEC 42001 | 2023 | Planned | — |
| NIST AI RMF | 1.0 | Planned | — |
| EU AI Act | 2024 | Planned | — |
## Who This Is For

- GRC analysts conducting cross-framework gap assessments
- TPRM teams evaluating vendors against multiple standards
- AI governance specialists aligning ISO 42001 with NIST AI RMF
- Compliance leads building unified control libraries

## Roadmap

- [ ] Complete control library across all 5 frameworks
- [ ] CLI lookup and reverse search
- [ ] Web interface with live demo
- [ ] MCP server integration for Claude Desktop
- [ ] Companion AI Vendor Risk Assessment Agent

## About

Built by Breck Agyekum, GRC and AI Governance Analyst based in Ottawa, ON. This project demonstrates the intersection of GRC framework expertise and modern AI tooling.

## License

MIT License — free to use, modify, and distribute.
