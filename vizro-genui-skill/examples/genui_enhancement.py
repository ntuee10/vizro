"""How to leverage the Vizro GenUI skill to enhance Federator.ai's UI and GenUI.

Three strategies for incorporating Vizro into the system:

Strategy 1: GenUI Streaming (Conversational Dashboard Generation)
    User speaks -> Cortex understands intent -> Skill generates config -> Dashboard appears

Strategy 2: Component Library Enhancement (Embed Vizro charts in existing UI)
    Existing Federator.ai UI -> Inject Vizro-generated Plotly specs -> Richer visualizations

Strategy 3: Full System Integration (Production dashboards in the platform)
    Generated code -> Code review -> Merge into Federator.ai codebase -> Permanent feature
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd


# =============================================================================
# STRATEGY 1: GenUI Streaming
# =============================================================================
# The conversational interface generates dashboards on-the-fly.
# This is the "magic" experience - user asks, dashboard appears.

class GenUIStreamHandler:
    """Handles the GenUI streaming flow for Federator.ai's conversational interface.

    Flow:
    1. User types: "Show me GPU utilization trends"
    2. Cortex LLM parses intent -> routes to VizroGenUISkill
    3. Skill generates validated config
    4. This handler streams the result to the frontend
    5. Frontend renders the dashboard (iframe or component mapping)
    """

    def __init__(self, adapter):
        self.adapter = adapter

    def stream_dashboard(self, user_message: str, data_context: dict[str, Any]) -> dict[str, Any]:
        """Process a user message and stream back a dashboard.

        Returns a GenUI response payload that the frontend knows how to render.
        """
        from vizro_genui import CortexIntent

        # Parse the user message into an intent
        intent = CortexIntent(
            action="generate_dashboard",
            objective=user_message,
            datasets=list(data_context.keys()),
        )

        # Register any provided data
        for name, df in data_context.items():
            self.adapter.register_federator_data(name, df)

        # Generate
        response = self.adapter.handle_intent(intent)

        if response.status == "success":
            config = response.payload["config"]

            # Return GenUI-compatible response
            return {
                "type": "genui_dashboard",
                "render_mode": "vizro",  # Frontend knows to use Vizro renderer
                "config": config,
                "plotly_specs": self._extract_plotly_specs(config),
                "message": response.message,
            }
        else:
            return {
                "type": "genui_error",
                "message": response.message,
                "fallback": "I couldn't generate a dashboard. Could you be more specific?",
            }

    def _extract_plotly_specs(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract individual Plotly chart specs from the config.

        This enables Pattern B (component-level GenUI) where the frontend
        renders each chart independently using react-plotly.js instead of
        a full Vizro/Dash backend.
        """
        specs = []
        for page in config.get("pages", []):
            for comp in page.get("components", []):
                if comp.get("type") == "Graph":
                    specs.append({
                        "chart_function": comp.get("chart_function"),
                        "chart_params": comp.get("chart_params", {}),
                        "title": comp.get("title", ""),
                        "page": page.get("title", ""),
                    })
        return specs


# =============================================================================
# STRATEGY 2: Component Library Enhancement
# =============================================================================
# Inject Vizro-quality charts into the existing Federator.ai UI
# without replacing the entire frontend.

class VizroComponentEnhancer:
    """Enhances existing Federator.ai UI components with Vizro-quality charts.

    Instead of generating full dashboards, this generates individual chart
    specifications that can be embedded in the existing UI.
    """

    @staticmethod
    def generate_chart_spec(
        chart_type: str,
        data: pd.DataFrame,
        x: str,
        y: str,
        color: str | None = None,
        title: str = "",
    ) -> dict[str, Any]:
        """Generate a single Plotly chart spec using Vizro's styling.

        The returned spec can be passed directly to react-plotly.js
        or any Plotly renderer in the Federator.ai frontend.
        """
        import vizro.plotly.express as px

        chart_func = getattr(px, chart_type, px.bar)
        kwargs = {"data_frame": data, "x": x, "y": y}
        if color:
            kwargs["color"] = color
        if title:
            kwargs["title"] = title

        fig = chart_func(**kwargs)

        # Return the Plotly JSON spec for frontend rendering
        return json.loads(fig.to_json())

    @staticmethod
    def apply_vizro_theme(plotly_spec: dict[str, Any], theme: str = "vizro_dark") -> dict[str, Any]:
        """Apply Vizro's professional theme to any Plotly chart spec.

        Use this to upgrade existing charts in the Federator.ai UI
        to McKinsey-grade styling without changing the data logic.
        """
        from vizro._themes import dark_theme, light_theme

        template = dark_theme if theme == "vizro_dark" else light_theme
        plotly_spec.setdefault("layout", {})
        plotly_spec["layout"]["template"] = template

        return plotly_spec

    @staticmethod
    def generate_kpi_card(
        metric_name: str,
        value: float | str,
        trend: str = "",
        description: str = "",
    ) -> dict[str, Any]:
        """Generate a KPI card spec for the Federator.ai UI.

        Returns structured data that the frontend renders as a KPI card.
        """
        return {
            "type": "kpi_card",
            "metric_name": metric_name,
            "value": str(value),
            "trend": trend,
            "description": description,
            "vizro_markdown": (
                f"### {metric_name}\n"
                f"# {value}\n"
                f"{trend}\n\n"
                f"{description}"
            ),
        }


