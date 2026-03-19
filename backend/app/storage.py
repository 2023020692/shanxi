"""File-system based storage utilities (replaces database).

All persistent data is stored as JSON files on disk, organised by type:
  raw/          – uploaded TIF files + <id>_<filename>.meta.json sidecar files
  processed/    – COG-converted TIF files
  wells/        – wells.json  (GeoJSON FeatureCollection)
  jobs/         – <job_id>.json  (fusion / enrichment jobs)
  reports/      – <report_id>.meta.json  (report metadata) + <report_id>.pdf
  detections/   – <detection_id>.json  (SAM2 results)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


# ---------------------------------------------------------------------------
# Rasters
# ---------------------------------------------------------------------------

def _raster_meta_glob(raster_id: str):
    """Yield metadata paths whose stem starts with <raster_id>_."""
    raw_dir = Path(settings.raw_dir)
    if not raw_dir.exists():
        return
    yield from raw_dir.glob(f"{raster_id}_*.meta.json")


def save_raster_meta(data: Dict[str, Any]) -> None:
    raster_id = data["id"]
    filename = data["filename"]
    path = Path(settings.raw_dir) / f"{raster_id}_{filename}.meta.json"
    _write_json(path, data)


def load_raster_meta(raster_id: str) -> Optional[Dict[str, Any]]:
    for p in _raster_meta_glob(raster_id):
        return _read_json(p)
    return None


def list_rasters() -> List[Dict[str, Any]]:
    raw_dir = Path(settings.raw_dir)
    if not raw_dir.exists():
        return []
    items = []
    for p in sorted(raw_dir.glob("*.meta.json"), key=_mtime, reverse=True):
        data = _read_json(p)
        if data:
            items.append(data)
    return items


def update_raster_meta(raster_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for p in _raster_meta_glob(raster_id):
        data = _read_json(p)
        if data:
            data.update(updates)
            data["updated_at"] = _now_iso()
            _write_json(p, data)
            return data
    return None


# ---------------------------------------------------------------------------
# Wells
# ---------------------------------------------------------------------------

def _wells_file() -> Path:
    return Path(settings.wells_dir) / "wells.json"


def load_wells() -> Dict[str, Any]:
    path = _wells_file()
    if path.exists():
        data = _read_json(path)
        if data:
            return data
    return {"type": "FeatureCollection", "features": []}


def save_wells(geojson: Dict[str, Any]) -> None:
    _write_json(_wells_file(), geojson)


def append_wells(new_features: List[Dict[str, Any]]) -> int:
    current = load_wells()
    current["features"].extend(new_features)
    save_wells(current)
    return len(new_features)


# ---------------------------------------------------------------------------
# Jobs  (fusion / enrichment)
# ---------------------------------------------------------------------------

def _job_path(job_id: str) -> Path:
    return Path(settings.jobs_dir) / f"{job_id}.json"


def save_job(data: Dict[str, Any]) -> None:
    _write_json(_job_path(data["id"]), data)


def load_job(job_id: str) -> Optional[Dict[str, Any]]:
    return _read_json(_job_path(job_id))


def list_jobs(job_type: Optional[str] = None) -> List[Dict[str, Any]]:
    jobs_dir = Path(settings.jobs_dir)
    if not jobs_dir.exists():
        return []
    items = []
    for p in sorted(jobs_dir.glob("*.json"), key=_mtime, reverse=True):
        data = _read_json(p)
        if data and (job_type is None or data.get("type") == job_type):
            items.append(data)
    return items


def update_job(job_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    path = _job_path(job_id)
    data = _read_json(path)
    if data:
        data.update(updates)
        data["updated_at"] = _now_iso()
        _write_json(path, data)
        return data
    return None


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def _report_meta_path(report_id: str) -> Path:
    return Path(settings.reports_dir) / f"{report_id}.meta.json"


def save_report_meta(data: Dict[str, Any]) -> None:
    _write_json(_report_meta_path(data["id"]), data)


def load_report_meta(report_id: str) -> Optional[Dict[str, Any]]:
    return _read_json(_report_meta_path(report_id))


def list_reports() -> List[Dict[str, Any]]:
    reports_dir = Path(settings.reports_dir)
    if not reports_dir.exists():
        return []
    items = []
    for p in sorted(reports_dir.glob("*.meta.json"), key=_mtime, reverse=True):
        data = _read_json(p)
        if data:
            items.append(data)
    return items


def update_report_meta(report_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    path = _report_meta_path(report_id)
    data = _read_json(path)
    if data:
        data.update(updates)
        _write_json(path, data)
        return data
    return None


# ---------------------------------------------------------------------------
# SAM2 Detections
# ---------------------------------------------------------------------------

def _detection_path(detection_id: str) -> Path:
    return Path(settings.detections_dir) / f"{detection_id}.json"


def save_detection(data: Dict[str, Any]) -> None:
    _write_json(_detection_path(data["detection_id"]), data)


def load_detection(detection_id: str) -> Optional[Dict[str, Any]]:
    return _read_json(_detection_path(detection_id))


def list_detections() -> List[Dict[str, Any]]:
    det_dir = Path(settings.detections_dir)
    if not det_dir.exists():
        return []
    items = []
    for p in sorted(det_dir.glob("*.json"), key=_mtime, reverse=True):
        data = _read_json(p)
        if data:
            items.append(data)
    return items
