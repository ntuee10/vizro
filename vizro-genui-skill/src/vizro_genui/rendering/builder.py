"""Build and render Vizro dashboards from LLM-generated configurations.

This module takes the JSON config produced by the GenUI skill and materializes
it into a running Vizro application. It handles:
- Config validation against Vizro's Pydantic models
- Data binding (connecting dataset references to actual data)
- Dashboard instantiation and serving
"""

from __future__ import annotations

import uuid
from typing import Any, Callable

import pandas as pd


def validate_config(config: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a dashboard configuration against Vizro's Pydantic models.

    Returns (is_valid, list_of_errors).
    """
    errors = []

    if "pages" not in config:
        errors.append("Dashboard config must contain 'pages'")
        return False, errors

    if not isinstance(config["pages"], list) or len(config["pages"]) == 0:
        errors.append("'pages' must be a non-empty list")
        return False, errors

    for i, page in enumerate(config["pages"]):
        if "title" not in page:
            errors.append(f"Page {i} missing required field 'title'")
        if "components" not in page:
            errors.append(f"Page {i} missing required field 'components'")
        elif not isinstance(page["components"], list) or len(page["components"]) == 0:
            errors.append(f"Page {i} 'components' must be a non-empty list")

    if errors:
        return False, errors

    # Deep validation via Pydantic
    try:
        _config_to_dashboard(config)
    except Exception as e:
        errors.append(f"Pydantic validation failed: {e}")
        return False, errors

    return True, []


def build_dashboard_from_config(
    config: dict[str, Any],
    data_sources: dict[str, Callable[..., pd.DataFrame] | pd.DataFrame] | None = None,
    theme: str = "vizro_dark",
) -> Any:
    """Build a Vizro Dashboard object from a validated config.

    Args:
        config: The LLM-generated dashboard configuration dict.
        data_sources: Mapping of dataset names to DataFrames or callables
            that return DataFrames. These get registered with Vizro's data_manager.
        theme: Dashboard theme ("vizro_dark" or "vizro_light").

    Returns:
        A built Vizro application ready to run.
    """
    from vizro import Vizro
    from vizro.managers import data_manager

    # Register data sources
    if data_sources:
        for name, source in data_sources.items():
            if callable(source):
                data_manager[name] = source
            else:
                data_manager[name] = lambda df=source: df

    # Override theme if specified
    if "theme" not in config:
        config["theme"] = theme

    dashboard = _config_to_dashboard(config)
    app = Vizro().build(dashboard)
    return app


def build_and_serve(
    config: dict[str, Any],
    data_sources: dict[str, Callable[..., pd.DataFrame] | pd.DataFrame] | None = None,
    host: str = "0.0.0.0",
    port: int = 8050,
) -> str:
    """Build the dashboard and start serving it. Returns the URL.

    This is the Pattern A approach: backend dashboard generator.
    The Cortex agent calls this, gets back a URL to embed in the GenUI frontend.
    """
    app = build_dashboard_from_config(config, data_sources)
    app_id = str(uuid.uuid4())[:8]
    url = f"http://{host}:{port}/{app_id}"

    # In production, mount to an ASGI server at the dynamic route.
    # For development, run directly:
    app.run(host=host, port=port)
    return url


def config_to_python_code(config: dict[str, Any]) -> str:
    """Convert a dashboard config to executable Python code.

    This is useful for Pattern B: when you want to incorporate the generated
    dashboard code directly into the system rather than serving dynamically.
    Produces clean, McKinsey-grade code ready for code review.
    """
    lines = [
        '"""Auto-generated Vizro dashboard from GenUI skill."""',
        "",
        "import vizro.models as vm",
        "import vizro.plotly.express as px",
        "from vizro import Vizro",
        "",
    ]

    # Generate page definitions
    for i, page in enumerate(config.get("pages", [])):
        page_var = f"page_{i}"
        lines.append(f"{page_var} = vm.Page(")
        lines.append(f'    title="{page["title"]}",')

        # Components
        lines.append("    components=[")
        for comp in page.get("components", []):
            comp_type = comp.get("type", "Card")
            lines.append(f"        {_component_to_code(comp_type, comp)},")
        lines.append("    ],")

        # Controls
        controls = page.get("controls", [])
        if controls:
            lines.append("    controls=[")
            for ctrl in controls:
                lines.append(f"        {_control_to_code(ctrl)},")
            lines.append("    ],")

        # Layout
        layout = page.get("layout")
        if layout:
            lines.append(f"    layout={_layout_to_code(layout)},")

        lines.append(")")
        lines.append("")

    # Generate dashboard
    page_vars = ", ".join(f"page_{i}" for i in range(len(config.get("pages", []))))
    theme = config.get("theme", "vizro_dark")
    title = config.get("title", "")

    lines.append("dashboard = vm.Dashboard(")
    lines.append(f"    pages=[{page_vars}],")
    if title:
        lines.append(f'    title="{title}",')
    lines.append(f'    theme="{theme}",')
    lines.append(")")
    lines.append("")
    lines.append('if __name__ == "__main__":')
    lines.append("    Vizro().build(dashboard).run()")
    lines.append("")

    return "\n".join(lines)


def _config_to_dashboard(config: dict[str, Any]) -> Any:
    """Instantiate a Vizro Dashboard from a config dict.

    This relies on Vizro's Pydantic models to parse and validate.
    For the figure fields in Graph components, we need to resolve
    the chart function references to actual callables.
    """
    import vizro.models as vm
    import vizro.plotly.express as px

    pages = []
    for page_config in config["pages"]:
        components = []
        for comp in page_config.get("components", []):
            components.append(_resolve_component(comp, px))

        controls = []
        for ctrl in page_config.get("controls", []):
            controls.append(_resolve_control(ctrl))

        layout = None
        if "layout" in page_config and page_config["layout"] is not None:
            layout = _resolve_layout(page_config["layout"])

        page = vm.Page(
            title=page_config["title"],
            components=components,
            controls=controls,
            **({"layout": layout} if layout else {}),
        )
        pages.append(page)

    dashboard_kwargs: dict[str, Any] = {"pages": pages}
    if "theme" in config:
        dashboard_kwargs["theme"] = config["theme"]
    if "title" in config:
        dashboard_kwargs["title"] = config["title"]

    return vm.Dashboard(**dashboard_kwargs)


def _resolve_component(comp: dict[str, Any], px_module: Any) -> Any:
    """Resolve a component config dict to a Vizro component model instance."""
    import vizro.models as vm

    comp_type = comp.get("type", "Card")

    if comp_type == "Graph":
        chart_func_name = comp.get("chart_function", "bar")
        chart_params = comp.get("chart_params", {})
        chart_func = getattr(px_module, chart_func_name, px_module.bar)
        figure = chart_func(**chart_params)
        return vm.Graph(
            figure=figure,
            title=comp.get("title", ""),
        )
    elif comp_type == "Card":
        return vm.Card(text=comp.get("text", ""))
    elif comp_type == "Table":
        return vm.Table(
            title=comp.get("title", ""),
            figure=comp.get("figure"),
        )
    elif comp_type == "Text":
        return vm.Text(text=comp.get("text", ""))
    else:
        # Fallback to Card
        return vm.Card(text=comp.get("text", str(comp)))


def _resolve_control(ctrl: dict[str, Any]) -> Any:
    """Resolve a control config dict to a Vizro control model instance."""
    import vizro.models as vm

    ctrl_type = ctrl.get("type", "filter")

    if ctrl_type == "filter":
        return vm.Filter(
            column=ctrl["column"],
            targets=ctrl.get("targets", []),
        )
    elif ctrl_type == "parameter":
        return vm.Parameter(
            targets=ctrl["targets"],
            selector=ctrl.get("selector"),
        )
    else:
        return vm.Filter(column=ctrl.get("column", ""))


def _resolve_layout(layout_config: dict[str, Any]) -> Any:
    """Resolve a layout config to a Vizro layout model."""
    import vizro.models as vm

    layout_type = layout_config.get("type", "grid")

    if layout_type == "flex":
        return vm.Flex(
            direction=layout_config.get("direction", "column"),
            wrap=layout_config.get("wrap", False),
        )
    else:
        grid = layout_config.get("grid")
        if grid:
            return vm.Grid(grid=grid)
        return None


def _component_to_code(comp_type: str, comp: dict[str, Any]) -> str:
    """Convert a component config to Python code string."""
    if comp_type == "Graph":
        func = comp.get("chart_function", "bar")
        params = comp.get("chart_params", {})
        param_str = ", ".join(f'{k}="{v}"' if isinstance(v, str) else f"{k}={v}" for k, v in params.items())
        title = comp.get("title", "")
        parts = [f'vm.Graph(figure=px.{func}({param_str})']
        if title:
            parts[0] += f', title="{title}"'
        return parts[0] + ")"
    elif comp_type == "Card":
        return f'vm.Card(text="""{comp.get("text", "")}""")'
    elif comp_type == "Text":
        return f'vm.Text(text="""{comp.get("text", "")}""")'
    else:
        return f'vm.Card(text="{comp_type} component")'


def _control_to_code(ctrl: dict[str, Any]) -> str:
    """Convert a control config to Python code string."""
    ctrl_type = ctrl.get("type", "filter")
    if ctrl_type == "filter":
        return f'vm.Filter(column="{ctrl["column"]}")'
    return f"vm.Filter(column=\"{ctrl.get('column', '')}\")"


def _layout_to_code(layout: dict[str, Any]) -> str:
    """Convert a layout config to Python code string."""
    layout_type = layout.get("type", "grid")
    if layout_type == "flex":
        direction = layout.get("direction", "column")
        return f'vm.Flex(direction="{direction}")'
    grid = layout.get("grid")
    if grid:
        return f"vm.Grid(grid={grid})"
    return "vm.Flex()"
