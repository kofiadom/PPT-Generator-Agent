# Script Testing Guide

This guide walks you through testing each stage's scripts manually to verify they work correctly before implementing the router-based workflow.

## Prerequisites

```powershell
# Ensure you have the required dependencies
pip install python-pptx "markitdown[all]" pillow
```

**Note:** The `markitdown[all]` package includes support for DOCX, PPTX, PDF, and other formats.

**Helper Script:** We've created `scripts/convert_to_markdown.py` as a wrapper for the markitdown Python API since the CLI command may not be available in all environments.

## Test Setup

Create a test workspace:

**Windows PowerShell:**
```powershell
mkdir test_run\stage0-template-intake -Force
mkdir test_run\stage0-source-intake -Force
mkdir test_run\stage1-extract -Force
mkdir test_run\stage2-analyze -Force
mkdir test_run\stage3-outline -Force
mkdir test_run\stage4-rearrange -Force
mkdir test_run\stage5-inventory -Force
mkdir test_run\stage6-replacement -Force
mkdir test_run\stage7-final -Force
```

**Or use a single command:**
```powershell
"stage0-template-intake","stage0-source-intake","stage1-extract","stage2-analyze","stage3-outline","stage4-rearrange","stage5-inventory","stage6-replacement","stage7-final" | ForEach-Object { mkdir "test_run\$_" -Force }
```

---

## Stage 0A: Template Intake (Automated)

**Purpose:** Copy template and extract metadata

```powershell
# Copy template
copy sample_pptx\Consulting.pptx test_run\stage0-template-intake\

# Extract metadata
python scripts/pptx_probe.py test_run\stage0-template-intake\Consulting.pptx test_run\stage0-template-intake\template-metadata.json
```

**Expected Output:**
- `test_run\stage0-template-intake\Consulting.pptx` (copied file)
- `test_run\stage0-template-intake\template-metadata.json` (slide count, dimensions)

**Verify:**
```powershell
Get-Content test_run\stage0-template-intake\template-metadata.json
```

---

## Stage 0B: Source Intake (Automated)

**Purpose:** Copy source document and extract text

```powershell
# Copy source document
copy sample_pptx\Consulting.docx test_run\stage0-source-intake\

# Extract text to markdown
python scripts/convert_to_markdown.py test_run\stage0-source-intake\Consulting.docx test_run\stage0-source-intake\source-ingest.md
```

**Expected Output:**
- `test_run\stage0-source-intake\Consulting.docx` (copied file)
- `test_run\stage0-source-intake\source-ingest.md` (markdown text)

**Verify:**
```powershell
Get-Content test_run\stage0-source-intake\source-ingest.md | Select-Object -First 20
```

---

## Stage 1: Extract Template Content (Automated)

**Purpose:** Extract template text and create thumbnails

```powershell
# Extract text from template
python scripts/convert_to_markdown.py test_run\stage0-template-intake\Consulting.pptx test_run\stage1-extract\template-content.md

# Create thumbnail grid
python scripts/thumbnail.py test_run\stage0-template-intake\Consulting.pptx test_run\stage1-extract\template-thumbnail
```

**Expected Output:**
- `test_run\stage1-extract\template-content.md` (extracted text)
- `test_run\stage1-extract\template-thumbnail.jpg` (visual grid)

**Verify:**
```powershell
# Check text extraction
Get-Content test_run\stage1-extract\template-content.md | Select-Object -First 30

# Check thumbnail exists
Get-Item test_run\stage1-extract\template-thumbnail.jpg
```

---

## Stage 2: Analyze Template (⚠️ MANUAL/LLM)

**Purpose:** Create template inventory document

**This stage requires LLM/human analysis.** For testing, create a minimal inventory:

```powershell
@"
# Template Inventory

**Total Slides:** 11 (indexed 0-10)

## Slide Catalog

- Slide 0: Title/Cover slide
- Slide 1: Section header with subtitle
- Slide 2: Three-column layout
- Slide 3: Two-column layout
- Slide 4: Full-width content
- Slide 5: Quote layout
- Slide 6: Deliverables with highlights
- Slide 7: Process/timeline
- Slide 8: Team grid (4 members)
- Slide 9: Contact/closing
- Slide 10: Thank you slide

## Design Elements
- Primary color: Dark teal (#2C3E50)
- Accent color: Yellow/gold (#F39C12)
- Typography: Sans-serif, clean and modern
"@ | Out-File -FilePath test_run\stage2-analyze\template-inventory.md -Encoding utf8
```

**Expected Output:**
- `test_run\stage2-analyze\template-inventory.md`

**Verify:**
```powershell
Get-Content test_run\stage2-analyze\template-inventory.md
```

---

## Stage 3: Create Outline (⚠️ MANUAL/LLM)

