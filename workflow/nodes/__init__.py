"""
Node implementations for the PPTX workflow.

This package contains all node functions for the LangGraph workflow,
including script execution nodes and LLM-based nodes.
"""

from workflow.nodes.script_nodes import (
    stage0a_template_intake,
    stage0b_source_intake,
    stage1_extract,
    stage4_rearrange,
    stage5_inventory,
    stage7_finalize,
)

from workflow.nodes.llm_nodes import (
    stage2_analyze,
    stage3_outline,
    stage6_replacements,
    get_llm,
)

__all__ = [
    # Script nodes
    "stage0a_template_intake",
    "stage0b_source_intake",
    "stage1_extract",
    "stage4_rearrange",
    "stage5_inventory",
    "stage7_finalize",
    # LLM nodes
    "stage2_analyze",
    "stage3_outline",
    "stage6_replacements",
    "get_llm",
]