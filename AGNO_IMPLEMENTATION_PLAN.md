# Agno Implementation Plan for PPTX Workflow

## Overview

This document outlines how to implement the PPTX generation workflow using Agno, a Python framework for building multi-agent systems with shared memory and state management.

## Agno vs LangGraph Comparison

| Feature | LangGraph | Agno |
|---------|-----------|------|
| **State Management** | TypedDict with reducers | `session_state` dict |
| **Routing** | Conditional edges | `Router` with selector functions |
| **Checkpointing** | SQLite/Postgres | Built-in with `db` parameter |
| **Agents** | Custom node functions | `Agent` class with tools |
| **Workflow** | `StateGraph` | `Workflow` with `Step` sequence |
| **LLM Integration** | LangChain models | OpenAI/Anthropic via `model` parameter |

---

## Architecture Design

### **Agno Workflow Structure**

```python
from agno.workflow import Workflow, Step, Router
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

workflow = Workflow(
    name="PPTX Generation",
    db=SqliteDb(db_file="pptx_workflow.db"),
    session_state={
        "template_path": None,
        "source_path": None,
        "current_stage": "start",
        "completed_stages": [],
        "artifacts": {}
    },
    steps=[
        # Stages defined here
    ]
)
```

---

## Implementation Approach

### **Option 1: Sequential Steps (Simpler)**

Use Agno's sequential `Step` execution with agents for each stage:

```python
workflow = Workflow(
    name="PPTX Generation",
    db=SqliteDb(db_file="pptx_workflow.db"),
    steps=[
        Step(name="Template Intake", agent=template_intake_agent),
        Step(name="Source Intake", agent=source_intake_agent),
        Step(name="Extract Template", agent=extract_agent),
        Step(name="Analyze Template", agent=analyze_agent),  # LLM
        Step(name="Create Outline", agent=outline_agent),    # LLM
        Step(name="Rearrange Slides", agent=rearrange_agent),
        Step(name="Text Inventory", agent=inventory_agent),
        Step(name="Generate Replacements", agent=replacement_agent),  # LLM
        Step(name="Finalize", agent=finalize_agent),
    ],
    add_workflow_history_to_steps=True  # Enables state continuity
)
```

### **Option 2: Router-Based (More Flexible)**

Use `Router` for conditional routing based on state:

```python
def route_next_stage(step_input: StepInput, session_state: dict) -> Step:
    """Route to next stage based on completed stages."""
    completed = set(session_state.get("completed_stages", []))
    
    if "stage0a" not in completed:
        return stage0a_step
    elif "stage0b" not in completed:
        return stage0b_step
    # ... etc
    
workflow = Workflow(
    name="PPTX Generation",
    db=SqliteDb(db_file="pptx_workflow.db"),
    steps=[
        Router(
            name="Stage Router",
            selector=route_next_stage,
            choices=[stage0a_step, stage0b_step, stage1_step, ...]
        )
    ],
    session_state={"completed_stages": [], "artifacts": {}}
)
```

---

## Agent Definitions

### **Script-Based Agents (Stages 0A, 0B, 1, 4, 5, 7)**

For script execution stages, create agents with custom tools:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
import subprocess
from pathlib import Path

