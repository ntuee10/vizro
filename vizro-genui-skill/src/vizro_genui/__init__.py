"""Vizro GenUI Skill - Configuration-driven dashboard generation for Federator.ai Cortex."""

from vizro_genui.schema.extractor import extract_vizro_schema, get_constrained_schema
from vizro_genui.rendering.builder import build_dashboard_from_config, validate_config
from vizro_genui.cortex.skill import VizroGenUISkill
from vizro_genui.cortex.agent import CortexSkillAdapter, CortexIntent, CortexResponse

__all__ = [
    "extract_vizro_schema",
    "get_constrained_schema",
    "build_dashboard_from_config",
    "validate_config",
    "VizroGenUISkill",
    "CortexSkillAdapter",
    "CortexIntent",
    "CortexResponse",
]
