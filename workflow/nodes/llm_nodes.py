"""
LLM-based nodes for intelligent workflow stages.

These nodes use Claude (via LangChain) to perform tasks that require
understanding, analysis, and content generation.
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

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
    read_text,
    write_text,
    read_json,
    write_json,
)


def get_llm(model: str = "claude-sonnet-4-5", temperature: float = 0.7, max_tokens: int = 32000) -> ChatAnthropic:
    """
    Get configured LLM instance.
    
    Args:
        model: Model name
        temperature: Temperature setting
        max_tokens: Maximum tokens for response
    
    Returns:
        Configured ChatAnthropic instance
    """
    return ChatAnthropic(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )


# Stage 2: Analyze Template (LLM)
def stage2_analyze(state: WorkflowState) -> Dict[str, Any]:
    """
    Stage 2: Analyze Template node.
    
    Uses LLM to analyze template structure and create comprehensive inventory.
    """
    log_stage_start("stage2_analyze: Analyze Template")
    
    try:
        workspace = Path(state["workspace_dir"])
        
        # Read inputs
        template_content_path = workspace / "stage1-extract" / "template-content.md"
        template_content = read_text(str(template_content_path))
        
        # Read metadata if available
        metadata_path = workspace / "stage0-template-intake" / "template-metadata.json"
        metadata = read_json(str(metadata_path)) if metadata_path.exists() else {}
        
        # Build context
        context = f"""# Template Content

{template_content}

# Template Metadata

{json.dumps(metadata, indent=2)}

# Task

Analyze this PowerPoint template and create a comprehensive inventory.
"""
        
        # System prompt
        system_prompt = """You are a PowerPoint template analysis expert.

Analyze the provided template content and metadata to create a comprehensive inventory.

Create a markdown document with:

1. **Total Slide Count** (0-indexed: slide 0 to slide N-1)

2. **For EACH slide:**
   - Slide index (0-based)
   - Layout description (title, multi-column, chart, team grid, etc.)
   - Purpose/use case
   - Special features (colors, highlights, images, placeholders)

3. **Overall Design Elements:**
   - Color scheme (primary, secondary, accent colors)
   - Typography patterns (fonts, sizes, styles)
   - Layout categories and patterns

4. **Recommendations:**
   - Which slides work best for different content types
   - Layout compatibility notes

CRITICAL: Number slides starting from 0. If there are 11 slides, they are indexed 0-10.

Output ONLY the markdown content, no additional commentary."""
        
        # Invoke LLM
        llm = get_llm()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]
        
        print("  Invoking LLM for template analysis...")
        response = llm.invoke(messages)
        inventory_content = response.content
        
        # Save inventory
        inventory_path = workspace / "stage2-analyze" / "template-inventory.md"
        write_text(str(inventory_path), inventory_content)
        
        print(f"  Created inventory: {inventory_path}")
        log_stage_complete("stage2_analyze: Analyze Template")
        
        # Update state
        update = mark_stage_complete("stage2_analyze")
        update.update(add_message(state, "system", "✅ Completed Analyze Template"))
        update["template_inventory"] = inventory_content
        update["artifacts"] = {
            **state.get("artifacts", {}),
            "template_inventory": str(inventory_path)
        }
        
        return update
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        log_stage_error("stage2_analyze", error_msg)
        update = add_error(state, "stage2_analyze", error_msg)
        update.update(add_message(state, "system", f"❌ Failed Analyze Template: {error_msg}"))
        return update


# Stage 3: Create Outline (LLM)
def stage3_outline(state: WorkflowState) -> Dict[str, Any]:
    """
    Stage 3: Create Outline node.
    
    Uses LLM to parse content and create presentation outline with slide mapping.
    """
    log_stage_start("stage3_outline: Create Outline")
    
    try:
        workspace = Path(state["workspace_dir"])
        
        # Read inputs
        source_ingest_path = workspace / "stage0-source-intake" / "source-ingest.md"
        source_content = read_text(str(source_ingest_path))
        
        template_inventory = state.get("template_inventory", "")
        if not template_inventory:
            inventory_path = workspace / "stage2-analyze" / "template-inventory.md"
            template_inventory = read_text(str(inventory_path))
        
        # Build context
        context = f"""# Source Content

