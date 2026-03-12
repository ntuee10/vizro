"""Prompt templates for the Vizro GenUI skill.

These prompts constrain the LLM to output valid Vizro configurations.
The key insight is that we never ask the LLM to write arbitrary Python -
we force it to fill in a structured schema.
"""

from __future__ import annotations

from typing import Any


def build_system_prompt(
    chart_descriptions: str,
    theme: str = "vizro_dark",
) -> str:
    """Build the system prompt that constrains LLM output to valid Vizro configs."""
    return f"""You are a senior data visualization architect specializing in executive-grade \
dashboards. You generate Vizro dashboard configurations that are:
- Analytically rigorous: charts chosen for the data type and question
- Visually clean: McKinsey presentation standards
- Interactive: appropriate filters and controls for drill-down

IMPORTANT CONSTRAINTS:
1. You MUST use the generate_vizro_dashboard tool to output your configuration.
2. Every Graph component needs a "chart_function" (a vizro.plotly.express function name) \
and "chart_params" (the parameters to pass to that function).
3. The "data_frame" parameter in chart_params should reference a registered dataset name as a string.
4. Available chart functions:
{chart_descriptions}

5. Default theme: "{theme}"
6. Each page must have a meaningful title and at least one component.
7. Use filters when the data has categorical columns suitable for segmentation.
8. Prefer Grid layout with explicit grid arrays for precise control over component placement.
9. For BP presentations: favor clean bar charts, line trends, and KPI cards.
10. For analytics dashboards: use scatter plots, heatmaps, and cross-filters.

OUTPUT FORMAT:
Your output MUST be a valid call to generate_vizro_dashboard with a JSON object containing:
- title: Dashboard title (string)
- theme: "vizro_dark" or "vizro_light"
- pages: Array of page objects, each with:
  - title: Page title
  - components: Array of component objects (Graph, Card, Text)
  - controls: Optional array of Filter/Parameter objects
  - layout: Optional Grid or Flex layout specification"""


def build_generation_prompt(
    analytical_objective: str,
    data_schemas: dict[str, dict[str, str]],
    additional_context: str = "",
) -> str:
    """Build the user prompt with the analytical objective and data context."""
    schema_descriptions = []
    for name, schema in data_schemas.items():
        cols = "\n".join(f"    - {col}: {dtype}" for col, dtype in schema.items())
        schema_descriptions.append(f"Dataset '{name}':\n{cols}")

    schemas_text = "\n\n".join(schema_descriptions) if schema_descriptions else "No datasets registered."

    prompt = f"""Generate a Vizro dashboard configuration for the following objective:

OBJECTIVE: {analytical_objective}

AVAILABLE DATA:
{schemas_text}

REQUIREMENTS:
- Choose the most appropriate chart types for the data and objective
- Add filters for categorical columns that enable meaningful drill-down
- Use clear, descriptive titles for pages and charts
- Arrange components in a logical visual hierarchy
- For Graph components, specify chart_function and chart_params
- Reference dataset names in the data_frame parameter"""

    if additional_context:
        prompt += f"\n\nADDITIONAL CONTEXT:\n{additional_context}"

    return prompt


def build_refinement_prompt(
    original_config: dict[str, Any],
    feedback: str,
) -> str:
    """Build a prompt for refining an existing dashboard based on user feedback."""
    import json
    config_str = json.dumps(original_config, indent=2)

    return f"""Refine the following Vizro dashboard configuration based on user feedback.

CURRENT CONFIGURATION:
{config_str}

USER FEEDBACK:
{feedback}

Generate an updated configuration that addresses the feedback while maintaining \
the overall structure and analytical value of the dashboard."""
