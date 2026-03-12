"""Inspect the Vizro schema extracted for LLM constraint.

Run this to see exactly what JSON schema the LLM is constrained to.
This is useful for debugging and understanding the skill's output contract.
"""

import json

from vizro_genui.schema.extractor import (
    extract_vizro_schema,
    get_constrained_schema,
    schema_to_tool_definition,
)
from vizro_genui.schema.chart_registry import get_chart_descriptions


def main():
    # Full schema
    print("=== Full Vizro Dashboard Schema ===")
    full_schema = extract_vizro_schema()
    print(f"Top-level keys: {list(full_schema.keys())}")
    print(f"Number of model definitions: {len(full_schema.get('$defs', {}))}")
    print(f"Model names: {list(full_schema.get('$defs', {}).keys())}")
    print()

    # Constrained schema (for BP use case - only Graph, Card, Filter)
    print("=== Constrained Schema (BP Mode) ===")
    bp_schema = get_constrained_schema(
        include_components=["Graph", "Card"],
        include_controls=["Filter"],
        max_pages=3,
    )
    print(f"Remaining model definitions: {list(bp_schema.get('$defs', {}).keys())}")
    print()

    # Tool definition ready for Claude API
    print("=== Claude Tool Definition ===")
    tool_def = schema_to_tool_definition()
    print(f"Tool name: {tool_def['name']}")
    print(f"Description: {tool_def['description'][:100]}...")
    print()

    # Available chart types
    print("=== Available Chart Types ===")
    print(get_chart_descriptions())


if __name__ == "__main__":
    main()
