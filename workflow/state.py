"""
State schema definitions for the PPTX workflow.

This module defines the complete state structure for the LangGraph-based
PowerPoint generation workflow, including state types, context configuration,
and helper functions.
"""

from typing import TypedDict, Annotated, Literal, Optional, List, Dict, Any
from datetime import datetime
from operator import add


class Message(TypedDict):
    """Message in conversation history."""
    role: Literal["user", "assistant", "system"]
    content: str


class ErrorRecord(TypedDict):
    """Error tracking record."""
    stage: str
    error: str
    timestamp: str


class StageTimingRecord(TypedDict):
    """Timing record for a stage."""
    stage: str
    start_time: str
    end_time: Optional[str]
    duration_seconds: Optional[float]


class WorkflowState(TypedDict):
    """
    Complete state for PPTX generation workflow.
    
    This state is persisted at each checkpoint and can be resumed
    from any point in the workflow.
    """
    
    # Workflow metadata
    workflow_id: str
    thread_id: str
    current_stage: str  # "stage0a", "stage1", etc.
    status: Literal["pending", "in_progress", "completed", "failed"]
    
    # Input files
    template_path: Optional[str]
    source_path: Optional[str]
    output_name: str
    
    # Conversation history (with reducer for appending)
    messages: Annotated[List[Message], add]
    
    # Stage completion tracking (with reducer for appending)
    completed_stages: Annotated[List[str], add]
    failed_stages: Annotated[List[str], add]
    
    # Artifacts (file paths generated at each stage)
    artifacts: Dict[str, str]  # stage_id -> file_path
    
    # Stage-specific data
    template_metadata: Optional[Dict[str, Any]]
    template_inventory: Optional[str]  # markdown content
    outline: Optional[str]  # markdown content
    slide_mapping: Optional[List[int]]
    text_inventory: Optional[Dict[str, Any]]
    replacement_text: Optional[Dict[str, Any]]
    
    # Error tracking (with reducer for appending)
    errors: Annotated[List[ErrorRecord], add]
    
    # Timing tracking (with reducer for appending)
    stage_timings: Annotated[List[StageTimingRecord], add]
    
    # Workspace
    workspace_dir: str
    
    # Timestamps
    created_at: str
    updated_at: str
    started_at: Optional[str]  # When first stage started
    completed_at: Optional[str]  # When workflow completed
    total_duration_seconds: Optional[float]  # Total execution time


class Context(TypedDict, total=False):
    """
    Configuration context for the workflow.
    
    These settings control workflow behavior and can be customized
    per execution.
    """
    max_retries: int
    llm_model: str
    llm_temperature: float
    workspace_root: str
    enable_interrupts: bool  # Pause before LLM stages for review


# Stage identifiers
STAGE_0A = "stage0a_template_intake"
STAGE_0B = "stage0b_source_intake"
STAGE_1 = "stage1_extract"
STAGE_2 = "stage2_analyze"
STAGE_3 = "stage3_outline"
STAGE_4 = "stage4_rearrange"
STAGE_5 = "stage5_inventory"
STAGE_6 = "stage6_replacements"
STAGE_7 = "stage7_finalize"

# All stages in order
ALL_STAGES = [
    STAGE_0A,
    STAGE_0B,
    STAGE_1,
    STAGE_2,
    STAGE_3,
    STAGE_4,
    STAGE_5,
    STAGE_6,
    STAGE_7,
]

# LLM-required stages
LLM_STAGES = [STAGE_2, STAGE_3, STAGE_6]

# Script-based stages
SCRIPT_STAGES = [STAGE_0A, STAGE_0B, STAGE_1, STAGE_4, STAGE_5, STAGE_7]


def create_initial_state(
    workflow_id: str,
    thread_id: str,
    template_path: str,
    source_path: str,
    output_name: str,
    workspace_dir: str,
) -> WorkflowState:
    """
    Create initial workflow state.
    
    Args:
        workflow_id: Unique workflow identifier
        thread_id: Thread identifier for checkpointing
        template_path: Path to PowerPoint template
        source_path: Path to source content document
        output_name: Name for output presentation (without extension)
        workspace_dir: Directory for workflow outputs
    
    Returns:
        Initial WorkflowState ready for execution
    """
    now = datetime.utcnow().isoformat()
    
    return WorkflowState(
        workflow_id=workflow_id,
        thread_id=thread_id,
        current_stage="start",
        status="pending",
        template_path=template_path,
        source_path=source_path,
        output_name=output_name,
        messages=[],
        completed_stages=[],
        failed_stages=[],
        artifacts={},
        template_metadata=None,
        template_inventory=None,
        outline=None,
        slide_mapping=None,
        text_inventory=None,
        replacement_text=None,
        errors=[],
        stage_timings=[],
        workspace_dir=workspace_dir,
        created_at=now,
        updated_at=now,
        started_at=None,
        completed_at=None,
        total_duration_seconds=None,
    )