**Purpose:** Create presentation outline and slide mapping

**This stage requires LLM/human strategy.** For testing, create a minimal outline:

```powershell
# Extract content first
python scripts/convert_to_markdown.py test_run\stage0-source-intake\Consulting.docx test_run\stage3-outline\content-extracted.md

# Create outline (manual for now)
@"
# Presentation Outline

## Slide 1: Cover
- Title: Digital Transformation Strategy
- Date: November 2025
- Template: Slide 0

## Slide 2: Overview
- Executive summary
- Template: Slide 1

## Slide 3: Challenge
- Current state issues
- Template: Slide 2

## Slide 4: Solution
- Proposed approach
- Template: Slide 3

## Slide 5: Deliverables
- Key outputs
- Template: Slide 6

## Slide 6: Timeline
- Implementation phases
- Template: Slide 7

## Slide 7: Team
- Project team
- Template: Slide 8

## Slide 8: Closing
- Next steps
- Template: Slide 9
"@ | Out-File -FilePath test_run\stage3-outline\outline.md -Encoding utf8

# Create mapping files
"0,1,2,3,6,7,8,9" | Out-File -FilePath test_run\stage3-outline\template-mapping.txt -Encoding utf8 -NoNewline
'[0,1,2,3,6,7,8,9]' | Out-File -FilePath test_run\stage3-outline\template-mapping.json -Encoding utf8 -NoNewline
```

**Expected Output:**
- `test_run\stage3-outline\content-extracted.md`
- `test_run\stage3-outline\outline.md`
- `test_run\stage3-outline\template-mapping.txt`
- `test_run\stage3-outline\template-mapping.json`

**Verify:**
```powershell
Get-Content test_run\stage3-outline\template-mapping.json
```

---

## Stage 4: Rearrange Slides (Automated)

**Purpose:** Rearrange slides based on mapping

```powershell
# Rearrange slides using mapping
python scripts/rearrange_from_mapping.py test_run\stage0-template-intake\Consulting.pptx test_run\stage4-rearrange\working.pptx test_run\stage3-outline\template-mapping.json

# Create verification thumbnail
python scripts/thumbnail.py test_run\stage4-rearrange\working.pptx test_run\stage4-rearrange\rearranged-slides
```

**Expected Output:**
- `test_run\stage4-rearrange\working.pptx` (8 slides)
- `test_run\stage4-rearrange\rearranged-slides.jpg`

**Verify:**
```powershell
# Check file exists and size
Get-Item test_run\stage4-rearrange\working.pptx

# View thumbnail
Get-Item test_run\stage4-rearrange\rearranged-slides.jpg
```

---

## Stage 5: Extract Text Inventory (Automated)

**Purpose:** Extract all text shapes with formatting

```powershell
python scripts/inventory.py test_run\stage4-rearrange\working.pptx test_run\stage5-inventory\text-inventory.json
```

**Expected Output:**
- `test_run\stage5-inventory\text-inventory.json` (detailed shape inventory)

**Verify:**
```powershell
# Check structure
python -m json.tool test_run\stage5-inventory\text-inventory.json | Select-Object -First 50

# Count shapes
python -c "import json; data=json.load(open('test_run/stage5-inventory/text-inventory.json')); print(f'Slides: {len(data)}, Total shapes: {sum(len(v) for v in data.values())}')"
```

---

## Stage 6: Generate Replacement Text (⚠️ MANUAL/LLM)

**Purpose:** Generate formatted replacement text

**This stage requires LLM/human content generation.** For testing, create minimal replacement:

```powershell
@"
{
  "slide-0": {
    "shape-0": {
      "paragraphs": [
        {
          "text": "Digital Transformation Strategy",
          "alignment": "CENTER",
          "bold": true,
          "font_size": 44.0
        }
      ]
    },
    "shape-1": {
      "paragraphs": [
        {
          "text": "November 2025",
          "alignment": "CENTER",
          "font_size": 18.0
        }
      ]
    }
  },
  "slide-1": {
    "shape-0": {
      "paragraphs": [
        {
          "text": "Executive Overview",
          "bold": true,
          "font_size": 32.0
        }
      ]
    },
    "shape-1": {
      "paragraphs": [
        {
          "text": "Strategic initiative to modernize operations",
          "font_size": 18.0
        }
      ]
    }
  }
}
"@ | Out-File -FilePath test_run\stage6-replacement\replacement-text.json -Encoding utf8
```

**Note:** In production, this JSON should cover ALL shapes from the inventory.

**Expected Output:**
- `test_run\stage6-replacement\replacement-text.json`

**Verify:**
```powershell
python -m json.tool test_run\stage6-replacement\replacement-text.json | Select-Object -First 30
```