# =============================================================================
# STRATEGY 3: Full System Integration
# =============================================================================
# Generate production-ready code for permanent Federator.ai features.

class SystemIntegrator:
    """Generates production-ready Vizro dashboard code for the Federator.ai system.

    Use this when you want to add permanent dashboard features to the platform,
    not ad-hoc GenUI responses.
    """

    @staticmethod
    def generate_production_module(
        config: dict[str, Any],
        module_name: str = "dashboard",
        data_loader_module: str = "federator_data",
    ) -> str:
        """Generate a complete, production-ready Python module.

        The output is a self-contained module that:
        - Imports from Federator.ai's data layer
        - Creates a Vizro dashboard
        - Can be served as a standalone app or mounted in Federator.ai's web layer
        """
        from vizro_genui.rendering.builder import config_to_python_code

        base_code = config_to_python_code(config)

        # Wrap with production-grade imports and data loading
        production_code = f'''"""Production dashboard module for Federator.ai.

Auto-generated by Vizro GenUI Skill. Reviewed and approved for production.
"""

from {data_loader_module} import load_data, get_data_manager

{base_code}
'''
        return production_code

    @staticmethod
    def generate_api_endpoint(
        config: dict[str, Any],
        route: str = "/api/v1/dashboards/generated",
    ) -> str:
        """Generate a FastAPI/Flask endpoint that serves the dashboard.

        This mounts the Vizro dashboard within Federator.ai's web server.
        """
        import json
        config_str = json.dumps(config, indent=4)

        return f'''"""API endpoint for serving generated Vizro dashboards.

Mount this in Federator.ai's ASGI/WSGI server.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

DASHBOARD_CONFIG = {config_str}


@router.get("{route}/config")
async def get_dashboard_config():
    """Return the dashboard configuration for frontend rendering."""
    return JSONResponse(content=DASHBOARD_CONFIG)


@router.post("{route}/generate")
async def generate_dashboard(objective: str):
    """Generate a new dashboard from an analytical objective.

    This endpoint is called by the Federator.ai GenUI frontend
    when a user requests a dashboard via the conversational interface.
    """
    from vizro_genui import VizroGenUISkill

    skill = VizroGenUISkill()
    result = skill.invoke(analytical_objective=objective)
    return JSONResponse(content={{
        "config": result.config,
        "python_code": result.python_code,
        "is_valid": result.is_valid,
        "errors": result.errors,
    }})
'''


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("=== Strategy 1: GenUI Streaming ===")
    print("Requires CortexSkillAdapter + API key. See activate_in_cortex.py")
    print()

    print("=== Strategy 2: Component Enhancement ===")
    sample_data = pd.DataFrame({
        "hour": list(range(24)),
        "gpu_util": [20 + i * 2.5 for i in range(24)],
        "cluster": ["A"] * 12 + ["B"] * 12,
    })

    enhancer = VizroComponentEnhancer()
    kpi = enhancer.generate_kpi_card(
        metric_name="Avg GPU Utilization",
        value="67.3%",
        trend="+12.5% vs last week",
        description="Across 3 clusters, 240 GPUs",
    )
    print(f"KPI Card:\n{json.dumps(kpi, indent=2)}\n")

    print("=== Strategy 3: System Integration ===")
    config = {
        "title": "Federator.ai GPU Monitor",
        "theme": "vizro_dark",
        "pages": [{
            "title": "GPU Overview",
            "components": [
                {"type": "Card", "text": "### Fleet Health\nAll clusters operational."},
                {
                    "type": "Graph",
                    "chart_function": "line",
                    "chart_params": {"x": "timestamp", "y": "gpu_utilization_pct"},
                    "title": "Utilization Trend",
                },
            ],
        }],
    }

    integrator = SystemIntegrator()
    api_code = integrator.generate_api_endpoint(config)
    print("Generated API endpoint:")
    print(api_code[:500] + "...\n")
