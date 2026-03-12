"""Registry of available chart functions and their parameter schemas.

This maps vizro.plotly.express functions to their signatures so the LLM
knows exactly which chart types are available and what parameters they accept.
"""

from __future__ import annotations

import inspect
from typing import Any


# Chart functions available in vizro.plotly.express that the LLM can reference.
# Each entry maps function_name -> { description, required_params, optional_params }
CHART_REGISTRY: dict[str, dict[str, Any]] = {
    "scatter": {
        "description": "Scatter plot for showing relationships between two continuous variables",
        "required": ["data_frame", "x", "y"],
        "optional": ["color", "size", "hover_name", "hover_data", "title", "template"],
    },
    "bar": {
        "description": "Bar chart for comparing categorical data",
        "required": ["data_frame", "x", "y"],
        "optional": ["color", "barmode", "orientation", "title", "template"],
    },
    "line": {
        "description": "Line chart for showing trends over time or continuous data",
        "required": ["data_frame", "x", "y"],
        "optional": ["color", "line_dash", "hover_data", "title", "template"],
    },
    "histogram": {
        "description": "Histogram for showing distribution of a single variable",
        "required": ["data_frame", "x"],
        "optional": ["y", "color", "nbins", "barmode", "title", "template"],
    },
    "box": {
        "description": "Box plot for showing statistical distribution",
        "required": ["data_frame", "x", "y"],
        "optional": ["color", "points", "title", "template"],
    },
    "violin": {
        "description": "Violin plot for showing distribution shape",
        "required": ["data_frame", "x", "y"],
        "optional": ["color", "box", "points", "title", "template"],
    },
    "pie": {
        "description": "Pie chart for showing proportions of a whole",
        "required": ["data_frame", "values", "names"],
        "optional": ["color", "hole", "title", "template"],
    },
    "treemap": {
        "description": "Treemap for hierarchical data visualization",
        "required": ["data_frame", "path", "values"],
        "optional": ["color", "title", "template"],
    },
    "funnel": {
        "description": "Funnel chart for showing progressive reduction in data",
        "required": ["data_frame", "x", "y"],
        "optional": ["color", "title", "template"],
    },
    "scatter_matrix": {
        "description": "Scatter matrix for pairwise relationships across multiple variables",
        "required": ["data_frame", "dimensions"],
        "optional": ["color", "title", "template"],
    },
    "heatmap": {
        "description": "Heatmap for showing magnitude across two categorical dimensions",
        "required": ["data_frame", "x", "y", "z"],
        "optional": ["color_continuous_scale", "title", "template"],
    },
    "area": {
        "description": "Area chart for showing cumulative trends",
        "required": ["data_frame", "x", "y"],
        "optional": ["color", "line_group", "title", "template"],
    },
    "strip": {
        "description": "Strip plot for showing individual data points along a category axis",
        "required": ["data_frame", "x", "y"],
        "optional": ["color", "orientation", "title", "template"],
    },
}


def get_chart_descriptions() -> str:
    """Return a formatted string of all available chart types for the LLM prompt."""
    lines = []
    for name, info in CHART_REGISTRY.items():
        required = ", ".join(info["required"])
        optional = ", ".join(info["optional"])
        lines.append(
            f"- px.{name}: {info['description']}\n"
            f"  Required: {required}\n"
            f"  Optional: {optional}"
        )
    return "\n".join(lines)


def get_chart_names() -> list[str]:
    """Return list of valid chart function names."""
    return list(CHART_REGISTRY.keys())


def validate_chart_reference(chart_name: str, params: dict[str, Any]) -> list[str]:
    """Validate that a chart reference uses correct function name and required params.

    Returns list of validation errors (empty if valid).
    """
    errors = []
    if chart_name not in CHART_REGISTRY:
        errors.append(f"Unknown chart type: {chart_name}. Valid types: {get_chart_names()}")
        return errors

    spec = CHART_REGISTRY[chart_name]
    for req in spec["required"]:
        if req not in params and req != "data_frame":  # data_frame is injected by Vizro
            errors.append(f"Chart '{chart_name}' requires parameter '{req}'")

    return errors
