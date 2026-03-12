"""Federator.ai Cortex agent adapter for the Vizro GenUI skill.

Federator.ai Cortex is ProphetStor's agentic orchestration layer that dynamically
coordinates intelligent agents via LLM-driven workflows. This module provides:

1. A CortexSkillAdapter that registers the VizroGenUISkill as a Cortex-compatible
   agent skill, following the conversational interface pattern from ProphetStor's
   patented agentic orchestration system.

2. Resource-aware dashboard generation that integrates with Federator.ai's
   CrystalClear Time Series Analysis and DataProphet Recommendation engines
   to visualize workload predictions, resource allocation, and cost optimization.

3. ADDC (AI-Defined Data Center) dashboard templates for GPU utilization,
   cluster health, and compute marketplace analytics.

Architecture:
    Federator.ai Cortex (Agentic Orchestration)
        -> Conversational Interface (LLM understands user intent)
        -> CortexSkillAdapter.handle_intent()
        -> VizroGenUISkill.invoke()
        -> Validated Vizro Config
        -> Dashboard served via Federator.ai's web layer
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

import pandas as pd

from vizro_genui.cortex.skill import VizroGenUISkill, SkillResult


@dataclass
class CortexIntent:
    """Parsed intent from Federator.ai Cortex's conversational interface."""

    action: str  # "generate_dashboard", "refine_dashboard", "get_template"
    objective: str  # The analytical objective
    datasets: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    feedback: str = ""  # For refinement intents


@dataclass
class CortexResponse:
    """Response format for Federator.ai Cortex agentic orchestration."""

    status: str  # "success", "validation_failed", "error"
    artifact_type: str  # "dashboard_config", "python_code", "dashboard_url"
    payload: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    next_actions: list[str] = field(default_factory=list)


