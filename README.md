# BluePipe AI Backend

BluePipe AI backend is a FastAPI plumbing plan analysis service. It provides a simple health check endpoint and a mock analysis endpoint for uploaded PDF or image plan files.

## Quick Start

1. Create and activate a virtual environment if desired.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the API locally:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Returns service status metadata |
| `POST` | `/api/analyze` | Accepts a multipart file upload in field `file` and returns mock plumbing analysis data |

## curl Tests

```bash
curl http://localhost:8000/health
```

```bash
curl -X POST http://localhost:8000/api/analyze -F "file=@your_plan.pdf"
```

## Docker Usage

Build the image:

```bash
docker build -t bluepipe-ai-backend .
```

Run the container:

```bash
docker run --rm -p 8000:8000 bluepipe-ai-backend
```

## Response Schema

`POST /api/analyze` returns JSON with this shape:

```json
{
  "fixtures": [
    {
      "id": "F-001",
      "type": "Water Closet",
      "count": 14,
      "location": "Zone A – Restroom Bank 1"
    },
    {
      "id": "F-002",
      "type": "Lavatory",
      "count": 18,
      "location": "Zone A/B – All Restrooms"
    },
    {
      "id": "F-003",
      "type": "Floor Drain",
      "count": 6,
      "location": "Zone C – Utility Rooms"
    },
    {
      "id": "F-004",
      "type": "Janitor Sink",
      "count": 2,
      "location": "Zone C – Janitor Closets"
    },
    {
      "id": "F-005",
      "type": "Hose Bibb",
      "count": 4,
      "location": "Perimeter – Exterior Walls"
    },
    {
      "id": "F-006",
      "type": "Water Heater",
      "count": 1,
      "location": "Zone D – Mechanical Room"
    }
  ],
  "kpis": {
    "total_fixtures": 45,
    "flagged_count": 3,
    "pipe_runs_estimated": 127,
    "estimated_labor_hrs": 312
  },
  "flagged_issues": [
    {
      "severity": "high",
      "description": "Cleanout missing at base of main waste stack – east restroom bank",
      "page": 3
    },
    {
      "severity": "medium",
      "description": "Water heater recirculation return unlabeled between sheets P5.1 and P5.2",
      "page": 5
    },
    {
      "severity": "low",
      "description": "Trap primer coverage incomplete for floor drains in janitor closet",
      "page": 7
    }
  ],
  "summary": "Analysis of your_plan.pdf identified 45 fixtures across 6 types. 3 issues flagged for engineer review. Estimated 127 pipe run segments and 312 labor hours for installation."
}
```

The response keys and structure stay consistent, while fixture counts and derived KPI totals can shift slightly based on uploaded file size.

## Notes

Smart mock returns realistic plumbing data — swap `smart_mock_analysis()` for real AI inference.
