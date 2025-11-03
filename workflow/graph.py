"""
LangGraph workflow construction for PPTX generation.

This module builds the complete stateful workflow graph with routing,
checkpointing, and all stage nodes.
"""

from typing import Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Import checkpointers conditionally
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

try:
    from langgraph.checkpoint.postgres import PostgresSaver
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

from workflow.state import WorkflowState, Context
from workflow.router import router
from workflow.nodes import (
    stage0a_template_intake,
    stage0b_source_intake,
    stage1_extract,
    stage2_analyze,
    stage3_outline,
    stage4_rearrange,
    stage5_inventory,
    stage6_replacements,
    stage7_finalize,
)


def build_workflow_graph(
    checkpointer_type: str = "sqlite",
    db_uri: Optional[str] = None,
    enable_interrupts: bool = False
):
    """
    Build the complete LangGraph workflow for PPTX generation.
    
    This creates a stateful workflow with:
    - Router-based conditional routing
    - 9 stages (0A, 0B, 1-7)
    - Checkpointing for persistence and resume
    - Error handling and state management
    
    Args:
        checkpointer_type: Type of checkpointer ("sqlite", "postgres", or "memory")
        db_uri: Database URI for checkpointer
            - SQLite: "checkpoints.db" or path to db file
            - PostgreSQL: "postgresql://user:pass@host:port/dbname"
        enable_interrupts: If True, pause before LLM stages for review
    
    Returns:
        Compiled StateGraph ready for execution
    
    Example:
        >>> # SQLite (development)
        >>> graph = build_workflow_graph("sqlite", "checkpoints.db")
        >>> 
        >>> # Memory (testing)
        >>> graph = build_workflow_graph("memory")
        >>> 
        >>> # PostgreSQL (production)
        >>> graph = build_workflow_graph(
        ...     "postgres",
        ...     "postgresql://user:pass@localhost/pptx_workflow"
        ... )
    """
    
    # Initialize checkpointer
    if checkpointer_type == "sqlite":
        if not SQLITE_AVAILABLE:
            print("⚠️  SQLite checkpointer not available, using in-memory checkpointer")
            print("   Install with: pip install langgraph-checkpoint-sqlite")
            checkpointer = MemorySaver()
            print("Using MemorySaver (in-memory, not persistent)")
        else:
            import sqlite3
            db_path = db_uri or "checkpoints.db"
            # Create connection and pass to SqliteSaver directly
            conn = sqlite3.connect(db_path, check_same_thread=False)
            checkpointer = SqliteSaver(conn)
            print(f"Using SQLite checkpointer: {db_path}")
    elif checkpointer_type == "postgres":
        if not POSTGRES_AVAILABLE:
            raise ImportError("PostgreSQL checkpointer not available. Install: pip install langgraph-checkpoint-postgres psycopg2-binary")
        if not db_uri:
            raise ValueError("PostgreSQL URI required for postgres checkpointer")
        # For PostgreSQL, we'll use the context manager approach in a wrapper
        checkpointer = PostgresSaver.from_conn_string(db_uri).__enter__()
        print(f"Using PostgreSQL checkpointer: {db_uri}")
    elif checkpointer_type == "memory":
        checkpointer = MemorySaver()
        print("Using MemorySaver (in-memory, not persistent)")
    else:
        raise ValueError(f"Unknown checkpointer type: {checkpointer_type}. Use 'sqlite', 'postgres', or 'memory'")
    
    # Create graph builder
    builder = StateGraph(
        state_schema=WorkflowState,
        config_schema=Context
    )
    
    # Add all stage nodes (router is NOT a node, it's a routing function)
    builder.add_node("stage0a_template_intake", stage0a_template_intake)
    builder.add_node("stage0b_source_intake", stage0b_source_intake)
    builder.add_node("stage1_extract", stage1_extract)
    builder.add_node("stage2_analyze", stage2_analyze)
    builder.add_node("stage3_outline", stage3_outline)
    builder.add_node("stage4_rearrange", stage4_rearrange)
    builder.add_node("stage5_inventory", stage5_inventory)
    builder.add_node("stage6_replacements", stage6_replacements)
    builder.add_node("stage7_finalize", stage7_finalize)
    
    # Entry point: START uses router function to determine first stage
    builder.add_conditional_edges(
        START,
        router,
        {
            "stage0a_template_intake": "stage0a_template_intake",
            "stage0b_source_intake": "stage0b_source_intake",
            "stage1_extract": "stage1_extract",
            "stage2_analyze": "stage2_analyze",
            "stage3_outline": "stage3_outline",
            "stage4_rearrange": "stage4_rearrange",
            "stage5_inventory": "stage5_inventory",
            "stage6_replacements": "stage6_replacements",
            "stage7_finalize": "stage7_finalize",
            END: END
        }
    )
    
    # All stage nodes use router to determine next stage
    for stage_node in [
        "stage0a_template_intake",
        "stage0b_source_intake",
        "stage1_extract",
        "stage2_analyze",
        "stage3_outline",
        "stage4_rearrange",
        "stage5_inventory",
        "stage6_replacements",
        "stage7_finalize"
    ]:
        builder.add_conditional_edges(
            stage_node,
            router,
            {
                "stage0a_template_intake": "stage0a_template_intake",
                "stage0b_source_intake": "stage0b_source_intake",
                "stage1_extract": "stage1_extract",
                "stage2_analyze": "stage2_analyze",
                "stage3_outline": "stage3_outline",
                "stage4_rearrange": "stage4_rearrange",
                "stage5_inventory": "stage5_inventory",
                "stage6_replacements": "stage6_replacements",
                "stage7_finalize": "stage7_finalize",
                END: END
            }
        )
    
    # Configure interrupts (optional)
    interrupt_before = []
    if enable_interrupts:
        # Pause before LLM stages for human review
        interrupt_before = ["stage2_analyze", "stage3_outline", "stage6_replacements"]
        print(f"Interrupts enabled before: {interrupt_before}")
    
    # Compile graph with checkpointing
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before if interrupt_before else None
    )
    
    print("✅ Workflow graph compiled successfully")
    return graph


