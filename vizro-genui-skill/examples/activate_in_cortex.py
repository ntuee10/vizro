"""How to activate and use the Vizro GenUI Skill in Federator.ai Cortex.

This file shows the complete activation flow within Cortex's agentic orchestration.
"""

import pandas as pd

from vizro_genui import CortexSkillAdapter, CortexIntent


# =============================================================================
# STEP 1: Activate the Skill in Cortex's Agent Registry
# =============================================================================

def activate_skill():
    """Register the Vizro GenUI skill with Federator.ai Cortex.

    Call this during Cortex agent initialization (startup).
    The adapter self-registers as a skill that Cortex can route intents to.
    """
    adapter = CortexSkillAdapter(
        model="claude-sonnet-4-20250514",  # Or your preferred model
        default_theme="vizro_dark",
    )

    # Register the skill manifest with Cortex's agent registry
    manifest = adapter.get_skill_manifest()
    # cortex_agent_registry.register_skill(manifest, handler=adapter.handle_intent)

    return adapter


# =============================================================================
# STEP 2: Connect Federator.ai Data Sources
# =============================================================================

def connect_data_sources(adapter: CortexSkillAdapter):
    """Wire Federator.ai's data layer into the skill.

    These are the data sources from Federator.ai's CrystalClear and DataProphet
    engines that the skill uses to generate infrastructure dashboards.
    """

    # Option A: Static DataFrame (for testing / BP presentations)
    sample_gpu_data = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=100, freq="h"),
        "gpu_utilization_pct": [25 + i * 0.5 for i in range(100)],
        "cluster_id": ["cluster-a"] * 50 + ["cluster-b"] * 50,
        "gpu_model": ["H100"] * 30 + ["B200"] * 40 + ["GB200"] * 30,
    })
    adapter.register_federator_data("gpu_metrics", sample_gpu_data)

    # Option B: Dynamic callable (for live Federator.ai integration)
    # adapter.register_federator_data(
    #     "gpu_metrics",
    #     lambda: federator_api.get_metrics("/v1/gpu/utilization"),
    # )

    # Option C: CrystalClear predictions
    # adapter.register_federator_data(
    #     "workload_predictions",
    #     lambda: federator_api.get_predictions("/v1/crystal-clear/forecast"),
    # )

    # Option D: DataProphet recommendations
    # adapter.register_federator_data(
    #     "cost_recommendations",
    #     lambda: federator_api.get_recommendations("/v1/data-prophet/optimize"),
    # )


# =============================================================================
# STEP 3: Handle User Intents (Conversational Interface)
# =============================================================================

def handle_user_request(adapter: CortexSkillAdapter):
    """Example: Cortex routes a user's conversational request to this skill.

    In Federator.ai's patented agentic orchestration, the LLM parses user
    intent from the conversational interface and routes it to the appropriate skill.
    """

    # User says: "Show me GPU utilization across clusters"
    intent = CortexIntent(
        action="generate_dashboard",
        objective="Show GPU utilization trends across clusters with drill-down by GPU model",
        datasets=["gpu_metrics"],
    )

    response = adapter.handle_intent(intent)

    if response.status == "success":
        print(f"Dashboard generated: {response.message}")
        print(f"Config: {response.payload['config']}")
        print(f"Next actions available: {response.next_actions}")

        # The GenUI frontend receives this and renders the dashboard
        # Either via iframe (Pattern A) or by mapping to React components (Pattern B)
        return response.payload
    else:
        print(f"Error: {response.message}")
        return None


# =============================================================================
# STEP 4: Use Pre-built ADDC Templates
# =============================================================================

def use_addc_template(adapter: CortexSkillAdapter):
    """Load a pre-built ADDC operations template.

    Templates encode best practices for Federator.ai's core metrics:
    GPU utilization, workload prediction, cost optimization, compute marketplace.
    """
    intent = CortexIntent(
        action="get_template",
        objective="ADDC operations dashboard for GPU fleet monitoring",
    )

    response = adapter.handle_intent(intent)
    print(f"Template loaded: {response.payload.get('template_name')}")
    print(f"Python code:\n{response.payload.get('python_code')}")
    return response


# =============================================================================
# STEP 5: Refine and Export
# =============================================================================

def refine_and_export(adapter: CortexSkillAdapter):
    """Iteratively refine the dashboard, then export production code."""

    # First, generate a dashboard
    adapter.handle_intent(CortexIntent(
        action="generate_dashboard",
        objective="Quarterly GPU cost analysis",
        datasets=["gpu_metrics"],
    ))

    # Then refine based on feedback
    adapter.handle_intent(CortexIntent(
        action="refine_dashboard",
        objective="Quarterly GPU cost analysis",
        feedback="Add a comparison view between H100 and GB200 cost efficiency",
    ))

    # Finally, export as production code for the system
    export_response = adapter.handle_intent(CortexIntent(
        action="export_code",
        objective="Export final version",
    ))

    print("Production-ready Python code:")
    print(export_response.payload.get("python_code"))


# =============================================================================
# MAIN: Full Activation Flow
# =============================================================================

if __name__ == "__main__":
    print("=== Activating Vizro GenUI Skill in Federator.ai Cortex ===\n")

    # 1. Activate
    adapter = activate_skill()
    print("Skill activated. Manifest registered with Cortex.\n")

    # 2. Connect data
    connect_data_sources(adapter)
    print("Data sources connected.\n")

    # 3. Use template (no API key needed)
    print("=== Loading ADDC Template ===")
    use_addc_template(adapter)

    # 4. Generate dashboard (requires ANTHROPIC_API_KEY)
    # handle_user_request(adapter)

    # 5. Refine and export (requires ANTHROPIC_API_KEY)
    # refine_and_export(adapter)