---

## Stage 7: Apply Replacements (Automated)

**Purpose:** Apply text replacements and create final presentation

```powershell
# Apply replacements
python scripts/replace.py test_run\stage4-rearrange\working.pptx test_run\stage6-replacement\replacement-text.json test_run\stage7-final\output.pptx

# Create final thumbnail
python scripts/thumbnail.py test_run\stage7-final\output.pptx test_run\stage7-final\final-presentation
```

**Expected Output:**
- `test_run\stage7-final\output.pptx` (final presentation)
- `test_run\stage7-final\final-presentation.jpg`

**Verify:**
```powershell
# Check file exists
Get-Item test_run\stage7-final\output.pptx

# View thumbnail
Get-Item test_run\stage7-final\final-presentation.jpg
```

---

## Complete Test Script (PowerShell)

Save as `test_workflow.ps1` and run all automated stages in sequence:

```powershell
# test_workflow.ps1
$ErrorActionPreference = "Stop"

Write-Host "=== Stage 0A: Template Intake ===" -ForegroundColor Green
copy sample_pptx\Consulting.pptx test_run\stage0-template-intake\
python scripts/pptx_probe.py test_run\stage0-template-intake\Consulting.pptx test_run\stage0-template-intake\template-metadata.json

Write-Host "=== Stage 0B: Source Intake ===" -ForegroundColor Green
copy sample_pptx\Consulting.docx test_run\stage0-source-intake\
python scripts/convert_to_markdown.py test_run\stage0-source-intake\Consulting.docx test_run\stage0-source-intake\source-ingest.md

Write-Host "=== Stage 1: Extract Template ===" -ForegroundColor Green
python scripts/convert_to_markdown.py test_run\stage0-template-intake\Consulting.pptx test_run\stage1-extract\template-content.md
python scripts/thumbnail.py test_run\stage0-template-intake\Consulting.pptx test_run\stage1-extract\template-thumbnail

Write-Host "=== Stage 2: Analyze Template (MANUAL) ===" -ForegroundColor Yellow
Write-Host "Create test_run\stage2-analyze\template-inventory.md manually"

Write-Host "=== Stage 3: Create Outline (MANUAL) ===" -ForegroundColor Yellow
python scripts/convert_to_markdown.py test_run\stage0-source-intake\Consulting.docx test_run\stage3-outline\content-extracted.md
Write-Host "Create outline.md and mapping files manually"

Write-Host "=== Stage 4: Rearrange Slides ===" -ForegroundColor Green
python scripts/rearrange_from_mapping.py test_run\stage0-template-intake\Consulting.pptx test_run\stage4-rearrange\working.pptx test_run\stage3-outline\template-mapping.json
python scripts/thumbnail.py test_run\stage4-rearrange\working.pptx test_run\stage4-rearrange\rearranged-slides

Write-Host "=== Stage 5: Text Inventory ===" -ForegroundColor Green
python scripts/inventory.py test_run\stage4-rearrange\working.pptx test_run\stage5-inventory\text-inventory.json

Write-Host "=== Stage 6: Generate Replacements (MANUAL) ===" -ForegroundColor Yellow
Write-Host "Create test_run\stage6-replacement\replacement-text.json manually"

Write-Host "=== Stage 7: Apply Replacements ===" -ForegroundColor Green
python scripts/replace.py test_run\stage4-rearrange\working.pptx test_run\stage6-replacement\replacement-text.json test_run\stage7-final\output.pptx
python scripts/thumbnail.py test_run\stage7-final\output.pptx test_run\stage7-final\final-presentation

Write-Host "=== COMPLETE ===" -ForegroundColor Green
```

Run with:
```powershell
.\test_workflow.ps1
```

---

## Validation Checklist

After running all stages, verify:

- [ ] Stage 0A: `template-metadata.json` contains slide count
- [ ] Stage 0B: `source-ingest.md` contains readable text
- [ ] Stage 1: `template-content.md` and `template-thumbnail.jpg` exist
- [ ] Stage 2: `template-inventory.md` lists all slides
- [ ] Stage 3: `template-mapping.json` is valid JSON array
- [ ] Stage 4: `working.pptx` has correct number of slides
- [ ] Stage 5: `text-inventory.json` contains shape data
- [ ] Stage 6: `replacement-text.json` matches inventory structure
- [ ] Stage 7: `output.pptx` opens in PowerPoint without errors

---

## Next Steps

Once all scripts work correctly:

1. ✅ Scripts are validated
2. ✅ Stage dependencies are clear
3. ✅ LLM stages are identified (2, 3, 6)
4. ➡️ Build router-based workflow framework
5. ➡️ Integrate LLM for stages 2, 3, 6
6. ➡️ Add state management and checkpointing