def get_default_context() -> Context:
    """
    Get default context configuration.
    
    Returns:
        Default Context with sensible defaults
    """
    return Context(
        max_retries=3,
        llm_model="claude-sonnet-4-5",
        llm_temperature=0.7,
        workspace_root="outputs",
        enable_interrupts=False,
    )


def is_stage_completed(state: WorkflowState, stage: str) -> bool:
    """Check if a stage has been completed."""
    return stage in state["completed_stages"]


def is_stage_failed(state: WorkflowState, stage: str) -> bool:
    """Check if a stage has failed."""
    return stage in state["failed_stages"]


def get_next_stage(state: WorkflowState) -> Optional[str]:
    """
    Determine the next stage to execute based on completed stages.
    
    Args:
        state: Current workflow state
    
    Returns:
        Next stage identifier or None if workflow is complete
    """
    completed = set(state["completed_stages"])
    
    # Check each stage in order
    for stage in ALL_STAGES:
        if stage not in completed:
            # Check dependencies
            if stage == STAGE_0A:
                return STAGE_0A
            elif stage == STAGE_0B:
                if STAGE_0A in completed:
                    return STAGE_0B
            elif stage == STAGE_1:
                if STAGE_0A in completed:
                    return STAGE_1
            elif stage == STAGE_2:
                if STAGE_1 in completed:
                    return STAGE_2
            elif stage == STAGE_3:
                if STAGE_0B in completed and STAGE_2 in completed:
                    return STAGE_3
            elif stage == STAGE_4:
                if STAGE_3 in completed:
                    return STAGE_4
            elif stage == STAGE_5:
                if STAGE_4 in completed:
                    return STAGE_5
            elif stage == STAGE_6:
                if STAGE_3 in completed and STAGE_5 in completed:
                    return STAGE_6
            elif stage == STAGE_7:
                if STAGE_4 in completed and STAGE_6 in completed:
                    return STAGE_7
    
    # All stages completed
    return None


def add_message(state: WorkflowState, role: str, content: str) -> Dict[str, Any]:
    """
    Helper to add a message to state.
    
    Args:
        state: Current state
        role: Message role (user/assistant/system)
        content: Message content
    
    Returns:
        State update dict
    """
    return {
        "messages": [Message(role=role, content=content)],
        "updated_at": datetime.utcnow().isoformat(),
    }


def add_error(state: WorkflowState, stage: str, error: str) -> Dict[str, Any]:
    """
    Helper to add an error record to state.
    
    Args:
        state: Current state
        stage: Stage where error occurred
        error: Error message
    
    Returns:
        State update dict
    """
    return {
        "errors": [ErrorRecord(
            stage=stage,
            error=error,
            timestamp=datetime.utcnow().isoformat()
        )],
        "failed_stages": [stage],
        "status": "failed",
        "updated_at": datetime.utcnow().isoformat(),
    }


def mark_stage_complete(stage: str, start_time: str) -> Dict[str, Any]:
    """
    Helper to mark a stage as complete with timing.
    
    Args:
        stage: Stage identifier
        start_time: ISO format timestamp when stage started
    
    Returns:
        State update dict
    """
    end_time = datetime.utcnow()
    start_dt = datetime.fromisoformat(start_time)
    duration = (end_time - start_dt).total_seconds()
    
    return {
        "completed_stages": [stage],
        "current_stage": stage,
        "status": "in_progress",
        "updated_at": end_time.isoformat(),
        "stage_timings": [StageTimingRecord(
            stage=stage,
            start_time=start_time,
            end_time=end_time.isoformat(),
            duration_seconds=duration
        )]
    }


def start_stage_timing(stage: str) -> str:
    """
    Get current timestamp for stage start.
    
    Args:
        stage: Stage identifier
    
    Returns:
        ISO format timestamp
    """
    return datetime.utcnow().isoformat()


def get_total_duration(state: WorkflowState) -> Optional[float]:
    """
    Calculate total workflow duration from start to completion.
    
    Args:
        state: Current workflow state
    
    Returns:
        Total duration in seconds, or None if not started/completed
    """
    started_at = state.get("started_at")
    completed_at = state.get("completed_at")
    
    if not started_at or not completed_at:
        # If not completed, sum stage durations so far
        if state.get("stage_timings"):
            return sum(t.get("duration_seconds", 0) for t in state["stage_timings"])
        return None
    
    # Calculate from start to completion timestamps
    from datetime import datetime
    start_dt = datetime.fromisoformat(started_at)
    end_dt = datetime.fromisoformat(completed_at)
    return (end_dt - start_dt).total_seconds()