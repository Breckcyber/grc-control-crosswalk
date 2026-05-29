#!/usr/bin/env python3
"""
crosswalk.py  —  Cross-framework control crosswalk for GRC frameworks.

WHAT THIS TOOL DOES
-------------------
Given a single control (for example ISO 27001 "A.5.1"), it tells you how that
control maps across the other governance frameworks in the data/ folder
(NIST CSF 2.0, NIST AI RMF, ISO/IEC 42001, EU AI Act, etc.). It reads the
framework definitions and a mappings file, then prints the control's details
followed by every related control in other frameworks.

HOW TO USE IT (three modes)
---------------------------
MODE A - Look up one control and see all its cross-framework mappings:
    python src/crosswalk.py "ISO 27001 A.5.1"
    python src/crosswalk.py "A.5.1"          (framework prefix is optional)

MODE B - Search every framework by keyword (name + description):
    python src/crosswalk.py --search "policy"

MODE C - List every control in one framework:
    python src/crosswalk.py --framework "NIST CSF 2.0"

For full help:
    python src/crosswalk.py --help

THE MAPPING IS BIDIRECTIONAL
----------------------------
If mappings.yaml says A.5.1 -> GV.PO-01, then looking up *either* control will
show the relationship. Looking up A.5.1 shows it as a SOURCE (it maps out to
GV.PO-01); looking up GV.PO-01 shows it as a TARGET (A.5.1 maps in to it).
That is almost always what you want from a crosswalk.

EXPECTED DATA FORMAT
--------------------
Each framework file (e.g. data/iso-27001.yaml) should look like:

    framework: "ISO 27001:2022"
    controls:
      - id: "A.5.1"
        name: "Policies for information security"
        description: "Management direction for information security..."

The mappings file (data/mappings.yaml) uses the NESTED schema:

    mappings:                       # the top-level "mappings:" key is optional
      - source:
          framework: "ISO 27001:2022"
          id: "A.5.1"
        targets:
          - framework: "NIST CSF 2.0"
            id: "GV.PO-01"
            relationship: "Direct"
            notes: "Both address top-level security policy."   # optional

The loaders are deliberately forgiving. A framework name may also appear under
'name'/'title', controls under 'items', and control text under 'title'/'desc'.
Mappings may be a top-level list OR sit under 'mappings:'. Each entry's source
may be a {framework, id} object OR a single "Framework ID" string, and targets
may be a list OR a single 'target'. Adjust the *_ALIASES blocks near the top if
your files use different key names.
"""

import argparse
import difflib
import sys
from pathlib import Path

import yaml  # PyYAML - the only required third-party dependency


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# The framework files we expect to find inside the data/ folder.
FRAMEWORK_FILES = [
    "nist-csf.yaml",
    "iso-27001.yaml",
    "nist-ai-rmf.yaml",
    "iso-42001.yaml",
    "eu-ai-act.yaml",
]
MAPPINGS_FILE = "mappings.yaml"

# Accepted alternative key names for framework files, so the tool works even if
# your YAML uses slightly different field names. The first match wins.
FIELD_ALIASES = {
    "framework_name": ["framework", "name", "title"],
    "control_list": ["controls", "items"],
    "control_id": ["id", "control_id", "ref"],
    "control_name": ["name", "title"],
    "control_desc": ["description", "desc", "summary"],
}

# Accepted alternative key names for the mappings file (the nested schema).
MAPPING_ALIASES = {
    "mapping_list": ["mappings", "crosswalk", "links"],
    "map_source": ["source", "from", "src"],
    "map_targets": ["targets", "target", "to"],
    "map_framework": ["framework", "fw", "standard"],
    "map_id": ["id", "control_id", "ref"],
    "map_relationship": ["relationship", "type", "rel"],
    "map_notes": ["notes", "note", "comment"],
}


# ---------------------------------------------------------------------------
# Colour handling (with graceful fallback if colorama is missing)
# ---------------------------------------------------------------------------

