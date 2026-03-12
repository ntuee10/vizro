"""Extract and constrain Vizro's Pydantic JSON Schema for strict LLM output enforcement.

The core insight: Vizro abstracts Dash/Plotly behind Pydantic models. By extracting
the JSON schema, we force the LLM to output ONLY valid dashboard configurations -
no raw Python code, no syntax errors, no execution vulnerabilities.
"""

from __future__ import annotations

import json
from typing import Any


def extract_vizro_schema() -> dict[str, Any]:
    """Extract the full JSON Schema from Vizro's Dashboard Pydantic model.

    Returns the complete schema including all nested models (Page, Graph, Filter, etc.)
    via Pydantic's $defs mechanism.
    """
    from vizro.models import Dashboard

    return Dashboard.model_json_schema()


def get_constrained_schema(
    include_components: list[str] | None = None,
    include_controls: list[str] | None = None,
    max_pages: int | None = None,
) -> dict[str, Any]:
    """Return a constrained subset of the Vizro schema for targeted generation.

    For BP presentations, you may only need Graph + Card + Filter.
    For Cortex analytics dashboards, you may want the full component set.

    Args:
        include_components: Whitelist of component types (e.g., ["Graph", "Card", "Table"]).
            If None, all components are included.
        include_controls: Whitelist of control types (e.g., ["Filter"]).
            If None, all controls are included.
        max_pages: Maximum number of pages allowed in the generated dashboard.
    """
    schema = extract_vizro_schema()

    if max_pages is not None:
        _apply_max_pages(schema, max_pages)

    if include_components is not None:
        _filter_component_types(schema, include_components)

    if include_controls is not None:
        _filter_control_types(schema, include_controls)

    return schema


def get_schema_for_structured_output() -> dict[str, Any]:
    """Return a simplified schema suitable for LLM structured output APIs.

    Strips Vizro-internal fields (type discriminators, private attrs) and
    returns a clean schema that works with Claude's tool_use or structured output.
    """
    schema = extract_vizro_schema()
    _strip_internal_fields(schema)
    return schema


def schema_to_tool_definition(
    name: str = "generate_vizro_dashboard",
    description: str | None = None,
) -> dict[str, Any]:
    """Package the Vizro schema as a Claude tool_use definition.

    This is the tool definition you pass to Claude's API so it generates
    a valid Vizro config as a structured tool call.
    """
    if description is None:
        description = (
            "Generate a complete, interactive dashboard configuration. "
            "The output must strictly adhere to the Vizro Dashboard JSON Schema. "
            "Use vizro.plotly.express chart functions for the figure field in Graph components."
        )

    schema = get_schema_for_structured_output()

    return {
        "name": name,
        "description": description,
        "input_schema": schema,
    }


def _apply_max_pages(schema: dict[str, Any], max_pages: int) -> None:
    """Inject maxItems constraint on the pages array."""
    if "properties" in schema and "pages" in schema["properties"]:
        schema["properties"]["pages"]["maxItems"] = max_pages


def _filter_component_types(schema: dict[str, Any], allowed: list[str]) -> None:
    """Remove component $defs not in the allowed list."""
    defs = schema.get("$defs", {})
    component_models = {
        "AgGrid", "Button", "Card", "Container", "Figure",
        "Graph", "Table", "Tabs", "Text",
    }
    for model_name in component_models - set(allowed):
        defs.pop(model_name, None)


def _filter_control_types(schema: dict[str, Any], allowed: list[str]) -> None:
    """Remove control $defs not in the allowed list."""
    defs = schema.get("$defs", {})
    control_models = {"Filter", "Parameter"}
    for model_name in control_models - set(allowed):
        defs.pop(model_name, None)


def _strip_internal_fields(schema: dict[str, Any]) -> None:
    """Remove Vizro-internal fields that confuse LLMs."""
    internal_keys = {"type"}  # Vizro uses 'type' as discriminator, not needed in generation
    defs = schema.get("$defs", {})
    for model_schema in defs.values():
        if "properties" in model_schema:
            for key in internal_keys:
                model_schema["properties"].pop(key, None)
