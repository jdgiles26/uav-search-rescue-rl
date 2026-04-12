"""Document ingestion: PDF/text parsing + AI-powered mission-parameter extraction.

When ANTHROPIC_API_KEY is set, uses Claude for intelligent extraction.
Otherwise falls back to regex heuristics.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional

from backend.config import ANTHROPIC_API_KEY, THEATERS

# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_from_file(path: str) -> str:
    """Return raw text from a PDF or plain-text file."""
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        return _extract_pdf(path)
    # Assume plain text / markdown / etc.
    return p.read_text(errors="replace")


def _extract_pdf(path: str) -> str:
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return "\n\n".join(pages)
    except ImportError:
        # Fallback to PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(path)
            return "\n\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        except ImportError:
            raise RuntimeError(
                "No PDF library available. Install pdfplumber or PyPDF2."
            )


# ---------------------------------------------------------------------------
# AI-powered extraction (Claude)
# ---------------------------------------------------------------------------

_EXTRACTION_PROMPT = """\
You are a search-and-rescue operations analyst. Extract structured mission
parameters from the following document text.  Return ONLY valid JSON with
these keys (use null for anything not found):

{
  "location_name": "string — closest named region or coordinates",
  "latitude": float or null,
  "longitude": float or null,
  "survivors_estimate": int or null,
  "urgency": "critical" | "high" | "medium" | "low" | null,
  "terrain": "string description" or null,
  "weather_conditions": "string" or null,
  "recommended_uavs": int or null,
  "search_area_km2": float or null,
  "notes": "any other relevant details"
}

Document text:
---
{text}
---
"""


def _extract_with_claude(raw_text: str) -> tuple[dict, float]:
    """Use Anthropic API to extract mission params. Returns (data, confidence)."""
    import anthropic

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": _EXTRACTION_PROMPT.format(text=raw_text[:8000])}
        ],
    )
    text = message.content[0].text.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    data = json.loads(text)
    # Rough confidence from how many fields were populated
    filled = sum(1 for v in data.values() if v is not None and v != "")
    confidence = round(filled / len(data), 2)
    return data, confidence


# ---------------------------------------------------------------------------
# Regex fallback extraction
# ---------------------------------------------------------------------------

_COORD_RE = re.compile(
    r"(-?\d{1,3}(?:\.\d+)?)\s*[°]?\s*([NS])?\s*,?\s*(-?\d{1,3}(?:\.\d+)?)\s*[°]?\s*([EW])?",
    re.IGNORECASE,
)
_SURVIVORS_RE = re.compile(
    r"(\d+)\s*(?:survivors?|persons?|people|victims?|stranded|missing)",
    re.IGNORECASE,
)
_URGENCY_RE = re.compile(
    r"\b(critical|urgent|high\s*priority|immediate|emergency)\b",
    re.IGNORECASE,
)
_UAVS_RE = re.compile(r"(\d+)\s*(?:UAVs?|drones?|aircraft)", re.IGNORECASE)


def _extract_with_regex(raw_text: str) -> tuple[dict, float]:
    data: dict = {
        "location_name": None,
        "latitude": None,
        "longitude": None,
        "survivors_estimate": None,
        "urgency": None,
        "terrain": None,
        "weather_conditions": None,
        "recommended_uavs": None,
        "search_area_km2": None,
        "notes": None,
    }
    confidence_hits = 0

    # Coordinates
    m = _COORD_RE.search(raw_text)
    if m:
        lat = float(m.group(1))
        if m.group(2) and m.group(2).upper() == "S":
            lat = -lat
        lon = float(m.group(3))
        if m.group(4) and m.group(4).upper() == "W":
            lon = -lon
        data["latitude"] = lat
        data["longitude"] = lon
        confidence_hits += 2

    # Location name — try to match a known theater
    lower = raw_text.lower()
    for theater_name in THEATERS:
        if any(tok in lower for tok in theater_name.lower().split(",")):
            data["location_name"] = theater_name
            if data["latitude"] is None:
                data["latitude"], data["longitude"] = THEATERS[theater_name]
            confidence_hits += 1
            break

    # Survivors
    m = _SURVIVORS_RE.search(raw_text)
    if m:
        data["survivors_estimate"] = int(m.group(1))
        confidence_hits += 1

    # Urgency
    m = _URGENCY_RE.search(raw_text)
    if m:
        data["urgency"] = "critical" if "critical" in m.group(0).lower() else "high"
        confidence_hits += 1

    # UAVs
    m = _UAVS_RE.search(raw_text)
    if m:
        data["recommended_uavs"] = int(m.group(1))
        confidence_hits += 1

    confidence = round(confidence_hits / 6, 2)  # 6 key fields
    return data, confidence


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_mission_params(raw_text: str) -> tuple[dict, float]:
    """
    Extract mission parameters from raw document text.

    Returns (extracted_dict, confidence_score).
    """
    if ANTHROPIC_API_KEY:
        try:
            return _extract_with_claude(raw_text)
        except Exception:
            pass  # fall through to regex
    return _extract_with_regex(raw_text)


def params_to_env_config(extracted: dict) -> dict:
    """
    Map extracted SAR parameters to UAVEnvironment configuration.
    """
    survivors = extracted.get("survivors_estimate") or 20
    n_service = max(10, min(survivors, 100))

    recommended_uavs = extracted.get("recommended_uavs") or max(1, n_service // 10)
    n_uavs = max(1, min(recommended_uavs, 5))

    area = extracted.get("search_area_km2")
    if area and area > 0:
        map_size = max(50, min(int(area ** 0.5 / KM_PER_UNIT), 200))
    else:
        map_size = 100

    urgency = (extracted.get("urgency") or "medium").lower()
    if urgency in ("critical", "high"):
        battery_limit = 100
        time_limit = 200
    else:
        battery_limit = 80
        time_limit = 150

    return {
        "n_service_nodes": n_service,
        "n_charging_stations": max(2, n_uavs),
        "map_size": map_size,
        "time_limit": time_limit,
        "battery_limit": battery_limit,
        "seed": 42,
        "n_uavs": n_uavs,
    }


KM_PER_UNIT = 0.1