def run_pptx_probe(session_state, template_path: str, output_path: str) -> str:
    """Tool to run pptx_probe.py script."""
    cmd = [
        "python",
        "scripts/pptx_probe.py",
        template_path,
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return f"Error: {result.stderr}"
    
    # Update session state
    session_state["artifacts"]["template_metadata"] = output_path
    session_state["completed_stages"].append("stage0a")
    
    return f"Metadata extracted to {output_path}"

# Create agent with tool
template_intake_agent = Agent(
    name="Template Intake Agent",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[run_pptx_probe],
    instructions=[
        "You are responsible for template intake.",
        "Use the run_pptx_probe tool to extract template metadata.",
        "Update session state with artifact paths."
    ],
    session_state={}  # Will be merged with workflow session_state
)
```

### **LLM-Based Agents (Stages 2, 3, 6)**

For LLM stages, use Agno agents with Anthropic models:

```python
from agno.models.anthropic import Claude

analyze_agent = Agent(
    name="Template Analyzer",
    model=Claude(id="claude-sonnet-4-5"),
    instructions=[
        "You are a PowerPoint template analysis expert.",
        "Analyze the template content and create a comprehensive inventory.",
        "Output a markdown document with slide catalog and design elements.",
        "Number slides starting from 0."
    ],
    output_schema=None,  # Or define Pydantic model for structured output
)

outline_agent = Agent(
    name="Content Strategist",
    model=Claude(id="claude-sonnet-4-5"),
    instructions=[
        "You are a presentation content strategist.",
        "Map source content to template slides.",
        "Create outline and slide mapping array.",
        "Validate layout compatibility."
    ],
)

replacement_agent = Agent(
    name="Content Generator",
    model=Claude(id="claude-sonnet-4-5", max_tokens=32000),
    instructions=[
        "You are a PowerPoint content generator.",
        "Generate formatted replacement text for all slides.",
        "Output valid JSON with all shapes from inventory.",
        "Preserve formatting and prevent text overflow."
    ],
)
```

---

## Complete Agno Implementation

```python
from agno.workflow import Workflow, Step, Router
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from typing import List

# Database for persistence
db = SqliteDb(db_file="pptx_workflow.db")

# Define all agents (script + LLM)
# ... (agent definitions from above)

# Define steps
stage0a_step = Step(name="Template Intake", agent=template_intake_agent)
stage0b_step = Step(name="Source Intake", agent=source_intake_agent)
stage1_step = Step(name="Extract Template", agent=extract_agent)
stage2_step = Step(name="Analyze Template", agent=analyze_agent)
stage3_step = Step(name="Create Outline", agent=outline_agent)
stage4_step = Step(name="Rearrange Slides", agent=rearrange_agent)
stage5_step = Step(name="Text Inventory", agent=inventory_agent)
stage6_step = Step(name="Generate Replacements", agent=replacement_agent)
stage7_step = Step(name="Finalize", agent=finalize_agent)

# Create workflow
pptx_workflow = Workflow(
    name="PPTX Generation Workflow",
    description="Automated PowerPoint generation from templates",
    db=db,
    steps=[
        stage0a_step,
        stage0b_step,
        stage1_step,
        stage2_step,
        stage3_step,
        stage4_step,
        stage5_step,
        stage6_step,
        stage7_step,
    ],
    session_state={
        "template_path": None,
        "source_path": None,
        "output_name": None,
        "workspace_dir": None,
        "completed_stages": [],
        "artifacts": {},
        "errors": []
    },
    add_workflow_history_to_steps=True  # Enable state continuity
)

# Execute workflow
pptx_workflow.print_response(
    input="Generate presentation from template.pptx and content.docx",
    session_id="session-123",
    user_id="user-456",
    session_state={
        "template_path": "sample_pptx/Consulting.pptx",
        "source_path": "sample_pptx/Consulting.docx",
        "output_name": "Output-Presentation",
        "workspace_dir": "outputs/workflow_123"
    },
    stream=True
)
```

---

## Key Differences from LangGraph

### **1. State Management**

**LangGraph:**
```python
class WorkflowState(TypedDict):
    completed_stages: Annotated[List[str], add]  # Reducer
```

**Agno:**
```python
session_state = {
    "completed_stages": []  # Direct dict manipulation
}
# Agents/tools modify session_state directly
```

### **2. Routing**

**LangGraph:**
```python
def router(state: WorkflowState) -> Literal["stage1", "stage2", END]:
    # Return node name
    
builder.add_conditional_edges("router", router, {...})
```

**Agno:**
```python
def route_next_stage(step_input: StepInput, session_state: dict) -> Step:
    # Return Step object
    
Router(selector=route_next_stage, choices=[step1, step2, ...])
```

### **3. Agents**

**LangGraph:**
```python
def stage_node(state: WorkflowState) -> Dict[str, Any]:
    # Custom function
    llm = ChatAnthropic(...)
    response = llm.invoke(...)
    return {"completed_stages": ["stage1"]}
```

**Agno:**
```python
agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    tools=[custom_tool],
    instructions="...",
    session_state={}
)
```

---

## Recommended Approach

### **For PPTX Workflow: Use Sequential Steps**

Given that the PPTX workflow has clear dependencies and linear progression, **Option 1 (Sequential Steps)** is recommended:

**Advantages:**
- ✅ Simpler implementation
- ✅ Clear stage progression
- ✅ Built-in state management
- ✅ Automatic history tracking
- ✅ Less code than router-based approach

**Implementation:**
1. Create 9 agents (one per stage)
2. Script stages use tools that execute subprocess commands
3. LLM stages use Claude models directly
4. Sequential `Step` execution with `add_workflow_history_to_steps=True`
5. Session state tracks progress and artifacts

---

## Migration from LangGraph

To migrate the existing LangGraph implementation to Agno:

1. **Convert State Schema** → `session_state` dict
2. **Convert Router** → `Router` with selector function (or remove for sequential)
3. **Convert Nodes** → `Agent` instances with tools
4. **Convert Graph** → `Workflow` with `Step` sequence
5. **Convert Checkpointer** → `db` parameter with `SqliteDb`

**Estimated effort:** 2-3 days (most code can be reused, just wrapped differently)

---

## Next Steps

1. **Decide on approach**: Sequential vs Router-based
2. **Create agent definitions** for all 9 stages
3. **Implement tools** for script execution
4. **Build workflow** with steps
5. **Test** with sample data
6. **Compare** with LangGraph implementation

---

## Recommendation

**Keep LangGraph as primary implementation** because:
- ✅ Already working perfectly
- ✅ More mature ecosystem
- ✅ Better documentation
- ✅ More flexible routing
- ✅ Production-tested

**Use Agno as alternative** if:
- Need simpler agent-based abstraction
- Prefer built-in agent tools
- Want integrated memory management
- Require multi-agent collaboration features

Both frameworks can coexist in the repository for different use cases.