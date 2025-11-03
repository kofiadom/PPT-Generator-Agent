# Setup and Testing Guide

This guide walks you through setting up and testing the LangGraph-based PPTX workflow.

## Prerequisites

- Python 3.10 or higher (you have 3.13.2 ✅)
- Anthropic API key
- Sample files in `sample_pptx/` directory

## Step 1: Install Dependencies

```powershell
# Ensure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt
```

**Expected packages:**
- `langgraph` - State machine framework
- `langchain-core` - LangChain core
- `langchain-anthropic` - Claude integration
- `python-pptx` - PowerPoint processing
- `pillow` - Image processing
- `markitdown` - Document conversion
- `python-dotenv` - Environment variables

## Step 2: Configure Environment

```powershell
# Copy environment template
copy .env.example .env

# Edit .env and add your Anthropic API key
notepad .env
```

**Required in `.env`:**
```
ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
DATABASE_URL=checkpoints.db
```

## Step 3: Verify Installation

```powershell
# Test imports
python -c "from workflow import WorkflowState, create_initial_state; print('✅ Workflow package OK')"

# Test LangGraph
python -c "from langgraph.graph import StateGraph; print('✅ LangGraph OK')"

# Test Claude
python -c "from langchain_anthropic import ChatAnthropic; print('✅ LangChain Anthropic OK')"

# Test scripts
python scripts/pptx_probe.py sample_pptx/Consulting.pptx test_metadata.json
python -c "import json; print('✅ Scripts OK'); import os; os.remove('test_metadata.json')"
```

## Step 4: Run Example Workflow

### Option A: Using Example Script (Recommended)

```powershell
# Run the example
python example_usage.py
```

**Expected output:**
```
============================================================
PowerPoint Workflow - Example Execution
============================================================
Workflow ID: workflow_abc12345
Thread ID: thread_xyz67890
Template: sample_pptx/Consulting.pptx
Source: sample_pptx/Consulting.docx
Output: Example-Presentation.pptx
Workspace: outputs/workflow_abc12345
============================================================

Building workflow graph...
Using SQLite checkpointer: checkpoints.db
✅ Workflow graph compiled successfully

🚀 Starting workflow execution...

[Router] Routing to: stage0a_template_intake
[stage0a_template_intake] ✅ Completed Template Intake
[Router] Routing to: stage0b_source_intake
[stage0b_source_intake] ✅ Completed Source Intake
[Router] Routing to: stage1_extract
[stage1_extract] ✅ Completed Extract Template Content
[Router] Routing to: stage2_analyze
[stage2_analyze] ✅ Completed Analyze Template
[Router] Routing to: stage3_outline
[stage3_outline] ✅ Completed Create Outline
[Router] Routing to: stage4_rearrange
[stage4_rearrange] ✅ Completed Rearrange Slides
[Router] Routing to: stage5_inventory
[stage5_inventory] ✅ Completed Extract Text Inventory
[Router] Routing to: stage6_replacements
[stage6_replacements] ✅ Completed Generate Replacements
[Router] Routing to: stage7_finalize
[stage7_finalize] ✅ Workflow Complete! Final presentation: outputs/workflow_abc12345/stage7-final/Example-Presentation.pptx

============================================================
✅ Workflow Completed Successfully!
============================================================
📊 Final Presentation: outputs/workflow_abc12345/stage7-final/Example-Presentation.pptx
🖼️  Thumbnail: outputs/workflow_abc12345/stage7-final/final-presentation.jpg
============================================================
```

### Option B: Using CLI

```powershell
python -m workflow.cli `
  --template sample_pptx/Consulting.pptx `
  --source sample_pptx/Consulting.docx `
  --output "CLI-Test-Presentation"
```

## Step 5: Verify Outputs

```powershell
# Check workspace was created
ls outputs/

# Check final presentation
ls outputs/workflow_*/stage7-final/*.pptx

# View thumbnail
start outputs/workflow_*/stage7-final/final-presentation.jpg

# Open final presentation
start outputs/workflow_*/stage7-final/*.pptx
```

## Step 6: Test Resume Capability

```powershell
# List checkpoints (use actual thread ID from previous run)
python -m workflow.cli --list-checkpoints thread-xyz67890

# Get current state
python -m workflow.cli --get-state thread-xyz67890

# Resume from checkpoint (if workflow was interrupted)
python -m workflow.cli --resume thread-xyz67890
```

## Troubleshooting

### Issue: "No module named 'langgraph'"

**Solution:**
```powershell
pip install langgraph langchain-core langchain-anthropic
```

### Issue: "ANTHROPIC_API_KEY not found"

**Solution:**
```powershell
# Create .env file
copy .env.example .env

# Edit and add your API key
notepad .env
```

### Issue: "markitdown not working"

**Solution:**
```powershell
# Reinstall from GitHub
pip uninstall markitdown -y
pip install git+https://github.com/microsoft/markitdown.git
```

### Issue: "Template file not found"

**Solution:**
```powershell
# Verify sample files exist
ls sample_pptx/

# Use absolute paths if needed
python -m workflow.cli --template "D:\RGT\pptx\pptx\sample_pptx\Consulting.pptx" --source "D:\RGT\pptx\pptx\sample_pptx\Consulting.docx" --output "Test"
```

### Issue: Script execution fails

**Solution:**
```powershell
# Test scripts individually first (see TEST_SCRIPTS.md)
python scripts/pptx_probe.py sample_pptx/Consulting.pptx test.json
python scripts/convert_to_markdown.py sample_pptx/Consulting.docx test.md
```

## Testing Checklist

- [ ] Dependencies installed successfully
- [ ] Environment configured (.env file created)
- [ ] Imports work (workflow, langgraph, langchain)
- [ ] Scripts work individually
- [ ] Example workflow runs without errors
- [ ] All 9 stages complete successfully
- [ ] Final PPTX file created
- [ ] Thumbnail generated
- [ ] Checkpoints saved to checkpoints.db
- [ ] Resume capability works
- [ ] State inspection works

## Expected Workflow Duration

- **Stage 0A-0B**: ~5 seconds (file operations)
- **Stage 1**: ~10 seconds (extraction + thumbnails)
- **Stage 2**: ~30-60 seconds (LLM analysis)
- **Stage 3**: ~45-90 seconds (LLM outline)
- **Stage 4-5**: ~15 seconds (rearrange + inventory)
- **Stage 6**: ~60-120 seconds (LLM content generation)
- **Stage 7**: ~20 seconds (apply + finalize)

**Total**: ~3-5 minutes for complete workflow

## Next Steps After Testing

Once testing is successful:

1. ✅ Verify all stages work correctly
2. ✅ Check final PPTX quality
3. ✅ Test resume capability
4. ✅ Test error handling (try with invalid files)
5. ✅ Optimize LLM prompts if needed
6. ✅ Add unit tests (optional)
7. ✅ Deploy to production (optional)

## Production Deployment (Optional)

For production use with PostgreSQL:

```powershell
# Install PostgreSQL dependency
pip install psycopg2-binary

# Update .env
DATABASE_URL=postgresql://user:pass@host:5432/pptx_workflow

# Run with postgres
python -m workflow.cli --db-type postgres --template ... --source ... --output ...
```

---

**Ready to test!** 🚀

Start with: `python example_usage.py`