"""
Router node for the PPTX workflow.

The router determines the next stage to execute based on the current
workflow state, handling dependencies and completion detection.
"""

from typing import Literal
from langgraph.graph import END

from workflow.state import (
    WorkflowState,
    get_next_stage,
    STAGE_0A,
    STAGE_0B,
    STAGE_1,
    STAGE_2,
    STAGE_3,
    STAGE_4,
    STAGE_5,
    STAGE_6,
    STAGE_7,
)


def router(state: WorkflowState) -> Literal[
    "stage0a_template_intake",
    "stage0b_source_intake",
    "stage1_extract",
    "stage2_analyze",
    "stage3_outline",
    "stage4_rearrange",
    "stage5_inventory",
    "stage6_replacements",
    "stage7_finalize",
    END
]:
    """
    Route to the next stage based on current workflow state.
    
    This function implements the core routing logic for the workflow,
    determining which stage should execute next based on:
    - Completed stages
    - Failed stages
    - Stage dependencies
    - Workflow status
    
    Args:
        state: Current workflow state
    
    Returns:
        Next stage identifier or END if workflow is complete/failed
    """
    
    # Check if workflow has failed
    if state["status"] == "failed":
        print(f"[Router] Workflow failed, ending execution")
        return END
    
    # Check if workflow is complete
    if state["status"] == "completed":
        print(f"[Router] Workflow already completed")
        return END
    
    # Get next stage based on dependencies
    next_stage = get_next_stage(state)
    
    if next_stage is None:
        # All stages completed
        print(f"[Router] All stages completed, ending workflow")
        return END
    
    # Map stage constants to node names
    stage_map = {
        STAGE_0A: "stage0a_template_intake",
        STAGE_0B: "stage0b_source_intake",
        STAGE_1: "stage1_extract",
        STAGE_2: "stage2_analyze",
        STAGE_3: "stage3_outline",
        STAGE_4: "stage4_rearrange",
        STAGE_5: "stage5_inventory",
        STAGE_6: "stage6_replacements",
        STAGE_7: "stage7_finalize",
    }
    
    node_name = stage_map.get(next_stage)
    
    if node_name is None:
        print(f"[Router] Unknown stage: {next_stage}, ending workflow")
        return END
    
    print(f"[Router] Routing to: {node_name}")
    return node_name


def should_continue(state: WorkflowState) -> bool:
    """
    Check if workflow should continue execution.
    
    Args:
        state: Current workflow state
    
    Returns:
        True if workflow should continue, False otherwise
    """
    if state["status"] in ["failed", "completed"]:
        return False
    
    next_stage = get_next_stage(state)
    return next_stage is not None