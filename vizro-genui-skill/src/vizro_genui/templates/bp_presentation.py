"""Pre-built templates for Business Plan (BP) presentation dashboards.

These templates encode McKinsey-grade layout patterns that the GenUI skill
can use as starting points, reducing LLM hallucination risk.
"""

from __future__ import annotations

from typing import Any


def executive_summary_template(
    title: str = "Executive Summary",
    kpi_texts: list[str] | None = None,
    trend_chart: dict[str, Any] | None = None,
    breakdown_chart: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a standard executive summary page config.

    Layout: Top row = KPI cards, Bottom = trend line + breakdown bar chart.
    """
    components = []

    # KPI cards across the top
    for i, text in enumerate(kpi_texts or ["KPI 1", "KPI 2", "KPI 3"]):
        components.append({"type": "Card", "text": text})

    # Trend chart
    if trend_chart:
        components.append({"type": "Graph", **trend_chart})
    else:
        components.append({
            "type": "Graph",
            "chart_function": "line",
            "chart_params": {"x": "date", "y": "value"},
            "title": "Trend Over Time",
        })

    # Breakdown chart
    if breakdown_chart:
        components.append({"type": "Graph", **breakdown_chart})
    else:
        components.append({
            "type": "Graph",
            "chart_function": "bar",
            "chart_params": {"x": "category", "y": "value"},
            "title": "Breakdown by Category",
        })

    n_kpis = len(kpi_texts or ["KPI 1", "KPI 2", "KPI 3"])

    # Grid: KPIs in top row, charts in bottom row
    grid = []
    grid.append(list(range(n_kpis)))
    chart_row = [n_kpis, n_kpis + 1] if n_kpis <= 2 else [n_kpis] * (n_kpis // 2) + [n_kpis + 1] * (n_kpis - n_kpis // 2)
    grid.append(chart_row)

    return {
        "title": title,
        "components": components,
        "layout": {"type": "grid", "grid": grid},
    }


def quarterly_review_template(
    title: str = "Quarterly Review",
    metrics: list[str] | None = None,
    filter_columns: list[str] | None = None,
) -> dict[str, Any]:
    """Standard quarterly review page with metrics comparison and filters."""
    metrics = metrics or ["revenue", "costs", "margin"]

    components = []
    for metric in metrics:
        components.append({
            "type": "Graph",
            "chart_function": "bar",
            "chart_params": {"x": "quarter", "y": metric, "color": "region"},
            "title": f"{metric.replace('_', ' ').title()} by Quarter",
        })

    controls = []
    for col in (filter_columns or ["region"]):
        controls.append({"type": "filter", "column": col})

    return {
        "title": title,
        "components": components,
        "controls": controls,
    }


def pipeline_funnel_template(
    title: str = "Pipeline Analysis",
    stages: list[str] | None = None,
) -> dict[str, Any]:
    """Pipeline/funnel analysis page for sales or project tracking."""
    components = [
        {
            "type": "Graph",
            "chart_function": "funnel",
            "chart_params": {"x": "count", "y": "stage"},
            "title": "Pipeline Funnel",
        },
        {
            "type": "Graph",
            "chart_function": "bar",
            "chart_params": {"x": "stage", "y": "value", "color": "status"},
            "title": "Value by Stage",
        },
    ]

    return {
        "title": title,
        "components": components,
        "controls": [{"type": "filter", "column": "status"}],
        "layout": {"type": "grid", "grid": [[0], [1]]},
    }


def full_bp_dashboard(
    dashboard_title: str = "Business Plan Dashboard",
    theme: str = "vizro_dark",
) -> dict[str, Any]:
    """Assemble a complete BP dashboard from standard templates."""
    return {
        "title": dashboard_title,
        "theme": theme,
        "pages": [
            executive_summary_template(),
            quarterly_review_template(),
            pipeline_funnel_template(),
        ],
    }
