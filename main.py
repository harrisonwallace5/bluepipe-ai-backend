import os
import random
from pathlib import Path
from typing import Any, Dict, List

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address


load_dotenv()

SERVICE_VERSION = "1.0.0"
DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://localhost:4173"]
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "tiff", "tif"}
UPLOAD_CHUNK_SIZE = 1024 * 1024


def get_env_list(name: str, default: List[str]) -> List[str]:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default

    values = [item.strip() for item in raw_value.split(",") if item.strip()]
    return values or default


def get_env_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        parsed_value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc

    if parsed_value <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return parsed_value


def get_env_bool(name: str, default: bool) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None or not raw_value.strip():
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def get_cors_origins() -> List[str]:
    origins = get_env_list("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    if "*" in origins:
        raise ValueError("CORS_ORIGINS must be an explicit comma-separated origin list.")
    return origins


CORS_ORIGINS = get_cors_origins()
MAX_UPLOAD_MB = get_env_int("MAX_UPLOAD_MB", 20)
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
DEFAULT_RATE_LIMIT = os.environ.get("DEFAULT_RATE_LIMIT", "100/hour")
ANALYZE_RATE_LIMIT = os.environ.get("ANALYZE_RATE_LIMIT", "10/minute")
APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")
APP_PORT = get_env_int("APP_PORT", 8000)
APP_RELOAD = get_env_bool("APP_RELOAD", False)

limiter = Limiter(key_func=get_remote_address, default_limits=[DEFAULT_RATE_LIMIT])

app = FastAPI(title="BluePipe AI Backend", version=SERVICE_VERSION)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


async def read_limited_upload(file: UploadFile) -> bytes:
    content = bytearray()

    while chunk := await file.read(UPLOAD_CHUNK_SIZE):
        content.extend(chunk)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum upload size is {MAX_UPLOAD_MB}MB.",
            )

    return bytes(content)


async def validate_and_read_upload(file: UploadFile) -> tuple[str, bytes]:
    filename = file.filename or "uploaded-file"
    extension = Path(filename).suffix.lower().lstrip(".")

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=(
                "Unsupported file type. Allowed extensions: "
                + ", ".join(sorted(ALLOWED_EXTENSIONS))
            ),
        )

    try:
        file_bytes = await read_limited_upload(file)
    finally:
        await file.close()

    return filename, file_bytes


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
            adjustment = adjustment_pool[
                (byte_signature + index + rng.randint(0, 2)) % len(adjustment_pool)
            ]
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
    return {"status": "ok", "version": SERVICE_VERSION}


@app.post("/api/analyze")
@app.post("/analyze")
@limiter.limit(ANALYZE_RATE_LIMIT)
async def analyze(request: Request, file: UploadFile = File(...)) -> Dict[str, Any]:
    filename, file_bytes = await validate_and_read_upload(file)
    return smart_mock_analysis(filename, file_bytes)


if __name__ == "__main__":
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=APP_RELOAD)
