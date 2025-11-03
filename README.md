# PowerPoint Workflow with LangGraph

A stateful, router-based workflow system for generating professional PowerPoint presentations from templates and source documents using LangGraph and Claude AI.

## Features

- 🤖 **LLM-Powered** - Uses Claude for template analysis, outline creation, and content generation
- 🔄 **Stateful Workflow** - LangGraph state machine with automatic routing
- 💾 **Checkpointing** - SQLite-based persistence for resume capability
- 🎯 **9-Stage Pipeline** - Automated extraction, analysis, rearrangement, and finalization
- 🛠️ **CLI & API** - Command-line interface and programmatic usage
- ✅ **Error Handling** - Automatic error capture and recovery

## Quick Start

### Installation

```bash
# Create virtual environment (Python 3.10+)
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Anthropic API key
ANTHROPIC_API_KEY=your_api_key_here
```

### Run Example

```bash
# Using example script
python example_usage.py

# Using CLI
python -m workflow.cli --template sample_pptx/Consulting.pptx --source sample_pptx/Consulting.docx --output "My-Presentation"
```

## Workflow Stages

| Stage | Type | Description |
|-------|------|-------------|
| 0A | Script | Template intake and metadata extraction |
| 0B | Script | Source document intake and text extraction |
| 1 | Script | Extract template content and create thumbnails |
| 2 | LLM 🤖 | Analyze template structure (Claude) |
| 3 | LLM 🤖 | Create presentation outline and slide mapping (Claude) |
| 4 | Script | Rearrange slides based on mapping |
| 5 | Script | Extract text inventory with formatting |
| 6 | LLM 🤖 | Generate formatted replacement text (Claude) |
| 7 | Script | Apply replacements and create final PPTX |

## Project Structure

```
pptx/
├── workflow/              # LangGraph workflow implementation
│   ├── state.py          # State schema and helpers
│   ├── router.py         # Routing logic
│   ├── graph.py          # Graph construction
│   ├── cli.py            # Command-line interface
│   └── nodes/            # Stage node implementations
├── scripts/              # Utility scripts
├── sample_pptx/          # Sample template and document
├── requirements.txt      # Python dependencies
└── example_usage.py      # Example usage
```

## Documentation

- [`SETUP_AND_TEST.md`](SETUP_AND_TEST.md) - Detailed setup and testing guide
- [`TEST_SCRIPTS.md`](TEST_SCRIPTS.md) - Individual script testing
- [`WORKFLOW_SUMMARY.md`](WORKFLOW_SUMMARY.md) - Stage-by-stage workflow reference

## CLI Usage

```bash
# New workflow
python -m workflow.cli --template template.pptx --source content.docx --output "Presentation"

# Resume from checkpoint
python -m workflow.cli --resume thread-abc123

# List checkpoints
python -m workflow.cli --list-checkpoints thread-abc123

# Get current state
python -m workflow.cli --get-state thread-abc123
```


## Requirements

- Python 3.10 or higher
- Anthropic API key
- Dependencies in `requirements.txt`

## License

MIT License

## Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Uses [Claude](https://www.anthropic.com/claude) for LLM stages
- PowerPoint processing via [python-pptx](https://python-pptx.readthedocs.io/)