{source_content}

# Template Inventory

{template_inventory}

# Task

Create a presentation outline that maps the source content to appropriate template slides.
"""
        
        # System prompt
        system_prompt = """You are a presentation content strategist.

Parse the content document and map it to template slides.

Tasks:
1. Identify main sections from the source content
2. Match content sections to appropriate template slides
3. Validate layout compatibility:
   - 3-column layout → need exactly 3 items
   - 2-column layout → need exactly 2 items
   - Image layout → check for image availability
   - Quote layout → validate attribution present
4. Create slide mapping array (0-indexed template slide numbers)

Output TWO sections in your response:

## OUTLINE

[Create presentation outline in markdown format with:
- Presentation title and theme
- For each output slide:
  * Slide number (in final deck)
  * Template slide index to use
  * Content section from source
  * Key content points]

## MAPPING

[Provide ONLY a JSON array of template slide indices, e.g., [0, 1, 2, 3, 6, 8, 9, 10]]

CRITICAL: Ensure the mapping is a valid JSON array of integers."""
        
        # Invoke LLM
        llm = get_llm()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]
        
        print("  Invoking LLM for outline creation...")
        response = llm.invoke(messages)
        full_response = response.content
        
        # Parse response to extract outline and mapping
        parts = full_response.split("## MAPPING")
        outline_content = parts[0].replace("## OUTLINE", "").strip()
        
        # Extract JSON array from mapping section
        mapping_section = parts[1].strip() if len(parts) > 1 else "[]"
        
        # Find JSON array in mapping section
        import re
        json_match = re.search(r'\[[\d,\s]+\]', mapping_section)
        if json_match:
            mapping_json = json_match.group(0)
            slide_mapping = json.loads(mapping_json)
        else:
            raise ValueError("Could not extract slide mapping from LLM response")
        
        # Save outline
        outline_path = workspace / "stage3-outline" / "outline.md"
        write_text(str(outline_path), outline_content)
        
        # Save mapping as JSON
        mapping_json_path = workspace / "stage3-outline" / "template-mapping.json"
        write_json(str(mapping_json_path), slide_mapping)
        
        # Save mapping as CSV (for compatibility)
        mapping_csv_path = workspace / "stage3-outline" / "template-mapping.txt"
        write_text(str(mapping_csv_path), ",".join(map(str, slide_mapping)))
        
        print(f"  Created outline: {outline_path}")
        print(f"  Created mapping: {mapping_json_path}")
        print(f"  Slide mapping: {slide_mapping}")
        log_stage_complete("stage3_outline: Create Outline")
        
        # Update state
        update = mark_stage_complete("stage3_outline")
        update.update(add_message(state, "system", "✅ Completed Create Outline"))
        update["outline"] = outline_content
        update["slide_mapping"] = slide_mapping
        update["artifacts"] = {
            **state.get("artifacts", {}),
            "outline": str(outline_path),
            "template_mapping_json": str(mapping_json_path),
            "template_mapping_csv": str(mapping_csv_path)
        }
        
        return update
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        log_stage_error("stage3_outline", error_msg)
        update = add_error(state, "stage3_outline", error_msg)
        update.update(add_message(state, "system", f"❌ Failed Create Outline: {error_msg}"))
        return update


# Stage 6: Generate Replacements (LLM)
def stage6_replacements(state: WorkflowState) -> Dict[str, Any]:
    """
    Stage 6: Generate Replacements node.
    
    Uses LLM to generate formatted replacement text for all slides.
    """
    log_stage_start("stage6_replacements: Generate Replacements")
    
    try:
        workspace = Path(state["workspace_dir"])
        
        # Read inputs
        outline = state.get("outline", "")
        if not outline:
            outline_path = workspace / "stage3-outline" / "outline.md"
            outline = read_text(str(outline_path))
        
        source_ingest_path = workspace / "stage0-source-intake" / "source-ingest.md"
        source_content = read_text(str(source_ingest_path))
        
        inventory_path = workspace / "stage5-inventory" / "text-inventory.json"
        text_inventory = read_json(str(inventory_path))
        
        # Build context
        context = f"""# Presentation Outline

