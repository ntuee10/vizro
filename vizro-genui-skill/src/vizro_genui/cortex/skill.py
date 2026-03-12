"""Vizro GenUI Skill for Federator.ai Cortex.

This is the main skill class that an agent in the Cortex framework invokes.
It orchestrates:
1. Schema extraction for strict output enforcement
2. Prompt construction with data context
3. LLM invocation with structured output
4. Config validation and dashboard materialization

Architecture:
    Cortex Agent -> VizroGenUISkill.invoke() -> LLM (structured output) -> Vizro Config -> Dashboard
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

import pandas as pd

from vizro_genui.schema.chart_registry import get_chart_descriptions
from vizro_genui.schema.extractor import get_constrained_schema, schema_to_tool_definition
from vizro_genui.rendering.builder import (
    build_dashboard_from_config,
    config_to_python_code,
    validate_config,
)
from vizro_genui.cortex.prompts import (
    build_system_prompt,
    build_generation_prompt,
)


@dataclass
class SkillResult:
    """Result returned by the VizroGenUISkill."""

    config: dict[str, Any]
    """The validated Vizro dashboard configuration."""

    python_code: str
    """Executable Python code for the dashboard."""

    is_valid: bool
    """Whether the config passed validation."""

    errors: list[str] = field(default_factory=list)
    """Validation errors, if any."""

    dashboard_url: str | None = None
    """URL of the served dashboard, if Pattern A was used."""


class VizroGenUISkill:
    """GenUI skill that generates McKinsey-grade Vizro dashboards.

    Usage in Federator.ai Cortex:

        skill = VizroGenUISkill()

        # Register your datasets
        skill.register_data("sales", sales_df)
        skill.register_data("pipeline", load_pipeline_data)

        # Generate a dashboard
        result = skill.invoke(
            analytical_objective="Show quarterly sales trends by region with drill-down filters",
            dataset_names=["sales"],
        )

        # Get the executable code for incorporation into the system
        print(result.python_code)

        # Or build and serve directly
        app = skill.build(result.config)
    """

    def __init__(
        self,
        llm_client: Any = None,
        model: str = "claude-sonnet-4-20250514",
        max_pages: int = 5,
        theme: str = "vizro_dark",
        allowed_components: list[str] | None = None,
        allowed_controls: list[str] | None = None,
    ):
        """Initialize the skill.

        Args:
            llm_client: An Anthropic client instance. If None, creates one from ANTHROPIC_API_KEY.
            model: The Claude model to use for generation.
            max_pages: Maximum pages allowed in generated dashboards.
            theme: Default Vizro theme.
            allowed_components: Whitelist of component types. None = all.
            allowed_controls: Whitelist of control types. None = all.
        """
        self._llm_client = llm_client
        self._model = model
        self._max_pages = max_pages
        self._theme = theme
        self._allowed_components = allowed_components
        self._allowed_controls = allowed_controls
        self._data_sources: dict[str, Callable[..., pd.DataFrame] | pd.DataFrame] = {}
        self._data_schemas: dict[str, dict[str, str]] = {}

    def register_data(
        self,
        name: str,
        source: Callable[..., pd.DataFrame] | pd.DataFrame,
    ) -> None:
        """Register a dataset for use in dashboard generation.

        Args:
            name: Identifier for this dataset (referenced in the config).
            source: A DataFrame or callable that returns one.
        """
        self._data_sources[name] = source

        # Extract schema for the LLM prompt
        if isinstance(source, pd.DataFrame):
            df = source
        else:
            df = source()

        self._data_schemas[name] = {
            col: str(dtype) for col, dtype in df.dtypes.items()
        }

    def invoke(
        self,
        analytical_objective: str,
        dataset_names: list[str] | None = None,
        additional_context: str = "",
        max_retries: int = 2,
    ) -> SkillResult:
        """Generate a Vizro dashboard configuration from an analytical objective.

        This is the main entry point called by the Cortex agent.

        Args:
            analytical_objective: What the dashboard should show/answer.
            dataset_names: Which registered datasets to use. None = all.
            additional_context: Extra instructions (e.g., "use McKinsey blue palette").
            max_retries: Number of retries on validation failure.

        Returns:
            SkillResult with the validated config and executable code.
        """
        client = self._get_client()
        datasets = dataset_names or list(self._data_sources.keys())
        data_context = {name: self._data_schemas[name] for name in datasets if name in self._data_schemas}

        tool_def = schema_to_tool_definition()
        system_prompt = build_system_prompt(
            chart_descriptions=get_chart_descriptions(),
            theme=self._theme,
        )
        user_prompt = build_generation_prompt(
            analytical_objective=analytical_objective,
            data_schemas=data_context,
            additional_context=additional_context,
        )

        for attempt in range(max_retries + 1):
            config = self._call_llm(client, system_prompt, user_prompt, tool_def)

            is_valid, errors = validate_config(config)
            if is_valid:
                python_code = config_to_python_code(config)
                return SkillResult(
                    config=config,
                    python_code=python_code,
                    is_valid=True,
                )

            # On failure, append errors to prompt for self-correction
            user_prompt += (
                f"\n\nPrevious attempt failed validation with errors: {errors}. "
                "Please fix the configuration."
            )

        # Return best-effort result with errors
        python_code = config_to_python_code(config)
        return SkillResult(
            config=config,
            python_code=python_code,
            is_valid=False,
            errors=errors,
        )

    def build(
        self,
        config: dict[str, Any],
        theme: str | None = None,
    ) -> Any:
        """Build a Vizro app from a config. Returns the app object.

        Use this when you want to serve the dashboard (Pattern A).
        """
        return build_dashboard_from_config(
            config=config,
            data_sources=self._data_sources,
            theme=theme or self._theme,
        )

    def to_code(self, config: dict[str, Any]) -> str:
        """Convert config to executable Python code (Pattern B).

        Use this when incorporating the dashboard into the system codebase.
        """
        return config_to_python_code(config)

    def _get_client(self) -> Any:
        """Get or create the Anthropic client."""
        if self._llm_client is not None:
            return self._llm_client

        try:
            from anthropic import Anthropic
            self._llm_client = Anthropic()
            return self._llm_client
        except ImportError:
            raise ImportError(
                "anthropic package is required. Install with: pip install vizro-genui-skill[cortex]"
            )

    def _call_llm(
        self,
        client: Any,
        system_prompt: str,
        user_prompt: str,
        tool_def: dict[str, Any],
    ) -> dict[str, Any]:
        """Call Claude with structured output to get a Vizro config."""
        response = client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system_prompt,
            tools=[tool_def],
            tool_choice={"type": "tool", "name": tool_def["name"]},
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Extract the tool use result
        for block in response.content:
            if block.type == "tool_use":
                return block.input

        raise RuntimeError("LLM did not return a tool_use block with dashboard config")
