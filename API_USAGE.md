# FastAPI Usage Guide

This guide shows how to use the PPTX workflow via the REST API.

## Starting the Server

```bash
# Install FastAPI dependencies
pip install fastapi uvicorn python-multipart

# Start the server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

**Interactive docs:** `http://localhost:8000/docs`

---

## API Endpoints

### 1. Create Workflow

**POST** `/api/v1/workflows`

Upload template and source files to start a new workflow.

```bash
curl -X POST "http://localhost:8000/api/v1/workflows" \
  -F "template=@sample_pptx/Consulting.pptx" \
  -F "source=@sample_pptx/Consulting.docx" \
  -F "output_name=My-Presentation"
```

**Response:**
```json
{
  "workflow_id": "workflow_abc123",
  "thread_id": "thread_xyz789",
  "workspace_dir": "outputs/workflow_abc123",
  "status": "started",
  "message": "Workflow started. Use thread_id 'thread_xyz789' to check status."
}
```

---

### 2. Get Workflow Status

**GET** `/api/v1/workflows/{thread_id}/status`

Check the current status of a workflow.

```bash
curl "http://localhost:8000/api/v1/workflows/thread_xyz789/status"
```

**Response:**
```json
{
  "workflow_id": "workflow_abc123",
  "thread_id": "thread_xyz789",
  "current_stage": "stage6_replacements",
  "status": "in_progress",
  "completed_stages": [
    "stage0a_template_intake",
    "stage0b_source_intake",
    "stage1_extract",
    "stage2_analyze",
    "stage3_outline",
    "stage4_rearrange",
    "stage5_inventory"
  ],
  "failed_stages": [],
  "artifacts": {
    "template_pptx": "outputs/workflow_abc123/stage0-template-intake/Consulting.pptx",
    "template_metadata": "outputs/workflow_abc123/stage0-template-intake/template-metadata.json",
    ...
  },
  "errors": []
}
```

---

### 3. List Checkpoints

**GET** `/api/v1/workflows/{thread_id}/checkpoints?limit=10`

List all checkpoints for a workflow (for debugging/time-travel).

```bash
curl "http://localhost:8000/api/v1/workflows/thread_xyz789/checkpoints?limit=5"
```

**Response:**
```json
[
  {
    "checkpoint_id": "1ef4f797-8335-6428-8001-8a1503f9b875",
    "current_stage": "stage7_finalize",
    "status": "completed",
    "completed_count": 9
  },
  {
    "checkpoint_id": "1ef4f797-8335-6428-8001-8a1503f9b874",
    "current_stage": "stage6_replacements",
    "status": "in_progress",
    "completed_count": 8
  }
]
```

---

### 4. Download Result

**GET** `/api/v1/workflows/{thread_id}/result`

Download the final PowerPoint file (only available when status is "completed").

```bash
curl -O "http://localhost:8000/api/v1/workflows/thread_xyz789/result"
```

Returns the `.pptx` file for download.

---

### 5. Get Thumbnail

**GET** `/api/v1/workflows/{thread_id}/thumbnail`

Get the thumbnail preview image of the final presentation.

```bash
curl -O "http://localhost:8000/api/v1/workflows/thread_xyz789/thumbnail"
```

Returns a `.jpg` thumbnail grid.

---

### 6. Cancel Workflow

**DELETE** `/api/v1/workflows/{thread_id}`

Cancel a running workflow.

```bash
curl -X DELETE "http://localhost:8000/api/v1/workflows/thread_xyz789"
```

---

## Python Client Example

```python
import requests
import time

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

# 1. Create workflow
with open("template.pptx", "rb") as template, open("content.docx", "rb") as source:
    response = requests.post(
        f"{BASE_URL}/workflows",
        files={
            "template": template,
            "source": source
        },
        data={"output_name": "My-Presentation"}
    )

result = response.json()
thread_id = result["thread_id"]
print(f"Workflow started: {thread_id}")

# 2. Poll for completion
while True:
    status_response = requests.get(f"{BASE_URL}/workflows/{thread_id}/status")
    status = status_response.json()
    
    print(f"Status: {status['status']}, Stage: {status['current_stage']}")
    
    if status["status"] == "completed":
        print("✅ Workflow completed!")
        break
    elif status["status"] == "failed":
        print("❌ Workflow failed!")
        print(f"Errors: {status['errors']}")
        break
    
    time.sleep(5)  # Poll every 5 seconds

# 3. Download result
if status["status"] == "completed":
    result_response = requests.get(f"{BASE_URL}/workflows/{thread_id}/result")
    
    with open("output.pptx", "wb") as f:
        f.write(result_response.content)
    
    print("📊 Downloaded: output.pptx")
```

---

## JavaScript/TypeScript Client Example

```typescript
// Create workflow
const formData = new FormData();
formData.append('template', templateFile);
formData.append('source', sourceFile);
formData.append('output_name', 'My-Presentation');

const createResponse = await fetch('http://localhost:8000/api/v1/workflows', {
  method: 'POST',
  body: formData
});

const { thread_id } = await createResponse.json();

// Poll for status
const pollStatus = async () => {
  const response = await fetch(`http://localhost:8000/api/v1/workflows/${thread_id}/status`);
  const status = await response.json();
  
  console.log(`Status: ${status.status}, Stage: ${status.current_stage}`);
  
  if (status.status === 'completed') {
    // Download result
    const resultResponse = await fetch(`http://localhost:8000/api/v1/workflows/${thread_id}/result`);
    const blob = await resultResponse.blob();
    
    // Trigger download
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'presentation.pptx';
    a.click();
  } else if (status.status !== 'failed') {
    setTimeout(pollStatus, 5000);  // Poll every 5 seconds
  }
};

pollStatus();
```

---

## Testing the API

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Create workflow
curl -X POST "http://localhost:8000/api/v1/workflows" \
  -F "template=@sample_pptx/Consulting.pptx" \
  -F "source=@sample_pptx/Consulting.docx" \
  -F "output_name=Test-Presentation"

# Get status (replace with actual thread_id)
curl "http://localhost:8000/api/v1/workflows/thread_xyz789/status"

# Download result
curl -O "http://localhost:8000/api/v1/workflows/thread_xyz789/result"
```

### Using Swagger UI

1. Start the server
2. Open `http://localhost:8000/docs`
3. Try out endpoints interactively

---

## Production Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t pptx-workflow-api .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your_key pptx-workflow-api
```

### Using Gunicorn (Production)

```bash
pip install gunicorn

gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

---

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your_api_key_here

# Optional
DATABASE_URL=checkpoints.db
WORKSPACE_ROOT=outputs
```

---

## Error Handling

The API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad request (e.g., workflow not completed)
- `404` - Not found (e.g., invalid thread_id)
- `500` - Server error

**Example error response:**
```json
{
  "detail": "Workflow not found: thread_invalid123"
}