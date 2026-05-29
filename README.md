
> # GRC Control Crosswalk Tool

> Working open-source CLI that maps 340+ security and AI governance controls across five major frameworks — NIST CSF 2.0, ISO/IEC 27001:2022, ISO/IEC 42001:2023, NIST AI RMF 1.0, and the EU AI Act. One control in, cross-framework mappings out in seconds. Built with Anthropic Claude Code.

[![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-orange)](https://anthropic.com/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## The Problem

GRC teams routinely spend hours — sometimes days — manually mapping security controls across multiple frameworks. A single ISO 27001 control might map to NIST CSF, NIST AI RMF, ISO/IEC 42001, and the EU AI Act, but most teams maintain these mappings in fragile spreadsheets that go stale fast.

This tool solves that.

## What It Does

Takes a control from any of five frameworks and instantly returns the equivalent or related controls across the others.

## Usage

Install Python 3.10+ and the one required dependency:

```bash
pip install pyyaml
```

Optional, for colored terminal output:

```bash
pip install colorama
```

### Three query modes

**Mode A — Look up a control and see all cross-framework mappings:**

```bash
python src/crosswalk.py "A.5.1"
```

Returns the control details plus all mappings out to other frameworks AND mappings in from other frameworks.

**Mode B — Keyword search across all frameworks:**

```bash
python src/crosswalk.py --search "policy"
```

Returns top matches across all five frameworks.

**Mode C — List all controls in one framework:**

```bash
python src/crosswalk.py --framework "NIST CSF 2.0"
```

Lists every control in the specified framework with its ID and name.

**Help:**

```bash
python src/crosswalk.py --help
```

### Example output

```
Control
=======
  Framework:   ISO/IEC 27001:2022
  Control ID:  A.5.1
  Name:        Policies for information security
  Description: Information security policy and topic-specific policies
               shall be defined, approved by management...

Cross-framework mappings
========================
  Maps OUT to (this control as source):
    - NIST CSF 2.0          GV.PO-01     [Direct]
        Both require formal information security policy...
    - ISO/IEC 42001:2023    A.2.2        [Related]
        ISO 42001 A.2.2 extends policy concept to AI...
    - NIST AI RMF 1.0       GOVERN 1.1   [Related]
        Both address governance policy at organizational level...

  Mapped FROM (this control as target):
    - NIST CSF 2.0          GV.OC-01     [Partial]
        Organizational context understanding supports policy...
```

## Frameworks Covered

| Framework | Version | Status | Items |
|-----------|---------|--------|-------|
| NIST CSF | 2.0 | Complete | 106 subcategories |
| ISO/IEC 27001 | 2022 | Complete | 93 Annex A controls |
| NIST AI RMF | 1.0 | Complete | ~72 subcategories |
| ISO/IEC 42001 | 2023 | Complete | Clauses + 38 Annex A controls |
| EU AI Act | 2024 | Complete | ~30 key governance articles |

**Total: 340+ controls and articles across 5 frameworks.**

## Who This Is For

- GRC analysts conducting cross-framework gap assessments
- TPRM teams evaluating vendors against multiple standards
- AI governance specialists aligning ISO 42001 with NIST AI RMF
- Compliance leads building unified control libraries

## Roadmap

- [x] NIST CSF 2.0
- [x] ISO/IEC 27001:2022
- [x] NIST AI RMF 1.0
- [x] ISO/IEC 42001:2023
- [x] EU AI Act key articles
- [x] Cross-framework mappings file (~40 cross-framework mappings)
- [x] CLI lookup tool with 3 modes (lookup, search, framework dump)
- [ ] Public web interface

## About

Built by Breck Agyekum, GRC and AI Governance Analyst based in Canada. This project demonstrates the intersection of GRC framework expertise and modern AI-augmented tooling.

## License

MIT License — free to use, modify, and distribute.
