"""Tests for the rendering/builder module."""

import pytest


class TestValidateConfig:
    def test_valid_minimal_config(self):
        from vizro_genui.rendering.builder import validate_config

        config = {
            "pages": [
                {
                    "title": "Test Page",
                    "components": [{"type": "Card", "text": "Hello"}],
                }
            ]
        }
        is_valid, errors = validate_config(config)
        assert is_valid
        assert errors == []

    def test_missing_pages(self):
        from vizro_genui.rendering.builder import validate_config

        is_valid, errors = validate_config({})
        assert not is_valid
        assert any("pages" in e for e in errors)

    def test_empty_pages(self):
        from vizro_genui.rendering.builder import validate_config

        is_valid, errors = validate_config({"pages": []})
        assert not is_valid

    def test_page_missing_title(self):
        from vizro_genui.rendering.builder import validate_config

        config = {
            "pages": [{"components": [{"type": "Card", "text": "Hi"}]}]
        }
        is_valid, errors = validate_config(config)
        assert not is_valid
        assert any("title" in e for e in errors)

    def test_page_missing_components(self):
        from vizro_genui.rendering.builder import validate_config

        config = {
            "pages": [{"title": "Test"}]
        }
        is_valid, errors = validate_config(config)
        assert not is_valid
        assert any("components" in e for e in errors)


class TestConfigToPythonCode:
    def test_generates_valid_python(self):
        from vizro_genui.rendering.builder import config_to_python_code

        config = {
            "title": "Test Dashboard",
            "theme": "vizro_dark",
            "pages": [
                {
                    "title": "Overview",
                    "components": [
                        {"type": "Card", "text": "Welcome to the dashboard"},
                        {
                            "type": "Graph",
                            "chart_function": "bar",
                            "chart_params": {"x": "category", "y": "value"},
                            "title": "Sales",
                        },
                    ],
                    "controls": [{"type": "filter", "column": "region"}],
                }
            ],
        }

        code = config_to_python_code(config)
        assert "import vizro.models as vm" in code
        assert "import vizro.plotly.express as px" in code
        assert "vm.Dashboard" in code
        assert "vm.Page" in code
        assert "vm.Graph" in code
        assert "vm.Card" in code
        assert "vm.Filter" in code
        assert 'title="Test Dashboard"' in code

    def test_multi_page_code(self):
        from vizro_genui.rendering.builder import config_to_python_code

        config = {
            "pages": [
                {"title": "Page 1", "components": [{"type": "Card", "text": "A"}]},
                {"title": "Page 2", "components": [{"type": "Card", "text": "B"}]},
            ]
        }

        code = config_to_python_code(config)
        assert "page_0" in code
        assert "page_1" in code


class TestTemplates:
    def test_bp_dashboard_template(self):
        from vizro_genui.templates.bp_presentation import full_bp_dashboard

        config = full_bp_dashboard()
        assert "pages" in config
        assert len(config["pages"]) == 3
        assert config["title"] == "Business Plan Dashboard"

    def test_executive_summary_template(self):
        from vizro_genui.templates.bp_presentation import executive_summary_template

        page = executive_summary_template(title="Q4 Summary")
        assert page["title"] == "Q4 Summary"
        assert len(page["components"]) >= 3  # KPIs + charts

    def test_quarterly_review_template(self):
        from vizro_genui.templates.bp_presentation import quarterly_review_template

        page = quarterly_review_template(
            metrics=["revenue", "costs"],
            filter_columns=["region", "product"],
        )
        assert len(page["components"]) == 2
        assert len(page["controls"]) == 2
