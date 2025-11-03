"""
Command-line interface for the PPTX workflow.

Provides easy-to-use CLI for executing the workflow with various options.
"""

import argparse
import uuid
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

from workflow.state import create_initial_state, get_default_context
from workflow.graph import (
    build_workflow_graph,
    create_workflow_config,
    get_workflow_state,
    list_checkpoints,
)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PowerPoint Workflow - Generate presentations from templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python -m workflow.cli --template sample_pptx/Consulting.pptx --source sample_pptx/Consulting.docx --output "My-Presentation"
  
  # With custom workspace
  python -m workflow.cli --template template.pptx --source content.docx --output "Output" --workspace custom_outputs
  
  # Resume from checkpoint
  python -m workflow.cli --resume thread-abc123
  
  # List checkpoints
  python -m workflow.cli --list-checkpoints thread-abc123
        """
    )
    
    # Input arguments
    parser.add_argument(
        "--template",
        help="Path to PowerPoint template file (.pptx)"
    )
    parser.add_argument(
        "--source",
        help="Path to source content document (.docx, .pdf, .md, .txt)"
    )
    parser.add_argument(
        "--output",
        help="Output presentation name (without extension)"
    )
    
    # Workflow control
    parser.add_argument(
        "--workspace",
        help="Workspace directory for outputs (default: outputs/workflow_<id>)"
    )
    parser.add_argument(
        "--workflow-id",
        help="Custom workflow ID (default: auto-generated)"
    )
    parser.add_argument(
        "--thread-id",
        help="Custom thread ID (default: auto-generated)"
    )
    
    # Resume and inspection
    parser.add_argument(
        "--resume",
        metavar="THREAD_ID",
        help="Resume workflow from thread ID"
    )
    parser.add_argument(
        "--checkpoint",
        metavar="CHECKPOINT_ID",
        help="Resume from specific checkpoint ID (requires --resume)"
    )
    parser.add_argument(
        "--list-checkpoints",
        metavar="THREAD_ID",
        help="List all checkpoints for a thread"
    )
    parser.add_argument(
        "--get-state",
        metavar="THREAD_ID",
        help="Get current state for a thread"
    )
    
    # Database configuration
    parser.add_argument(
        "--db-type",
        choices=["sqlite", "postgres"],
        default="sqlite",
        help="Database type for checkpointing (default: sqlite)"
    )
    parser.add_argument(
        "--db-uri",
        help="Database URI (default: checkpoints.db for SQLite, or from DATABASE_URL env var)"
    )
    
    # LLM configuration
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-5",
        help="LLM model to use (default: claude-sonnet-4-5)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="LLM temperature (default: 0.7)"
    )
    
    # Workflow options
    parser.add_argument(
        "--enable-interrupts",
        action="store_true",
        help="Pause before LLM stages for review"
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        default=True,
        help="Stream workflow progress (default: True)"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Handle inspection commands
    if args.list_checkpoints:
        list_checkpoints_command(args)
        return
    
    if args.get_state:
        get_state_command(args)
        return
    
    # Handle resume
    if args.resume:
        resume_workflow_command(args)
        return
    
    # Validate required arguments for new workflow
    if not all([args.template, args.source, args.output]):
        parser.error("--template, --source, and --output are required for new workflow")
    
    # Execute new workflow
    execute_workflow_command(args)


def execute_workflow_command(args):
    """Execute a new workflow."""
    # Generate IDs
    workflow_id = args.workflow_id or f"workflow_{uuid.uuid4().hex[:8]}"
    thread_id = args.thread_id or f"thread_{uuid.uuid4().hex[:8]}"
    
    # Determine workspace
    if args.workspace:
        workspace_dir = args.workspace
    else:
        workspace_root = os.getenv("WORKSPACE_ROOT", "outputs")
        workspace_dir = f"{workspace_root}/{workflow_id}"
    
    # Validate input files
    template_path = Path(args.template)
    source_path = Path(args.source)
    
    if not template_path.exists():
        print(f"❌ Error: Template file not found: {args.template}")
        return
    
    if not source_path.exists():
        print(f"❌ Error: Source file not found: {args.source}")
        return
    
    # Create initial state
    initial_state = create_initial_state(
        workflow_id=workflow_id,
        thread_id=thread_id,
        template_path=str(template_path.absolute()),
        source_path=str(source_path.absolute()),
        output_name=args.output,
        workspace_dir=workspace_dir
    )
    
    # Get database URI
    db_uri = args.db_uri or os.getenv("DATABASE_URL", "checkpoints.db")
    
    # Build graph
    print(f"\n{'='*60}")
    print(f"PowerPoint Workflow Execution")
    print(f"{'='*60}")
    print(f"Workflow ID: {workflow_id}")
    print(f"Thread ID: {thread_id}")
    print(f"Template: {args.template}")
    print(f"Source: {args.source}")
    print(f"Output: {args.output}.pptx")
    print(f"Workspace: {workspace_dir}")
    print(f"{'='*60}\n")
    
    graph = build_workflow_graph(
        checkpointer_type=args.db_type,
        db_uri=db_uri,
        enable_interrupts=args.enable_interrupts
    )
    
    # Create config
    config = create_workflow_config(thread_id)
    
    # Execute workflow
    if args.stream:
        print("\n🚀 Starting workflow execution...\n")
        for chunk in graph.stream(initial_state, config, stream_mode="values"):
            current_stage = chunk.get("current_stage", "unknown")
            status = chunk.get("status", "unknown")
            
            # Print latest message if available
            if chunk.get("messages"):
                latest_msg = chunk["messages"][-1]
                print(f"[{current_stage}] {latest_msg['content']}")
            
            # Check for completion
            if status == "completed":
                print(f"\n{'='*60}")
                print("✅ Workflow Completed Successfully!")
                print(f"{'='*60}")
                final_pptx = chunk.get("artifacts", {}).get("final_pptx")
                if final_pptx:
                    print(f"📊 Final Presentation: {final_pptx}")
                print(f"{'='*60}\n")
                break
            
            # Check for failure
            if status == "failed":
                print(f"\n{'='*60}")
                print("❌ Workflow Failed")
                print(f"{'='*60}")
                if chunk.get("errors"):
                    for error in chunk["errors"]:
                        print(f"Stage: {error['stage']}")
                        print(f"Error: {error['error']}")
                print(f"{'='*60}\n")
                break
    else:
        # Non-streaming execution
        result = graph.invoke(initial_state, config)
        print(f"\nWorkflow Status: {result['status']}")
        if result['status'] == 'completed':
            print(f"Final PPTX: {result['artifacts'].get('final_pptx')}")


def resume_workflow_command(args):
    """Resume a workflow from a thread ID."""
    thread_id = args.resume
    checkpoint_id = args.checkpoint
    
    print(f"\n{'='*60}")
    print(f"Resuming Workflow")
    print(f"{'='*60}")
    print(f"Thread ID: {thread_id}")
    if checkpoint_id:
        print(f"Checkpoint ID: {checkpoint_id}")
    print(f"{'='*60}\n")
    
    # Get database URI
    db_uri = args.db_uri or os.getenv("DATABASE_URL", "checkpoints.db")
    
    # Build graph
    graph = build_workflow_graph(
        checkpointer_type=args.db_type,
        db_uri=db_uri,
        enable_interrupts=args.enable_interrupts
    )
    
    # Get current state
    current_state = get_workflow_state(graph, thread_id, checkpoint_id)
    
    if not current_state:
        print(f"❌ No state found for thread: {thread_id}")
        return
    
    print(f"Current Stage: {current_state.values['current_stage']}")
    print(f"Status: {current_state.values['status']}")
    print(f"Completed Stages: {current_state.values['completed_stages']}")
    print(f"\n🚀 Resuming execution...\n")
    
    # Create config
    config = create_workflow_config(thread_id, checkpoint_id)
    
    # Resume execution
    for chunk in graph.stream(None, config, stream_mode="values"):
        current_stage = chunk.get("current_stage", "unknown")
        status = chunk.get("status", "unknown")
        
        if chunk.get("messages"):
            latest_msg = chunk["messages"][-1]
            print(f"[{current_stage}] {latest_msg['content']}")
        
        if status in ["completed", "failed"]:
            break


def list_checkpoints_command(args):
    """List checkpoints for a thread."""
    thread_id = args.list_checkpoints
    
    # Get database URI
    db_uri = args.db_uri or os.getenv("DATABASE_URL", "checkpoints.db")
    
    # Build graph
    graph = build_workflow_graph(
        checkpointer_type=args.db_type,
        db_uri=db_uri
    )
    
    # List checkpoints
    checkpoints = list_checkpoints(graph, thread_id, limit=20)
    
    if not checkpoints:
        print(f"No checkpoints found for thread: {thread_id}")
        return
    
    print(f"\n{'='*60}")
    print(f"Checkpoints for Thread: {thread_id}")
    print(f"{'='*60}\n")
    
    for i, cp in enumerate(checkpoints):
        checkpoint_id = cp.config["configurable"]["checkpoint_id"]
        current_stage = cp.values.get("current_stage", "unknown")
        status = cp.values.get("status", "unknown")
        completed = len(cp.values.get("completed_stages", []))
        
        print(f"{i+1}. Checkpoint: {checkpoint_id}")
        print(f"   Stage: {current_stage}")
        print(f"   Status: {status}")
        print(f"   Completed: {completed}/9 stages")
        print()


def get_state_command(args):
    """Get current state for a thread."""
    thread_id = args.get_state
    
    # Get database URI
    db_uri = args.db_uri or os.getenv("DATABASE_URL", "checkpoints.db")
    
    # Build graph
    graph = build_workflow_graph(
        checkpointer_type=args.db_type,
        db_uri=db_uri
    )
    
    # Get state
    state = get_workflow_state(graph, thread_id)
    
    if not state:
        print(f"No state found for thread: {thread_id}")
        return
    
    values = state.values
    
    print(f"\n{'='*60}")
    print(f"Workflow State: {thread_id}")
    print(f"{'='*60}\n")
    print(f"Workflow ID: {values['workflow_id']}")
    print(f"Current Stage: {values['current_stage']}")
    print(f"Status: {values['status']}")
    print(f"Completed Stages ({len(values['completed_stages'])}/9):")
    for stage in values['completed_stages']:
        print(f"  ✅ {stage}")
    
    if values.get('failed_stages'):
        print(f"\nFailed Stages:")
        for stage in values['failed_stages']:
            print(f"  ❌ {stage}")
    
    if values.get('artifacts'):
        print(f"\nArtifacts:")
        for key, path in values['artifacts'].items():
            print(f"  {key}: {path}")
    
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()