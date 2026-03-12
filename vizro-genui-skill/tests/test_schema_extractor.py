"""Tests for schema extraction and constraint logic."""

import pytest


class TestExtractVizroSchema:
    def test_extracts_valid_json_schema(self):
        from vizro_genui.schema.extractor import extract_vizro_schema

        schema = extract_vizro_schema()
        assert isinstance(schema, dict)
        assert "$defs" in schema or "properties" in schema

    def test_schema_contains_page_definition(self):
        from vizro_genui.schema.extractor import extract_vizro_schema

        schema = extract_vizro_schema()
        defs = schema.get("$defs", {})
        assert "Page" in defs

    def test_schema_has_pages_property(self):
        from vizro_genui.schema.extractor import extract_vizro_schema

        schema = extract_vizro_schema()
        assert "pages" in schema.get("properties", {})


class TestGetConstrainedSchema:
    def test_max_pages_applied(self):
        from vizro_genui.schema.extractor import get_constrained_schema

        schema = get_constrained_schema(max_pages=3)
        pages_prop = schema.get("properties", {}).get("pages", {})
        assert pages_prop.get("maxItems") == 3

    def test_filter_components(self):
        from vizro_genui.schema.extractor import get_constrained_schema

        schema = get_constrained_schema(include_components=["Graph", "Card"])
        defs = schema.get("$defs", {})
        # Table should be removed
        assert "Table" not in defs
        # AgGrid should be removed
        assert "AgGrid" not in defs


class TestSchemaToToolDefinition:
    def test_returns_valid_tool_format(self):
        from vizro_genui.schema.extractor import schema_to_tool_definition

        tool = schema_to_tool_definition()
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool
        assert tool["name"] == "generate_vizro_dashboard"


class TestChartRegistry:
    def test_chart_descriptions_not_empty(self):
        from vizro_genui.schema.chart_registry import get_chart_descriptions

        desc = get_chart_descriptions()
        assert len(desc) > 0
        assert "scatter" in desc
        assert "bar" in desc

    def test_validate_valid_chart(self):
        from vizro_genui.schema.chart_registry import validate_chart_reference

        errors = validate_chart_reference("bar", {"x": "col1", "y": "col2"})
        assert errors == []

    def test_validate_unknown_chart(self):
        from vizro_genui.schema.chart_registry import validate_chart_reference

        errors = validate_chart_reference("nonexistent_chart", {})
        assert len(errors) > 0
        assert "Unknown chart type" in errors[0]

    def test_validate_missing_required_param(self):
        from vizro_genui.schema.chart_registry import validate_chart_reference

        errors = validate_chart_reference("scatter", {"x": "col1"})
        assert any("y" in e for e in errors)