class Palette:
    """Holds the colour codes used for output.

    If colorama is installed we use real ANSI colours; if not, every code
    becomes an empty string so the tool still prints clean plain text.
    """

    def __init__(self):
        try:
            from colorama import Fore, Style, init
            init()  # makes ANSI colours work on Windows terminals too
            self.framework = Fore.CYAN
            self.control = Fore.YELLOW
            self.relationship = Fore.GREEN
            self.heading = Fore.MAGENTA
            self.dim = Style.DIM
            self.reset = Style.RESET_ALL
            self.enabled = True
        except ImportError:
            # colorama not installed -> no colours, but no crash either.
            self.framework = ""
            self.control = ""
            self.relationship = ""
            self.heading = ""
            self.dim = ""
            self.reset = ""
            self.enabled = False


def colorize(text, colour, palette):
    """Wrap text in a colour code and reset, or return it plain if colours off."""
    if not colour:
        return text
    return f"{colour}{text}{palette.reset}"


# ---------------------------------------------------------------------------
# Small generic helpers
# ---------------------------------------------------------------------------

def first_present(record, alias_key):
    """Return the first value found in `record` for any alias of `alias_key`.

    Lets us read e.g. a control's id whether the YAML calls it 'id',
    'control_id', or 'ref'. Returns None if none of the aliases are present.
    """
    if not isinstance(record, dict):
        return None
    for key in FIELD_ALIASES[alias_key]:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def first_present_map(record, alias_key):
    """Same as first_present(), but for the mappings-file alias table."""
    if not isinstance(record, dict):
        return None
    for key in MAPPING_ALIASES[alias_key]:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def normalize(value):
    """Normalise an ID/name for comparison: trim, collapse spaces, upper-case.

    So 'a.5.1', ' A.5.1 ' and 'A.5.1' all compare equal.
    """
    if value is None:
        return ""
    return " ".join(str(value).split()).upper()


# ---------------------------------------------------------------------------
# Loading the YAML data
# ---------------------------------------------------------------------------