def create_workflow_config(thread_id: str, checkpoint_id: Optional[str] = None) -> dict:
    """
    Create configuration for workflow execution.
    
    Args:
        thread_id: Thread identifier for state isolation
        checkpoint_id: Optional checkpoint ID to resume from
    
    Returns:
        Configuration dict for graph.invoke() or graph.stream()
    
    Example:
        >>> # New execution
        >>> config = create_workflow_config("thread-123")
        >>> 
        >>> # Resume from checkpoint
        >>> config = create_workflow_config("thread-123", "checkpoint-abc")
    """
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    if checkpoint_id:
        config["configurable"]["checkpoint_id"] = checkpoint_id
    
    return config


def get_workflow_state(graph, thread_id: str, checkpoint_id: Optional[str] = None):
    """
    Get current workflow state.
    
    Args:
        graph: Compiled workflow graph
        thread_id: Thread identifier
        checkpoint_id: Optional specific checkpoint ID
    
    Returns:
        StateSnapshot with current state
    
    Example:
        >>> state = get_workflow_state(graph, "thread-123")
        >>> print(f"Current stage: {state.values['current_stage']}")
        >>> print(f"Completed: {state.values['completed_stages']}")
    """
    config = create_workflow_config(thread_id, checkpoint_id)
    return graph.get_state(config)


def list_checkpoints(graph, thread_id: str, limit: int = 10):
    """
    List checkpoint history for a thread.
    
    Args:
        graph: Compiled workflow graph
        thread_id: Thread identifier
        limit: Maximum number of checkpoints to return
    
    Returns:
        List of checkpoint snapshots
    
    Example:
        >>> checkpoints = list_checkpoints(graph, "thread-123")
        >>> for cp in checkpoints:
        ...     print(f"Checkpoint: {cp.config['configurable']['checkpoint_id']}")
        ...     print(f"Stage: {cp.values['current_stage']}")
    """
    config = create_workflow_config(thread_id)
    checkpoints = []
    
    for i, checkpoint in enumerate(graph.get_state_history(config)):
        if i >= limit:
            break
        checkpoints.append(checkpoint)
    
    return checkpoints