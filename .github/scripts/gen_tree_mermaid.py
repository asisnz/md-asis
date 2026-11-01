#!/usr/bin/env python3
"""Generate a Mermaid graph LR from CAN/TREE-<quarter>.json.

Writes a ```mermaid block to stdout. Subtypes and connections with a non-zero
`value` (wins - losses, written by update_tree_values.py) show it and are coloured.
Called by update-tree-mermaid.yml; update TREE_FILE at quarter rollover.
"""

import json
import re
import sys

TREE_FILE = "CAN/TREE-2026Q3.json"


def safe_id(text: str) -> str:
    """Strip non-alphanumeric chars to make a valid Mermaid node id."""
    return re.sub(r"[^A-Za-z0-9]", "_", text)


def gen_mermaid(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    quarter = data["meta"]["quarter"]
    lines = [
        "```mermaid",
        "graph LR",
        f'  ROOT(["🔴 ASIS New Zealand · {quarter}"])',
    ]

    classed = {"win": [], "lost": []}

    # connections{} comes before tree[] in the JSON — render it first
    conns = data.get("connections", {})
    if conns:
        lines.append('  ROOT --> CONNECTIONS["connections"]')
        group_labels = {"own": "own", "associations": "associations", "partners": "partners"}
        for group, label in group_labels.items():
            members = conns.get(group, {})
            if not members:
                continue
            grp_id = f'CONN_{group}'
            lines.append(f'  CONNECTIONS --> {grp_id}["{label}"]')
            for name, entry in members.items():
                mem_id = f'{grp_id}_{safe_id(name)}'
                value = entry.get("value", 0) if isinstance(entry, dict) else 0
                shown = f"{name} · {value:+d}" if value else name
                if value:
                    classed["win" if value > 0 else "lost"].append(mem_id)
                lines.append(f'  {grp_id} --> {mem_id}("{shown}")')

    # tree[] — grouped under a TREE node to match JSON structure
    lines.append('  ROOT --> TREE["tree"]')
    for cat in data["tree"]:
        cat_id = safe_id(cat["category"])
        lines.append(f'  TREE --> {cat_id}["{cat["category"]}"]')
        for t in cat["types"]:
            type_id = f'{cat_id}_{safe_id(t["type"])}'
            lines.append(f'  {cat_id} --> {type_id}["{t["type"]}"]')
            for s in t["subtypes"]:
                sub_id = f'{type_id}_{safe_id(s["name"])}'
                label = s["name"]
                # "value" is written by update_tree_values.py (wins - losses);
                # only non-zero values get a badge and a colour.
                value = s.get("value", 0)
                if value:
                    label += f" · {value:+d}"
                    classed["win" if value > 0 else "lost"].append(sub_id)
                lines.append(f'  {type_id} --> {sub_id}("{label}")')

    # Colour by net value: green = net win, red = net lost
    lines.append("  classDef win fill:#d4edda,stroke:#2e7d32,color:#1b5e20")
    lines.append("  classDef lost fill:#f8d7da,stroke:#c62828,color:#7f0000")
    for outcome, ids in classed.items():
        if ids:
            lines.append(f'  class {",".join(ids)} {outcome}')

    lines.append("```")
    return "\n".join(lines)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else TREE_FILE
    print(gen_mermaid(path))
