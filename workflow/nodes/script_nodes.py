"""
Script execution nodes for automated workflow stages.

These nodes execute Python scripts and shell commands for stages that
don't require LLM processing.
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, Any

from workflow.state import (
    WorkflowState,
    add_message,
    add_error,
    mark_stage_complete,
)
from workflow.utils import (
    log_stage_start,
    log_stage_complete,
    log_stage_error,
    copy_file,
    ensure_workspace,
)


# Helper to get filenames from state
def _get_template_filename(state: WorkflowState) -> str:
    """Get template filename from state."""
    return Path(state["template_path"]).name


def _get_source_filename(state: WorkflowState) -> str:
    """Get source filename from state."""
    return Path(state["source_path"]).name


# Stage 0A: Template Intake
def stage0a_template_intake(state: WorkflowState) -> Dict[str, Any]:
    """Stage 0A: Template Intake node."""
    log_stage_start("stage0a_template_intake: Template Intake")
    
    try:
        workspace = Path(state["workspace_dir"])
        ensure_workspace(str(workspace))
        
        # Copy template file
        template_path = state["template_path"]
        template_filename = Path(template_path).name
        dest_path = workspace / "stage0-template-intake" / template_filename
        
        print(f"  Copying template: {template_path} -> {dest_path}")
        copy_file(template_path, str(dest_path))
        
        # Run pptx_probe
        metadata_path = workspace / "stage0-template-intake" / "template-metadata.json"
        cmd = [sys.executable, "scripts/pptx_probe.py", str(dest_path), str(metadata_path)]
        
        print(f"  Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        
        log_stage_complete("stage0a_template_intake: Template Intake")
        
        # Update state
        update = mark_stage_complete("stage0a_template_intake")
        update.update(add_message(state, "system", "✅ Completed Template Intake"))
        update["artifacts"] = {
            **state.get("artifacts", {}),
            "template_pptx": str(dest_path),
            "template_metadata": str(metadata_path)
        }
        
        return update
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        log_stage_error("stage0a_template_intake", error_msg)
        update = add_error(state, "stage0a_template_intake", error_msg)
        update.update(add_message(state, "system", f"❌ Failed Template Intake: {error_msg}"))
        return update


# Stage 0B: Source Intake
def stage0b_source_intake(state: WorkflowState) -> Dict[str, Any]:
    """Stage 0B: Source Intake node."""
    log_stage_start("stage0b_source_intake: Source Intake")
    
    try:
        workspace = Path(state["workspace_dir"])
        ensure_workspace(str(workspace))
        
        # Copy source file
        source_path = state["source_path"]
        source_filename = Path(source_path).name
        dest_path = workspace / "stage0-source-intake" / source_filename
        
        print(f"  Copying source: {source_path} -> {dest_path}")
        copy_file(source_path, str(dest_path))
        
        # Run convert_to_markdown
        ingest_path = workspace / "stage0-source-intake" / "source-ingest.md"
        cmd = [sys.executable, "scripts/convert_to_markdown.py", str(dest_path), str(ingest_path)]
        
        print(f"  Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        # Debug output
        print(f"  Return code: {result.returncode}")
        if result.stdout:
            print(f"  Stdout: {result.stdout.strip()}")
        if result.stderr:
            print(f"  Stderr: {result.stderr.strip()}")
        
        # Check for errors
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or f"Command failed with exit code {result.returncode}"
            raise subprocess.CalledProcessError(result.returncode, cmd, stderr=error_msg)
        
        log_stage_complete("stage0b_source_intake: Source Intake")
        
        # Update state
        update = mark_stage_complete("stage0b_source_intake")
        update.update(add_message(state, "system", "✅ Completed Source Intake"))
        update["artifacts"] = {
            **state.get("artifacts", {}),
            "source_document": str(dest_path),
            "source_ingest": str(ingest_path)
        }
        
        return update
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        log_stage_error("stage0b_source_intake", error_msg)
        update = add_error(state, "stage0b_source_intake", error_msg)
        update.update(add_message(state, "system", f"❌ Failed Source Intake: {error_msg}"))
        return update


# Stage 1: Extract Template
def stage1_extract(state: WorkflowState) -> Dict[str, Any]:
    """Stage 1: Extract Template Content node."""
    log_stage_start("stage1_extract: Extract Template Content")
    
    try:
        workspace = Path(state["workspace_dir"])
        template_filename = _get_template_filename(state)
        template_path = workspace / "stage0-template-intake" / template_filename
        
        # Extract to markdown
        content_path = workspace / "stage1-extract" / "template-content.md"
        cmd1 = [sys.executable, "scripts/convert_to_markdown.py", str(template_path), str(content_path)]
        
        print(f"  Executing: {' '.join(cmd1)}")
        result = subprocess.run(cmd1, capture_output=True, text=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd1, stderr=result.stderr or result.stdout)
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        
        # Create thumbnail
        thumbnail_prefix = workspace / "stage1-extract" / "template-thumbnail"
        cmd2 = [sys.executable, "scripts/thumbnail.py", str(template_path), str(thumbnail_prefix)]
        
        print(f"  Executing: {' '.join(cmd2)}")
        result = subprocess.run(cmd2, capture_output=True, text=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd2, stderr=result.stderr or result.stdout)
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        
        log_stage_complete("stage1_extract: Extract Template Content")
        
        # Update state
        update = mark_stage_complete("stage1_extract")
        update.update(add_message(state, "system", "✅ Completed Extract Template Content"))
        update["artifacts"] = {
            **state.get("artifacts", {}),
            "template_content": str(content_path),
            "template_thumbnail": str(thumbnail_prefix) + ".jpg"
        }
        
        return update
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        log_stage_error("stage1_extract", error_msg)
        update = add_error(state, "stage1_extract", error_msg)
        update.update(add_message(state, "system", f"❌ Failed Extract Template Content: {error_msg}"))
        return update


# Stage 4: Rearrange Slides
def stage4_rearrange(state: WorkflowState) -> Dict[str, Any]:
    """Stage 4: Rearrange Slides node."""
    log_stage_start("stage4_rearrange: Rearrange Slides")
    
    try:
        workspace = Path(state["workspace_dir"])
        template_filename = _get_template_filename(state)
        template_path = workspace / "stage0-template-intake" / template_filename
        working_path = workspace / "stage4-rearrange" / "working.pptx"
        mapping_path = workspace / "stage3-outline" / "template-mapping.json"
        
        # Rearrange slides
        cmd1 = [sys.executable, "scripts/rearrange_from_mapping.py", str(template_path), str(working_path), str(mapping_path)]
        
        print(f"  Executing: {' '.join(cmd1)}")
        result = subprocess.run(cmd1, capture_output=True, text=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd1, stderr=result.stderr or result.stdout)
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        
        # Create thumbnail
        thumbnail_prefix = workspace / "stage4-rearrange" / "rearranged-slides"
        cmd2 = [sys.executable, "scripts/thumbnail.py", str(working_path), str(thumbnail_prefix)]
        
        print(f"  Executing: {' '.join(cmd2)}")
        result = subprocess.run(cmd2, capture_output=True, text=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd2, stderr=result.stderr or result.stdout)
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        
        log_stage_complete("stage4_rearrange: Rearrange Slides")
        
        # Update state
        update = mark_stage_complete("stage4_rearrange")
        update.update(add_message(state, "system", "✅ Completed Rearrange Slides"))
        update["artifacts"] = {
            **state.get("artifacts", {}),
            "working_pptx": str(working_path),
            "rearranged_thumbnail": str(thumbnail_prefix) + ".jpg"
        }
        
        return update
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        log_stage_error("stage4_rearrange", error_msg)
        update = add_error(state, "stage4_rearrange", error_msg)
        update.update(add_message(state, "system", f"❌ Failed Rearrange Slides: {error_msg}"))
        return update


# Stage 5: Text Inventory
def stage5_inventory(state: WorkflowState) -> Dict[str, Any]:
    """Stage 5: Extract Text Inventory node."""
    log_stage_start("stage5_inventory: Extract Text Inventory")
    
    try:
        workspace = Path(state["workspace_dir"])
        working_path = workspace / "stage4-rearrange" / "working.pptx"
        inventory_path = workspace / "stage5-inventory" / "text-inventory.json"
        
        # Extract inventory
        cmd = [sys.executable, "scripts/inventory.py", str(working_path), str(inventory_path)]
        
        print(f"  Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd, stderr=result.stderr or result.stdout)
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        
        log_stage_complete("stage5_inventory: Extract Text Inventory")
        
        # Update state
        update = mark_stage_complete("stage5_inventory")
        update.update(add_message(state, "system", "✅ Completed Extract Text Inventory"))
        update["artifacts"] = {
            **state.get("artifacts", {}),
            "text_inventory": str(inventory_path)
        }
        
        return update
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        log_stage_error("stage5_inventory", error_msg)
        update = add_error(state, "stage5_inventory", error_msg)
        update.update(add_message(state, "system", f"❌ Failed Extract Text Inventory: {error_msg}"))
        return update


# Stage 7: Apply Replacements & Finalize
def stage7_finalize(state: WorkflowState) -> Dict[str, Any]:
    """Stage 7: Apply Replacements & Finalize node."""
    log_stage_start("stage7_finalize: Apply Replacements & Finalize")
    
    try:
        workspace = Path(state["workspace_dir"])
        working_path = workspace / "stage4-rearrange" / "working.pptx"
        replacement_path = workspace / "stage6-replacement" / "replacement-text.json"
        final_path = workspace / "stage7-final" / f"{state['output_name']}.pptx"
        
        # Apply replacements
        cmd1 = [sys.executable, "scripts/replace.py", str(working_path), str(replacement_path), str(final_path)]
        
        print(f"  Executing: {' '.join(cmd1)}")
        result = subprocess.run(cmd1, capture_output=True, text=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd1, stderr=result.stderr or result.stdout)
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        
        # Create final thumbnail
        thumbnail_prefix = workspace / "stage7-final" / "final-presentation"
        cmd2 = [sys.executable, "scripts/thumbnail.py", str(final_path), str(thumbnail_prefix)]
        
        print(f"  Executing: {' '.join(cmd2)}")
        result = subprocess.run(cmd2, capture_output=True, text=True)
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd2, stderr=result.stderr or result.stdout)
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")
        
        log_stage_complete("stage7_finalize: Apply Replacements & Finalize")
        
        # Update state - mark workflow as completed
        update = mark_stage_complete("stage7_finalize")
        update["status"] = "completed"  # Mark entire workflow as complete
        update.update(add_message(state, "system", f"✅ Workflow Complete! Final presentation: {final_path}"))
        update["artifacts"] = {
            **state.get("artifacts", {}),
            "final_pptx": str(final_path),
            "final_thumbnail": str(thumbnail_prefix) + ".jpg"
        }
        
        return update
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        log_stage_error("stage7_finalize", error_msg)
        update = add_error(state, "stage7_finalize", error_msg)
        update.update(add_message(state, "system", f"❌ Failed Apply Replacements & Finalize: {error_msg}"))
        return update