{outline}

# Source Content

{source_content}

# Text Inventory

{json.dumps(text_inventory, indent=2)}

# Task

Generate formatted replacement text for ALL slides based on the outline and source content.
"""
        
        # System prompt
        system_prompt = """You are a PowerPoint content generator.

Generate formatted replacement text for all slides.

Tasks:
1. Read the text inventory to understand ALL shapes (slide-N/shape-M)
2. For each slide in the outline:
   - Extract relevant content from source
   - Match content to inventory shapes
   - Generate replacement paragraphs with proper formatting

CRITICAL FORMATTING RULES:
- Headers/titles: Include "bold": true
- Lists: Use "bullet": true, "level": 0 (NO bullet symbols in text)
- Centered text: Include "alignment": "CENTER"
- Preserve font_size, theme_color, or color properties
- ALL shapes from inventory MUST be in replacement JSON (clear if no content)

TEXT LENGTH MANAGEMENT:
- Small shapes (< 3" wide): Short text (< 50 chars)
- Medium shapes (3-6" wide): Moderate text (50-150 chars)
- Large shapes (> 6" wide): Longer text (up to 300 chars)

Output ONLY valid JSON in this exact format:

{
  "slide-0": {
    "shape-0": {
      "paragraphs": [
        {"text": "Title Text", "alignment": "CENTER", "bold": true, "font_size": 44.0}
      ]
    },
    "shape-1": {
      "paragraphs": [
        {"text": "Subtitle", "alignment": "CENTER", "font_size": 18.0}
      ]
    }
  },
  "slide-1": {
    "shape-0": {
      "paragraphs": [
        {"text": "Section Header", "bold": true}
      ]
    }
  }
}

IMPORTANT: 
- Include ALL slides from the inventory
- Include ALL shapes from each slide
- Use empty paragraphs [] to clear shapes with no content
- Do NOT include bullet symbols (•, -, *) in text when bullet: true
- Output ONLY the JSON, no markdown code blocks or explanations"""
        
        # Invoke LLM with higher max_tokens for large JSON output
        llm = get_llm(temperature=0.5, max_tokens=32000)  # Maximum tokens for complete JSON
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]
        
        print("  Invoking LLM for replacement text generation...")
        response = llm.invoke(messages)
        response_content = response.content.strip()
        
        # Clean response (remove markdown code blocks if present)
        if response_content.startswith("```"):
            # Remove markdown code blocks
            lines = response_content.split("\n")
            # Find first and last ``` markers
            start_idx = 0
            end_idx = len(lines)
            for i, line in enumerate(lines):
                if line.strip().startswith("```"):
                    if start_idx == 0:
                        start_idx = i + 1
                    else:
                        end_idx = i
                        break
            response_content = "\n".join(lines[start_idx:end_idx])
        
        # Parse JSON
        try:
            replacement_data = json.loads(response_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM did not return valid JSON: {e}\nResponse: {response_content[:500]}")
        
        # Save replacement JSON
        replacement_path = workspace / "stage6-replacement" / "replacement-text.json"
        write_json(str(replacement_path), replacement_data)
        
        print(f"  Created replacement text: {replacement_path}")
        print(f"  Slides: {len(replacement_data)}, Total shapes: {sum(len(v) for v in replacement_data.values())}")
        log_stage_complete("stage6_replacements: Generate Replacements")
        
        # Update state
        update = mark_stage_complete("stage6_replacements")
        update.update(add_message(state, "system", "✅ Completed Generate Replacements"))
        update["replacement_text"] = replacement_data
        update["artifacts"] = {
            **state.get("artifacts", {}),
            "replacement_text": str(replacement_path)
        }
        
        return update
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        log_stage_error("stage6_replacements", error_msg)
        update = add_error(state, "stage6_replacements", error_msg)
        update.update(add_message(state, "system", f"❌ Failed Generate Replacements: {error_msg}"))
        return update