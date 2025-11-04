"""
FastAPI server for PPTX workflow.

Provides REST API endpoints for workflow execution, status checking,
and result retrieval.
"""

import uuid
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from workflow.state import create_initial_state
from workflow.graph import (
    build_workflow_graph,
    create_workflow_config,
    get_workflow_state,
    list_checkpoints as get_checkpoints,
)

# Load environment
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="PPTX Workflow API",
    description="Automated PowerPoint generation from templates using LangGraph and Claude AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global graph instance
graph = None


@app.on_event("startup")
async def startup_event():
    """Initialize workflow graph on startup."""
    global graph
    db_uri = os.getenv("DATABASE_URL", "checkpoints.db")
    graph = build_workflow_graph("sqlite", db_uri)
    print("✅ Workflow graph initialized")


# Pydantic models for API
class WorkflowCreateRequest(BaseModel):
    """Request model for creating a new workflow."""
    output_name: str
    workflow_id: Optional[str] = None
    thread_id: Optional[str] = None


class WorkflowCreateResponse(BaseModel):
    """Response model for workflow creation."""
    workflow_id: str
    thread_id: str
    workspace_dir: str
    status: str
    message: str


class StageTimingInfo(BaseModel):
    """Stage timing information."""
    stage: str
    start_time: str
    end_time: Optional[str]
    duration_seconds: Optional[float]


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    workflow_id: str
    thread_id: str
    current_stage: str
    status: str
    completed_stages: List[str]
    failed_stages: List[str]
    artifacts: dict
    errors: List[dict]
    stage_timings: List[StageTimingInfo]
    started_at: Optional[str]
    completed_at: Optional[str]
    total_duration_seconds: Optional[float]


class CheckpointInfo(BaseModel):
    """Checkpoint information."""
    checkpoint_id: str
    current_stage: str
    status: str
    completed_count: int


# API Endpoints

@app.post("/api/v1/workflows", response_model=WorkflowCreateResponse)
async def create_workflow(
    background_tasks: BackgroundTasks,
    template: UploadFile = File(...),
    source: UploadFile = File(...),
    output_name: str = Form(...),
    workflow_id: Optional[str] = Form(None),
    thread_id: Optional[str] = Form(None)
):
    """
    Create and execute a new PPTX generation workflow.
    
    Uploads template and source files, then starts workflow execution
    in the background.
    """
    # Generate IDs
    wf_id = workflow_id or f"workflow_{uuid.uuid4().hex[:8]}"
    th_id = thread_id or f"thread_{uuid.uuid4().hex[:8]}"
    workspace_dir = f"outputs/{wf_id}"
    
    # Create workspace
    workspace = Path(workspace_dir)
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded files
    template_path = workspace / "input" / template.filename
    source_path = workspace / "input" / source.filename
    template_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write files
    with open(template_path, "wb") as f:
        f.write(await template.read())
    
    with open(source_path, "wb") as f:
        f.write(await source.read())
    
    # Create initial state
    initial_state = create_initial_state(
        workflow_id=wf_id,
        thread_id=th_id,
        template_path=str(template_path.absolute()),
        source_path=str(source_path.absolute()),
        output_name=output_name,
        workspace_dir=workspace_dir
    )
    
    # Execute workflow in background
    background_tasks.add_task(execute_workflow_background, th_id, initial_state)
    
    return WorkflowCreateResponse(
        workflow_id=wf_id,
        thread_id=th_id,
        workspace_dir=workspace_dir,
        status="started",
        message=f"Workflow started. Use thread_id '{th_id}' to check status."
    )


async def execute_workflow_background(thread_id: str, initial_state: dict):
    """Execute workflow in background."""
    try:
        config = create_workflow_config(thread_id)
        
        # Execute workflow
        for chunk in graph.stream(initial_state, config, stream_mode="values"):
            # Workflow progresses automatically
            pass
            
    except Exception as e:
        print(f"Error in background workflow: {e}")


@app.get("/api/v1/workflows/{thread_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(thread_id: str):
    """
    Get current status of a workflow.
    
    Returns the current state including stage, completion status,
    and any errors.
    """
    try:
        state = get_workflow_state(graph, thread_id)
        
        if not state:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {thread_id}")
        
        values = state.values
        
        return WorkflowStatusResponse(
            workflow_id=values["workflow_id"],
            thread_id=values["thread_id"],
            current_stage=values["current_stage"],
            status=values["status"],
            completed_stages=values["completed_stages"],
            failed_stages=values["failed_stages"],
            artifacts=values["artifacts"],
            errors=values["errors"],
            stage_timings=[
                StageTimingInfo(**timing) for timing in values.get("stage_timings", [])
            ],
            started_at=values.get("started_at"),
            completed_at=values.get("completed_at"),
            total_duration_seconds=values.get("total_duration_seconds")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workflows/{thread_id}/checkpoints", response_model=List[CheckpointInfo])
async def list_workflow_checkpoints(thread_id: str, limit: int = 10):
    """
    List all checkpoints for a workflow.
    
    Useful for debugging and understanding workflow progression.
    """
    try:
        checkpoints = get_checkpoints(graph, thread_id, limit)
        
        result = []
        for cp in checkpoints:
            result.append(CheckpointInfo(
                checkpoint_id=cp.config["configurable"]["checkpoint_id"],
                current_stage=cp.values.get("current_stage", "unknown"),
                status=cp.values.get("status", "unknown"),
                completed_count=len(cp.values.get("completed_stages", []))
            ))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workflows/{thread_id}/result")
async def get_workflow_result(thread_id: str):
    """
    Get the final PPTX file if workflow is completed.
    
    Returns the generated PowerPoint file for download.
    """
    try:
        state = get_workflow_state(graph, thread_id)
        
        if not state:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {thread_id}")
        
        values = state.values
        
        if values["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Workflow not completed. Current status: {values['status']}"
            )
        
        # Get final PPTX path
        final_pptx = values["artifacts"].get("final_pptx")
        
        if not final_pptx or not Path(final_pptx).exists():
            raise HTTPException(status_code=404, detail="Final PPTX file not found")
        
        # Return file
        return FileResponse(
            path=final_pptx,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=f"{values['output_name']}.pptx"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/workflows/{thread_id}")
async def cancel_workflow(thread_id: str):
    """
    Cancel a running workflow.
    
    Note: This marks the workflow as failed but doesn't stop
    background execution immediately.
    """
    try:
        state = get_workflow_state(graph, thread_id)
        
        if not state:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {thread_id}")
        
        # TODO: Implement actual cancellation logic
        # For now, just return current state
        
        return JSONResponse(
            content={
                "message": "Workflow cancellation requested",
                "thread_id": thread_id,
                "current_status": state.values["status"]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "PPTX Workflow API",
        "version": "1.0.0",
        "graph_initialized": graph is not None
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "PPTX Workflow API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "create_workflow": "POST /api/v1/workflows",
            "get_status": "GET /api/v1/workflows/{thread_id}/status",
            "list_checkpoints": "GET /api/v1/workflows/{thread_id}/checkpoints",
            "get_result": "GET /api/v1/workflows/{thread_id}/result",
            "cancel_workflow": "DELETE /api/v1/workflows/{thread_id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)