def load_yaml_file(path):
    """Safely load one YAML file. Returns the parsed object, or None on error.

    Uses yaml.safe_load (never yaml.load) so the files cannot execute code.
    Prints a clear, specific message if a file is missing or malformed.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except FileNotFoundError:
        print(f"  [!] File not found: {path}", file=sys.stderr)
        return None
    except yaml.YAMLError as error:
        print(f"  [!] Could not parse YAML in {path}: {error}", file=sys.stderr)
        return None


def load_framework(path):
    """Load a single framework file into a tidy dict.

    Returns {"name": <framework name>, "controls": [ {id, name, description}, ... ]}
    or None if the file could not be read.
    """
    raw = load_yaml_file(path)
    if raw is None:
        return None

    framework_name = first_present(raw, "framework_name") or Path(path).stem
    raw_controls = first_present(raw, "control_list") or []

    controls = []
    for item in raw_controls:
        controls.append({
            "id": first_present(item, "control_id"),
            "name": first_present(item, "control_name") or "",
            "description": first_present(item, "control_desc") or "",
        })

    return {"name": framework_name, "controls": controls}


def load_all_frameworks(data_dir):
    """Load every framework file in FRAMEWORK_FILES from data_dir.

    Returns a list of framework dicts. Missing files are skipped with a warning
    rather than stopping the whole tool.
    """
    frameworks = []
    for filename in FRAMEWORK_FILES:
        framework = load_framework(data_dir / filename)
        if framework is not None:
            frameworks.append(framework)
    return frameworks


def load_mappings(data_dir):
    """Load mappings.yaml into a normalised list of mapping entries.

    Accepts BOTH supported shapes:

      Nested (current):                Flat (legacy):
        - source:                        - source: "ISO 27001 A.5.1"
            framework: "ISO 27001:2022"    target: "NIST CSF 2.0 GV.PO-01"
            id: "A.5.1"                    relationship: "Direct"
          targets:                         notes: "..."
            - framework: "NIST CSF 2.0"
              id: "GV.PO-01"
              relationship: "Direct"
              notes: "..."

    Each returned entry is normalised to:
        {
          "source": {"framework": <str|None>, "id": <str>},
          "targets": [ {"framework", "id", "relationship", "notes"}, ... ],
        }
    """
    raw = load_yaml_file(data_dir / MAPPINGS_FILE)
    if raw is None:
        return []

    # The file may be a bare list, or a dict with a 'mappings:' key.
    if isinstance(raw, dict):
        raw_entries = first_present_map(raw, "mapping_list") or []
    elif isinstance(raw, list):
        raw_entries = raw
    else:
        raw_entries = []

    entries = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            continue
        source = _parse_endpoint(first_present_map(raw_entry, "map_source"))
        targets = _parse_targets(raw_entry)
        if source["id"] is None and not targets:
            continue  # nothing usable in this entry
        entries.append({"source": source, "targets": targets})
    return entries


def _parse_endpoint(value):
    """Turn a source/target into {framework, id}.

    Accepts a {framework, id} object (nested schema) or a "Framework ID"
    string (legacy schema, where the ID is the last whitespace token).
    """
    if isinstance(value, dict):
        return {
            "framework": first_present_map(value, "map_framework"),
            "id": first_present_map(value, "map_id"),
        }
    if isinstance(value, str) and value.strip():
        framework, control_id = split_query(value)
        return {"framework": framework, "id": control_id}
    return {"framework": None, "id": None}


def _parse_targets(raw_entry):
    """Extract the list of normalised targets from one mapping entry.

    Handles 'targets:' as a list, a single 'target:' object, or the legacy flat
    form where the relationship/notes sit on the entry itself alongside a
    single 'target:' string.
    """
    targets = []
    raw_targets = first_present_map(raw_entry, "map_targets")

    # Normalise to a list we can iterate over.
    if raw_targets is None:
        candidates = []
    elif isinstance(raw_targets, list):
        candidates = raw_targets
    else:
        candidates = [raw_targets]

    for candidate in candidates:
        endpoint = _parse_endpoint(candidate)
        # Relationship/notes may live on the target (nested) or, for the legacy
        # flat form, on the parent entry. Prefer the target, fall back to entry.
        relationship = (
            first_present_map(candidate, "map_relationship")
            if isinstance(candidate, dict) else None
        ) or first_present_map(raw_entry, "map_relationship") or "related"
        notes = (
            first_present_map(candidate, "map_notes")
            if isinstance(candidate, dict) else None
        ) or first_present_map(raw_entry, "map_notes") or ""

        if endpoint["id"] is not None:
            targets.append({
                "framework": endpoint["framework"],
                "id": endpoint["id"],
                "relationship": relationship,
                "notes": notes,
            })
    return targets


# ---------------------------------------------------------------------------
# Lookup logic
# ---------------------------------------------------------------------------

def split_query(query):
    """Split a lookup string into (framework_hint, control_id).

    The control ID is taken to be the LAST whitespace-separated token, and any
    words before it are treated as a framework hint. So:
        "ISO 27001 A.5.1" -> ("ISO 27001", "A.5.1")
        "A.5.1"           -> (None, "A.5.1")
    The framework hint is optional everywhere in this tool; lookups match on ID.
    """
    tokens = query.strip().split()
    if not tokens:
        return None, ""
    if len(tokens) == 1:
        return None, tokens[0]
    framework_hint = " ".join(tokens[:-1])
    control_id = tokens[-1]
    return framework_hint, control_id


def find_control(control_id, frameworks):
    """Find a control by ID across ALL frameworks (framework name not required).

    Returns (framework_name, control_dict) for the first match, or None.
    This is what lets the user type just "A.5.1" and have the tool work out
    which framework it belongs to.
    """
    target = normalize(control_id)
    for framework in frameworks:
        for control in framework["controls"]:
            if normalize(control["id"]) == target:
                return framework["name"], control
    return None


def suggest_closest(control_id, frameworks):
    """Return up to 3 control IDs that look closest to a not-found input.

    Powers the "did you mean...?" message. Uses difflib over every known ID.
    """
    all_ids = [
        control["id"]
        for framework in frameworks
        for control in framework["controls"]
        if control["id"]
    ]
    return difflib.get_close_matches(control_id, all_ids, n=3, cutoff=0.5)


def find_framework(name, frameworks):
    """Find a framework by name (case-insensitive, forgiving of extra spaces).

    Returns the framework dict, or None if not found.
    """
    target = normalize(name)
    for framework in frameworks:
        if normalize(framework["name"]) == target:
            return framework
    # Looser fallback: allow a partial match like "NIST CSF" for "NIST CSF 2.0".
    for framework in frameworks:
        if target in normalize(framework["name"]):
            return framework
    return None


def find_mappings(control_id, mappings):
    """Find every mapping that touches `control_id`, in BOTH directions.

    Matching is on the control ID only (never the framework name), so a bare
    ID like "A.5.1" works. Returns two lists of result rows:

        as_source: this control maps OUT to these controls
                   [{"framework", "id", "relationship", "notes"}, ...]
        as_target: these controls map IN to this control (reverse direction)
                   [{"framework", "id", "relationship", "notes"}, ...]
    """
    target = normalize(control_id)
    as_source = []
    as_target = []

    for entry in mappings:
        source = entry["source"]
        source_matches = normalize(source["id"]) == target

        for tgt in entry["targets"]:
            target_matches = normalize(tgt["id"]) == target

            if source_matches:
                # Our control is the source -> the other control is the target.
                as_source.append({
                    "framework": tgt["framework"],
                    "id": tgt["id"],
                    "relationship": tgt["relationship"],
                    "notes": tgt["notes"],
                })
            if target_matches:
                # Our control is the target -> point back to the source.
                as_target.append({
                    "framework": source["framework"],
                    "id": source["id"],
                    "relationship": tgt["relationship"],
                    "notes": tgt["notes"],
                })

    return as_source, as_target


def search_keyword(keyword, frameworks):
    """Find controls whose name or description contains `keyword`.

    Plain case-insensitive substring match. Returns a list of
    (framework_name, control_dict), capped by the caller.
    """
    needle = keyword.strip().lower()
    hits = []
    for framework in frameworks:
        for control in framework["controls"]:
            haystack = f"{control['name']} {control['description']}".lower()
            if needle in haystack:
                hits.append((framework["name"], control))
    return hits


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_header(title, palette):
    """Print a clean section header."""
    bar = "=" * len(title)
    print()
    print(colorize(title, palette.heading, palette))
    print(colorize(bar, palette.heading, palette))


def display_control(framework_name, control, palette):
    """Print the details of a single control."""
    print_header("Control", palette)
    print(f"  Framework:   {colorize(framework_name, palette.framework, palette)}")
    print(f"  Control ID:  {colorize(control['id'], palette.control, palette)}")
    print(f"  Name:        {control['name']}")
    if control["description"]:
        print(f"  Description: {control['description']}")


def display_mappings(as_source, as_target, palette):
    """Print all cross-framework mappings, separated by direction.

    `as_source` = controls this one maps out to.
    `as_target` = controls that map in to this one (reverse direction).
    """
    print_header("Cross-framework mappings", palette)

    if not as_source and not as_target:
        print("  No mappings found for this control yet.")
        return

    if as_source:
        print(f"  {colorize('Maps OUT to (this control as source):', palette.dim, palette)}")
        for row in as_source:
            _print_mapping_row(row, palette)

    if as_target:
        if as_source:
            print()
        print(f"  {colorize('Mapped FROM (this control as target):', palette.dim, palette)}")
        for row in as_target:
            _print_mapping_row(row, palette)


def _print_mapping_row(row, palette):
    """Print one mapping line: framework, control ID, relationship, notes."""
    framework = colorize(row["framework"] or "(unspecified framework)",
                         palette.framework, palette)
    control_id = colorize(row["id"], palette.control, palette)
    relationship = colorize(row["relationship"], palette.relationship, palette)
    print(f"    - {framework}  {control_id}  [{relationship}]")
    if row["notes"]:
        print(f"        {colorize(row['notes'], palette.dim, palette)}")


def display_search_results(keyword, hits, palette):
    """Print up to 10 keyword search matches."""
    print_header(f"Search results for '{keyword}'", palette)
    if not hits:
        print("  No controls matched that keyword.")
        return
    for framework_name, control in hits[:10]:
        framework = colorize(framework_name, palette.framework, palette)
        control_id = colorize(control["id"], palette.control, palette)
        print(f"  - {framework}  {control_id}  {control['name']}")
    if len(hits) > 10:
        print(f"  ... and {len(hits) - 10} more. Narrow the keyword to see fewer.")


def display_framework_dump(framework, palette):
    """List every control in one framework (ID + name)."""
    print_header(f"All controls in {framework['name']}", palette)
    if not framework["controls"]:
        print("  This framework has no controls listed.")
        return
    for control in framework["controls"]:
        control_id = colorize(control["id"], palette.control, palette)
        print(f"  {control_id}  {control['name']}")
    print(f"\n  {len(framework['controls'])} control(s) total.")


# ---------------------------------------------------------------------------
# Mode handlers
# ---------------------------------------------------------------------------

def run_lookup(query, frameworks, mappings, palette):
    """MODE A: look up one control and show all of its mappings."""
    _framework_hint, control_id = split_query(query)

    match = find_control(control_id, frameworks)
    if match is None:
        print(f"\n  Control '{control_id}' was not found in any framework.")
        suggestions = suggest_closest(control_id, frameworks)
        if suggestions:
            print("  Did you mean: " + ", ".join(
                colorize(s, palette.control, palette) for s in suggestions
            ) + "?")
        return 1

    framework_name, control = match
    display_control(framework_name, control, palette)

    # Match mappings on the control's canonical ID from the framework file,
    # which is the reliable key (the typed input may differ in case/spacing).
    as_source, as_target = find_mappings(control["id"], mappings)
    display_mappings(as_source, as_target, palette)
    return 0


def run_search(keyword, frameworks, palette):
    """MODE B: keyword search across all framework names + descriptions."""
    hits = search_keyword(keyword, frameworks)
    display_search_results(keyword, hits, palette)
    return 0


def run_framework_dump(name, frameworks, palette):
    """MODE C: list every control in one framework."""
    framework = find_framework(name, frameworks)
    if framework is None:
        print(f"\n  Framework '{name}' was not found.")
        known = ", ".join(colorize(f["name"], palette.framework, palette)
                          for f in frameworks)
        print(f"  Known frameworks: {known}")
        return 1
    display_framework_dump(framework, palette)
    return 0


# ---------------------------------------------------------------------------
# Command-line plumbing
# ---------------------------------------------------------------------------

def build_parser():
    """Build the argument parser with all three modes documented."""
    parser = argparse.ArgumentParser(
        prog="crosswalk.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Cross-framework control crosswalk for GRC frameworks.\n\n"
            "MODE A  Look up a control and see all its cross-framework mappings:\n"
            '          python src/crosswalk.py "ISO 27001 A.5.1"\n'
            '          python src/crosswalk.py "A.5.1"   (framework prefix optional)\n\n'
            "MODE B  Keyword search across all frameworks (name + description):\n"
            '          python src/crosswalk.py --search "policy"\n\n'
            "MODE C  List all controls in one framework:\n"
            '          python src/crosswalk.py --framework "NIST CSF 2.0"'
        ),
    )
    parser.add_argument(
        "control",
        nargs="?",
        help='A control to look up, e.g. "A.5.1" or "ISO 27001 A.5.1" (Mode A).',
    )
    parser.add_argument(
        "--search",
        metavar="KEYWORD",
        help="Keyword search across all frameworks (Mode B).",
    )
    parser.add_argument(
        "--framework",
        metavar="NAME",
        help='List all controls in one framework, e.g. "NIST CSF 2.0" (Mode C).',
    )
    parser.add_argument(
        "--data-dir",
        metavar="PATH",
        default="data",
        help="Folder holding the framework + mappings YAML files (default: data).",
    )
    return parser


def main(argv=None):
    """Entry point: parse arguments, load data, dispatch to the right mode."""
    parser = build_parser()
    args = parser.parse_args(argv)
    palette = Palette()

    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        print(f"  [!] Data folder not found: {data_dir}", file=sys.stderr)
        return 2

    frameworks = load_all_frameworks(data_dir)
    if not frameworks:
        print("  [!] No framework files could be loaded. Check the data/ folder.",
              file=sys.stderr)
        return 2

    # Dispatch. Mode B and C don't need the mappings file; Mode A does.
    if args.search:
        return run_search(args.search, frameworks, palette)
    if args.framework:
        return run_framework_dump(args.framework, frameworks, palette)
    if args.control:
        mappings = load_mappings(data_dir)
        return run_lookup(args.control, frameworks, mappings, palette)

    # No mode chosen -> show help rather than failing silently.
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())