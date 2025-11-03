"""
LangGraph-based PPTX workflow implementation.

This package provides a stateful, router-based workflow for generating
PowerPoint presentations from templates and source documents.
"""

from workflow.state import (
    WorkflowState,
    Context,
    Message,
    ErrorRecord,
    create_initial_state,
    get_default_context,
    is_stage_completed,
    is_stage_failed,
    get_next_stage,
    add_message,
    add_error,
    mark_stage_complete,
    STAGE_0A,
    STAGE_0B,
    STAGE_1,
    STAGE_2,
    STAGE_3,
    STAGE_4,
    STAGE_5,
    STAGE_6,
    STAGE_7,
    ALL_STAGES,
    LLM_STAGES,
    SCRIPT_STAGES,
)

__all__ = [
    "WorkflowState",
    "Context",
    "Message",
    "ErrorRecord",
    "create_initial_state",
    "get_default_context",
    "is_stage_completed",
    "is_stage_failed",
    "get_next_stage",
    "add_message",
    "add_error",
    "mark_stage_complete",
    "STAGE_0A",
    "STAGE_0B",
    "STAGE_1",
    "STAGE_2",
    "STAGE_3",
    "STAGE_4",
    "STAGE_5",
    "STAGE_6",
    "STAGE_7",
    "ALL_STAGES",
    "LLM_STAGES",
    "SCRIPT_STAGES",
]

__version__ = "0.1.0"