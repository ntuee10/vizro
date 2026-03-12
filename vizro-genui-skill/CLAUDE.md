# Vizro GenUI Skill

A GenUI skill that leverages Vizro's configuration-driven architecture to generate
McKinsey-grade dashboards for Federator.ai Cortex.

## Architecture

```
Cortex Agent → VizroGenUISkill.invoke() → Claude (structured output) → Vizro JSON Config → Dashboard
```

The key insight: Vizro abstracts Dash/Plotly behind Pydantic models. We extract the
JSON schema and force the LLM to output ONLY valid dashboard configurations via
structured tool_use — no raw Python, no syntax errors, no execution vulnerabilities.

## Project Structure

```
vizro-genui-skill/
├── src/vizro_genui/
│   ├── schema/           # Schema extraction and chart registry
│   │   ├── extractor.py  # Extract Vizro's Pydantic JSON Schema
│   │   └── chart_registry.py  # Available chart types + validation
│   ├── rendering/        # Dashboard materialization
│   │   └── builder.py    # Config → Vizro app + Python code generation
│   ├── cortex/           # Federator.ai Cortex integration
│   │   ├── skill.py      # Main VizroGenUISkill class
│   │   └── prompts.py    # LLM prompt templates
│   └── templates/        # Pre-built dashboard patterns
│       └── bp_presentation.py  # BP/quarterly review templates
├── examples/
│   ├── basic_usage.py
│   ├── cortex_integration.py
│   └── schema_inspection.py
└── tests/
```

## Three Integration Patterns

- **Pattern A (Backend Generator)**: Skill returns config → backend builds Vizro app → serves on dynamic URL → GenUI frontend embeds via iframe
- **Pattern B (Code Incorporation)**: Skill returns executable Python code → incorporated directly into system codebase
- **Pattern C (Hybrid)**: Start from BP template → LLM refines based on actual data

## Development

```bash
pip install -e ".[dev,cortex]"
pytest tests/
```
