"""ADDC (AI-Defined Data Center) operations dashboard templates for Federator.ai.

These templates are designed for ProphetStor's Federator.ai DataCenter OS,
providing visibility into GPU utilization, workload predictions, resource
allocation, and cost optimization across clusters.
"""

from __future__ import annotations

from typing import Any


def gpu_utilization_page(
    title: str = "GPU Utilization & Efficiency",
) -> dict[str, Any]:
    """GPU utilization monitoring page.

    Visualizes the core metric that Federator.ai optimizes:
    typical GPU utilization is <30% without proper orchestration.
    """
    return {
        "title": title,
        "components": [
            {
                "type": "Card",
                "text": (
                    "### GPU Fleet Efficiency\n"
                    "Federator.ai optimizes GPU utilization from typical <30% "
                    "to target >70% through AI-driven workload placement."
                ),
            },
            {
                "type": "Graph",
                "chart_function": "line",
                "chart_params": {
                    "x": "timestamp",
                    "y": "gpu_utilization_pct",
                    "color": "cluster_id",
                },
                "title": "GPU Utilization Over Time",
            },
            {
                "type": "Graph",
                "chart_function": "bar",
                "chart_params": {
                    "x": "gpu_model",
                    "y": "utilization_pct",
                    "color": "cluster_id",
                    "barmode": "group",
                },
                "title": "Utilization by GPU Model (H100 / B200 / GB200)",
            },
            {
                "type": "Graph",
                "chart_function": "heatmap",
                "chart_params": {
                    "x": "hour_of_day",
                    "y": "day_of_week",
                    "z": "avg_utilization",
                },
                "title": "Utilization Heatmap (Time Patterns)",
            },
        ],
        "controls": [
            {"type": "filter", "column": "cluster_id"},
            {"type": "filter", "column": "gpu_model"},
        ],
        "layout": {
            "type": "grid",
            "grid": [[0, 0, 1, 1], [2, 2, 3, 3]],
        },
    }


def workload_prediction_page(
    title: str = "Workload Prediction (CrystalClear)",
) -> dict[str, Any]:
    """Workload prediction page powered by Federator.ai's CrystalClear engine.

    Shows predicted vs actual workload, enabling just-in-time resource allocation.
    """
    return {
        "title": title,
        "components": [
            {
                "type": "Graph",
                "chart_function": "line",
                "chart_params": {
                    "x": "timestamp",
                    "y": "workload_actual",
                    "color": "metric_type",
                },
                "title": "Predicted vs Actual Workload",
            },
            {
                "type": "Graph",
                "chart_function": "area",
                "chart_params": {
                    "x": "timestamp",
                    "y": "resource_allocated",
                    "color": "resource_type",
                },
                "title": "Resource Allocation Over Time",
            },
            {
                "type": "Card",
                "text": (
                    "### CrystalClear Engine\n"
                    "AI-based prediction models analyze live time-series data "
                    "to provide just-in-time fitted resource recommendations."
                ),
            },
        ],
        "controls": [
            {"type": "filter", "column": "namespace"},
            {"type": "filter", "column": "resource_type"},
        ],
        "layout": {"type": "grid", "grid": [[0, 1], [0, 2]]},
    }


def cost_optimization_page(
    title: str = "Cost Optimization (DataProphet)",
) -> dict[str, Any]:
    """Cost optimization dashboard powered by Federator.ai's DataProphet engine.

    Shows right-sizing recommendations, spot vs on-demand analysis,
    and projected savings.
    """
    return {
        "title": title,
        "components": [
            {
                "type": "Graph",
                "chart_function": "bar",
                "chart_params": {
                    "x": "resource_name",
                    "y": "cost_usd",
                    "color": "cost_type",
                    "barmode": "group",
                },
                "title": "Current vs Recommended Cost",
            },
            {
                "type": "Graph",
                "chart_function": "funnel",
                "chart_params": {
                    "x": "savings_usd",
                    "y": "optimization_category",
                },
                "title": "Savings Opportunity Funnel",
            },
            {
                "type": "Graph",
                "chart_function": "pie",
                "chart_params": {
                    "values": "cost_usd",
                    "names": "resource_type",
                },
                "title": "Cost Distribution by Resource Type",
            },
        ],
        "controls": [
            {"type": "filter", "column": "cluster_id"},
            {"type": "filter", "column": "environment"},
        ],
    }


def compute_marketplace_page(
    title: str = "Global AI Compute Marketplace",
) -> dict[str, Any]:
    """ADDC.ai Global Compute Marketplace dashboard.

    Federate capacity across sites, optimize workload placement,
    enable compute trading.
    """
    return {
        "title": title,
        "components": [
            {
                "type": "Card",
                "text": (
                    "### Compute Marketplace\n"
                    "Federate GPU capacity across data center sites. "
                    "Optimize workload placement and enable compute trading."
                ),
            },
            {
                "type": "Graph",
                "chart_function": "scatter",
                "chart_params": {
                    "x": "available_capacity_gpu_hours",
                    "y": "price_per_gpu_hour",
                    "color": "site_location",
                    "size": "total_gpus",
                },
                "title": "Capacity vs Price by Site",
            },
            {
                "type": "Graph",
                "chart_function": "bar",
                "chart_params": {
                    "x": "site_location",
                    "y": "gpu_count",
                    "color": "gpu_generation",
                    "barmode": "stack",
                },
                "title": "GPU Fleet Composition by Site",
            },
        ],
        "controls": [
            {"type": "filter", "column": "site_location"},
            {"type": "filter", "column": "gpu_generation"},
        ],
    }


def addc_operations_dashboard(
    dashboard_title: str = "Federator.ai ADDC Operations",
    theme: str = "vizro_dark",
) -> dict[str, Any]:
    """Complete ADDC operations dashboard with all pages."""
    return {
        "title": dashboard_title,
        "theme": theme,
        "pages": [
            gpu_utilization_page(),
            workload_prediction_page(),
            cost_optimization_page(),
            compute_marketplace_page(),
        ],
    }
