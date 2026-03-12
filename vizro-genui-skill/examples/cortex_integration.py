"""Federator.ai Cortex integration example.

Shows how to wire the VizroGenUISkill into a Cortex agent pipeline,
including both Pattern A (backend serving) and Pattern B (code incorporation).
"""

import json
from typing import Any

import pandas as pd

from vizro_genui import VizroGenUISkill
from vizro_genui.templates.bp_presentation import full_bp_dashboard


# ============================================================================
# Pattern A: Backend Dashboard Generator (Dynamic Serving)
# ============================================================================
# The Cortex agent invokes the skill, gets a URL, and streams it to the GenUI frontend.

def cortex_pattern_a(agent_context: dict[str, Any]) -> dict[str, Any]:
    """Cortex agent handler: generate and serve a dashboard dynamically.

    In the Cortex pipeline, this function is registered as a skill handler.
    The GenUI frontend receives the dashboard_url and renders it in an iframe.
    """
    skill = VizroGenUISkill(
        model="claude-sonnet-4-20250514",
        theme="vizro_light",  # Light theme for presentations
    )

    # Load data from the Cortex data layer
    dataset = agent_context.get("dataset")
    if dataset is not None:
        skill.register_data("primary", dataset)

    result = skill.invoke(
        analytical_objective=agent_context["user_query"],
        additional_context=agent_context.get("context", ""),
    )

    if result.is_valid:
        # In production: build and mount to dynamic route
        # app = skill.build(result.config)
        # url = mount_to_server(app)
        return {
            "type": "dashboard",
            "config": result.config,
            "code": result.python_code,
            "status": "success",
        }
    else:
        return {
            "type": "error",
            "errors": result.errors,
            "status": "validation_failed",
        }


# ============================================================================
# Pattern B: Code Incorporation (System Integration)
# ============================================================================
# Generate the code, review it, and incorporate it into the system codebase.

def cortex_pattern_b() -> str:
    """Generate dashboard code for direct incorporation into the system.

    Use this when building permanent features, not ad-hoc dashboards.
    The generated code is McKinsey-grade and ready for code review.
    """
    skill = VizroGenUISkill()

    # Use a pre-built template as the starting point
    bp_config = full_bp_dashboard(
        dashboard_title="FY2026 Business Plan Review",
        theme="vizro_light",
    )

    # Convert to clean, production-ready Python code
    code = skill.to_code(bp_config)
    return code


# ============================================================================
# Pattern C: Hybrid - Template + LLM Refinement
# ============================================================================
# Start from a template, then let the LLM customize based on specific data.

def cortex_pattern_c(
    data: pd.DataFrame,
    objective: str,
) -> dict[str, Any]:
    """Start from a BP template and refine with LLM based on actual data."""
    from vizro_genui.cortex.prompts import build_refinement_prompt

    skill = VizroGenUISkill()
    skill.register_data("primary", data)

    # Start with the template
    base_config = full_bp_dashboard()

    # Invoke the skill to refine
    result = skill.invoke(
        analytical_objective=(
            f"Refine the following dashboard template for this specific objective: {objective}. "
            f"The template has {len(base_config['pages'])} pages. Adapt the chart types "
            f"and filters to match the actual data columns available."
        ),
        dataset_names=["primary"],
    )

    return {
        "base_template": base_config,
        "refined_config": result.config,
        "code": result.python_code,
    }


if __name__ == "__main__":
    # Demo: Pattern B - generate code from template
    print("=== Pattern B: Code Incorporation ===")
    code = cortex_pattern_b()
    print(code)

    # Demo: Pattern A - simulate agent context
    print("\n=== Pattern A: Dynamic Generation ===")
    sample_data = pd.DataFrame({
        "quarter": ["Q1", "Q2", "Q3", "Q4"],
        "revenue": [100, 120, 115, 140],
        "region": ["APAC", "EMEA", "Americas", "APAC"],
    })

    context = {
        "user_query": "Show me a revenue overview dashboard",
        "dataset": sample_data,
        "context": "Executive presentation for board meeting",
    }
    # result = cortex_pattern_a(context)  # Uncomment with valid API key
    print("Pattern A requires an Anthropic API key to run.")