class CortexSkillAdapter:
    """Adapter that registers VizroGenUISkill within Federator.ai Cortex.

    This adapter bridges Cortex's agentic orchestration (intent -> workflow -> execution)
    with the Vizro GenUI skill's structured output pipeline.

    Usage in Federator.ai Cortex:

        # During Cortex agent initialization
        adapter = CortexSkillAdapter()

        # Register infrastructure data sources from Federator.ai
        adapter.register_federator_data(
            "gpu_utilization",
            lambda: fetch_from_federator_api("/metrics/gpu"),
        )

        # Handle user intent from conversational interface
        response = adapter.handle_intent(CortexIntent(
            action="generate_dashboard",
            objective="Show GPU utilization trends across clusters",
            datasets=["gpu_utilization"],
        ))

        # Cortex serves the dashboard via its web layer
        dashboard_config = response.payload["config"]
    """

    def __init__(
        self,
        llm_client: Any = None,
        model: str = "claude-sonnet-4-20250514",
        default_theme: str = "vizro_dark",
    ):
        self._skill = VizroGenUISkill(
            llm_client=llm_client,
            model=model,
            theme=default_theme,
        )
        self._active_configs: dict[str, dict[str, Any]] = {}

    def register_federator_data(
        self,
        name: str,
        source: Callable[..., pd.DataFrame] | pd.DataFrame,
    ) -> None:
        """Register a data source from Federator.ai's data layer.

        Typical sources:
        - CrystalClear time-series predictions (workload forecasts)
        - DataProphet resource recommendations (pod/VM right-sizing)
        - Cluster metrics (GPU utilization, memory, network)
        - Cost optimization data (spot vs on-demand, reserved capacity)
        """
        self._skill.register_data(name, source)

    def handle_intent(self, intent: CortexIntent) -> CortexResponse:
        """Handle a parsed intent from Cortex's conversational interface.

        This is the main entry point called by Cortex's agentic orchestration
        when the LLM determines the user wants a dashboard.
        """
        handlers = {
            "generate_dashboard": self._handle_generate,
            "refine_dashboard": self._handle_refine,
            "get_template": self._handle_template,
            "export_code": self._handle_export,
        }

        handler = handlers.get(intent.action)
        if handler is None:
            return CortexResponse(
                status="error",
                artifact_type="error",
                message=f"Unknown action: {intent.action}. Valid actions: {list(handlers.keys())}",
            )

        return handler(intent)

    def get_skill_manifest(self) -> dict[str, Any]:
        """Return the skill manifest for Cortex's agent registry.

        Cortex uses this to understand what the skill can do and route
        intents appropriately.
        """
        return {
            "name": "vizro_genui",
            "version": "0.1.0",
            "description": (
                "Generates interactive, executive-grade dashboards from analytical objectives. "
                "Supports infrastructure monitoring, business analytics, and ADDC operations."
            ),
            "supported_actions": [
                {
                    "action": "generate_dashboard",
                    "description": "Generate a new dashboard from an analytical objective",
                    "required_params": ["objective"],
                    "optional_params": ["datasets", "context"],
                },
                {
                    "action": "refine_dashboard",
                    "description": "Refine an existing dashboard based on user feedback",
                    "required_params": ["objective", "feedback"],
                },
                {
                    "action": "get_template",
                    "description": "Get a pre-built dashboard template",
                    "required_params": ["objective"],
                },
                {
                    "action": "export_code",
                    "description": "Export dashboard config as production Python code",
                    "required_params": ["objective"],
                },
            ],
            "data_requirements": {
                "input_format": "pandas.DataFrame or callable returning DataFrame",
                "supports_dynamic_data": True,
                "supports_time_series": True,
            },
            "capabilities": [
                "structured_output_enforcement",
                "self_correcting_validation",
                "template_based_generation",
                "code_export",
                "resource_aware_visualization",
            ],
        }

    def _handle_generate(self, intent: CortexIntent) -> CortexResponse:
        """Generate a new dashboard."""
        additional_context = json.dumps(intent.context) if intent.context else ""

        result = self._skill.invoke(
            analytical_objective=intent.objective,
            dataset_names=intent.datasets or None,
            additional_context=additional_context,
        )

        if result.is_valid:
            # Store for potential refinement
            config_id = f"dashboard_{len(self._active_configs)}"
            self._active_configs[config_id] = result.config

            return CortexResponse(
                status="success",
                artifact_type="dashboard_config",
                payload={
                    "config_id": config_id,
                    "config": result.config,
                    "python_code": result.python_code,
                },
                message=f"Dashboard '{result.config.get('title', 'Untitled')}' generated successfully.",
                next_actions=["refine_dashboard", "export_code"],
            )
        else:
            return CortexResponse(
                status="validation_failed",
                artifact_type="dashboard_config",
                payload={
                    "config": result.config,
                    "errors": result.errors,
                },
                message=f"Dashboard generation completed with validation issues: {result.errors}",
                next_actions=["generate_dashboard"],
            )

    def _handle_refine(self, intent: CortexIntent) -> CortexResponse:
        """Refine an existing dashboard based on feedback."""
        # Find the most recent config to refine
        if not self._active_configs:
            return CortexResponse(
                status="error",
                artifact_type="error",
                message="No active dashboard to refine. Generate one first.",
                next_actions=["generate_dashboard"],
            )

        config_id = list(self._active_configs.keys())[-1]
        base_config = self._active_configs[config_id]

        # Refinement objective includes the original config context
        refinement_objective = (
            f"Refine the existing dashboard based on this feedback: {intent.feedback}. "
            f"Original objective: {intent.objective}"
        )

        result = self._skill.invoke(
            analytical_objective=refinement_objective,
            dataset_names=intent.datasets or None,
        )

        if result.is_valid:
            self._active_configs[config_id] = result.config
            return CortexResponse(
                status="success",
                artifact_type="dashboard_config",
                payload={
                    "config_id": config_id,
                    "config": result.config,
                    "python_code": result.python_code,
                },
                message="Dashboard refined successfully.",
                next_actions=["refine_dashboard", "export_code"],
            )
        else:
            return CortexResponse(
                status="validation_failed",
                artifact_type="dashboard_config",
                payload={"errors": result.errors},
                message=f"Refinement had validation issues: {result.errors}",
            )

    def _handle_template(self, intent: CortexIntent) -> CortexResponse:
        """Return a pre-built template based on the objective."""
        from vizro_genui.templates.bp_presentation import full_bp_dashboard
        from vizro_genui.templates.addc_operations import addc_operations_dashboard

        # Match objective to template
        objective_lower = intent.objective.lower()
        if any(kw in objective_lower for kw in ["gpu", "cluster", "infrastructure", "addc", "data center"]):
            config = addc_operations_dashboard()
            template_name = "ADDC Operations"
        else:
            config = full_bp_dashboard()
            template_name = "Business Plan"

        code = self._skill.to_code(config)
        config_id = f"template_{len(self._active_configs)}"
        self._active_configs[config_id] = config

        return CortexResponse(
            status="success",
            artifact_type="dashboard_config",
            payload={
                "config_id": config_id,
                "config": config,
                "python_code": code,
                "template_name": template_name,
            },
            message=f"Template '{template_name}' loaded. You can refine it with feedback.",
            next_actions=["refine_dashboard", "export_code"],
        )

    def _handle_export(self, intent: CortexIntent) -> CortexResponse:
        """Export the most recent config as production Python code."""
        if not self._active_configs:
            return CortexResponse(
                status="error",
                artifact_type="error",
                message="No active dashboard to export.",
                next_actions=["generate_dashboard"],
            )

        config_id = list(self._active_configs.keys())[-1]
        config = self._active_configs[config_id]
        code = self._skill.to_code(config)

        return CortexResponse(
            status="success",
            artifact_type="python_code",
            payload={
                "config_id": config_id,
                "python_code": code,
            },
            message="Python code exported. Ready for code review and system incorporation.",
        )
