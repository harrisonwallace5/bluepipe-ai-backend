from typing import Any, Dict, List
import random

import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware


SERVICE_NAME = "bluepipe-ai-backend"
SERVICE_VERSION = "1.0.0"


app = FastAPI(title="BluePipe AI Backend", version=SERVICE_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def smart_mock_analysis(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    base_fixtures: List[Dict[str, Any]] = [
        {
            "id": "F-001",
            "type": "Water Closet",
            "count": 14,
            "location": "Zone A – Restroom Bank 1",
        },
        {
            "id": "F-002",
            "type": "Lavatory",
            "count": 18,
            "location": "Zone A/B – All Restrooms",
        },
        {
            "id": "F-003",
            "type": "Floor Drain",
            "count": 6,
            "location": "Zone C – Utility Rooms",
        },
        {
            "id": "F-004",
            "type": "Janitor Sink",
            "count": 2,
            "location": "Zone C – Janitor Closets",
        },
        {
            "id": "F-005",
            "type": "Hose Bibb",
            "count": 4,
            "location": "Perimeter – Exterior Walls",
        },
        {
            "id": "F-006",
            "type": "Water Heater",
            "count": 1,
            "location": "Zone D – Mechanical Room",
        },
    ]

    byte_signature = len(file_bytes) % 10
    rng = random.Random(len(file_bytes))
    adjustment_pool = [-1, 0, 0, 1, 1, 2]

    fixtures: List[Dict[str, Any]] = []
    for index, fixture in enumerate(base_fixtures):
        count = fixture["count"]
        if byte_signature:
            adjustment = adjustment_pool[(byte_signature + index + rng.randint(0, 2)) % len(adjustment_pool)]
            count = max(1, count + adjustment)
        fixtures.append({**fixture, "count": count})

    total_fixtures = sum(item["count"] for item in fixtures)
    flagged_count = 3
    pipe_runs_estimated = 127 + (byte_signature * 2)
    estimated_labor_hrs = 312 + (byte_signature * 4)

    return {
        "fixtures": fixtures,
        "kpis": {
            "total_fixtures": total_fixtures,
            "flagged_count": flagged_count,
            "pipe_runs_estimated": pipe_runs_estimated,
            "estimated_labor_hrs": estimated_labor_hrs,
        },
        "flagged_issues": [
            {
                "severity": "high",
                "description": "Cleanout missing at base of main waste stack – east restroom bank",
                "page": 3,
            },
            {
                "severity": "medium",
                "description": "Water heater recirculation return unlabeled between sheets P5.1 and P5.2",
                "page": 5,
            },
            {
                "severity": "low",
                "description": "Trap primer coverage incomplete for floor drains in janitor closet",
                "page": 7,
            },
        ],
        "summary": (
            f"Analysis of {filename} identified {total_fixtures} fixtures across 6 types. "
            f"{flagged_count} issues flagged for engineer review. Estimated "
            f"{pipe_runs_estimated} pipe run segments and {estimated_labor_hrs} labor hours "
            "for installation."
        ),
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
    }


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)) -> Dict[str, Any]:
    filename = file.filename or "uploaded-file"
    file_bytes = await file.read()
    return smart_mock_analysis(filename, file_bytes)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
