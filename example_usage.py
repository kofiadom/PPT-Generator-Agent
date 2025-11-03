"""
Example usage of the PPTX LangGraph workflow.

This script demonstrates how to use the workflow programmatically.
"""

import uuid
from pathlib import Path
from dotenv import load_dotenv

from workflow.state import create_initial_state
from workflow.graph import build_workflow_graph, create_workflow_config

# Load environment variables
load_dotenv()


def main():
    """Run example workflow."""
    
    # Configuration
    template_path = "sample_pptx/Consulting.pptx"
    source_path = "sample_pptx/Consulting.docx"
    output_name = "Example-Presentation"
    
    # Generate IDs
    workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
    thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    workspace_dir = f"outputs/{workflow_id}"
    
    print(f"\n{'='*60}")
    print(f"PowerPoint Workflow - Example Execution")
    print(f"{'='*60}")
    print(f"Workflow ID: {workflow_id}")
    print(f"Thread ID: {thread_id}")
    print(f"Template: {template_path}")
    print(f"Source: {source_path}")
    print(f"Output: {output_name}.pptx")
    print(f"Workspace: {workspace_dir}")
    print(f"{'='*60}\n")
    
    # Validate input files
    if not Path(template_path).exists():
        print(f"❌ Template not found: {template_path}")
        return
    
    if not Path(source_path).exists():
        print(f"❌ Source not found: {source_path}")
        return
    
    # Create initial state
    initial_state = create_initial_state(
        workflow_id=workflow_id,
        thread_id=thread_id,
        template_path=str(Path(template_path).absolute()),
        source_path=str(Path(source_path).absolute()),
        output_name=output_name,
        workspace_dir=workspace_dir
    )
    
    # Build graph (using SQLite for simplicity)
    print("Building workflow graph...")
    graph = build_workflow_graph(
        checkpointer_type="sqlite",
        db_uri="checkpoints.db",
        enable_interrupts=False
    )
    
    # Create config
    config = create_workflow_config(thread_id)
    
    # Execute workflow with streaming
    print("\n🚀 Starting workflow execution...\n")
    
    try:
        for chunk in graph.stream(initial_state, config, stream_mode="values"):
            current_stage = chunk.get("current_stage", "unknown")
            status = chunk.get("status", "unknown")
            
            # Print latest message
            if chunk.get("messages"):
                latest_msg = chunk["messages"][-1]
                print(f"[{current_stage}] {latest_msg['content']}")
            
            # Check for completion
            if status == "completed":
                print(f"\n{'='*60}")
                print("✅ Workflow Completed Successfully!")
                print(f"{'='*60}")
                
                # Print artifacts
                artifacts = chunk.get("artifacts", {})
                if artifacts.get("final_pptx"):
                    print(f"📊 Final Presentation: {artifacts['final_pptx']}")
                if artifacts.get("final_thumbnail"):
                    print(f"🖼️  Thumbnail: {artifacts['final_thumbnail']}")
                
                print(f"\nCompleted Stages: {len(chunk['completed_stages'])}/9")
                for stage in chunk['completed_stages']:
                    print(f"  ✅ {stage}")
                
                print(f"{'='*60}\n")
                break
            
            # Check for failure
            if status == "failed":
                print(f"\n{'='*60}")
                print("❌ Workflow Failed")
                print(f"{'='*60}")
                
                if chunk.get("errors"):
                    for error in chunk["errors"]:
                        print(f"\nStage: {error['stage']}")
                        print(f"Error: {error['error']}")
                        print(f"Time: {error['timestamp']}")
                
                print(f"{'='*60}\n")
                break
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
        print(f"You can resume later with thread ID: {thread_id}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()