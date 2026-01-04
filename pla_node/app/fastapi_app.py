"""
FastAPI-based PLA Node gateway.
- Validates incoming events against contracts/event.schema.json
- Optional API key guard via header X-API-Key
- Forwards events to Brain Receiver at 127.0.0.1:8788/event with X-Request-ID
- Spools failed forwards to pla_node/spool and retries in the background
- Exposes host introspection endpoints for operations
"""
from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import subprocess
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from json import JSONDecodeError
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import requests
from fastapi import BackgroundTasks, Depends, FastAPI, Header, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

APP_VERSION = "0.3.0"
BRAIN_RECEIVER_URL = os.getenv("BRAIN_RECEIVER_URL", "http://127.0.0.1:8788/event")
PORT = int(os.getenv("PLA_NODE_PORT", "8787"))
API_KEY = os.getenv("PLA_API_KEY")
EVENT_VERSION = os.getenv("PLA_EVENT_VERSION", "1.0")

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "contracts" / "event.schema.json"
if not SCHEMA_PATH.exists():
    raise RuntimeError(f"Event schema not found at {SCHEMA_PATH}")

with SCHEMA_PATH.open("r", encoding="utf-8") as schema_file:
    EVENT_SCHEMA: Dict[str, Any] = json.load(schema_file)

VALIDATOR = Draft202012Validator(EVENT_SCHEMA, format_checker=FormatChecker())

SPOOL_DIR = REPO_ROOT / "pla_node" / "spool"
SPOOL_DIR.mkdir(parents=True, exist_ok=True)

start_monotonic = time.monotonic()

metrics: Dict[str, Any] = {
    "last_ingest_ts": None,
    "last_forward_success_ts": None,
    "last_forward_failure_ts": None,
    "forward_success_count": 0,
    "forward_failure_count": 0,
}

spool_lock = threading.Lock()
metrics_lock = threading.Lock()
retry_thread: Optional[threading.Thread] = None

LOG_PATH = REPO_ROOT / "logs" / "events.ndjson"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("pla_node")
logger.setLevel(logging.INFO)
_file_handler = RotatingFileHandler(LOG_PATH, maxBytes=5_000_000, backupCount=5)
_file_handler.setFormatter(logging.Formatter("%(message)s"))
logger.handlers = [_file_handler]
logger.propagate = False

@asynccontextmanager
async def lifespan(_app: FastAPI):
    global retry_thread
    log_json("pla_node_start", version=APP_VERSION, port=PORT)
    if retry_thread is None or not retry_thread.is_alive():
        retry_thread = threading.Thread(target=_process_spool_loop, daemon=True)
        retry_thread.start()
    yield


app = FastAPI(title="PLA Node", version=APP_VERSION, docs_url=None, redoc_url=None, lifespan=lifespan)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _spool_queue_depth() -> int:
    return len(list(SPOOL_DIR.glob("*.ndjson")))


def _event_id(payload: Dict[str, Any]) -> str:
    device_id = payload.get("device_id", "unknown")
    seq = payload.get("seq")
    return f"{device_id}:{seq}" if seq is not None else str(device_id)


def _request_id(payload: Dict[str, Any], header_rid: Optional[str]) -> str:
    if header_rid:
        return header_rid
    return payload.get("request_id") or str(uuid4())


def log_json(message: str, **extra: Any) -> None:
    entry = {"ts": _now_iso(), "msg": message}
    entry.update(extra)
    logger.info(json.dumps(entry, separators=(",", ":")))


def _validate_event(payload: Dict[str, Any]) -> None:
    VALIDATOR.validate(payload)
    if payload.get("event_version") != EVENT_VERSION:
        raise ValidationError(f"event_version must be '{EVENT_VERSION}'")


def _write_spool(payload: Dict[str, Any]) -> None:
    filename = f"event-{int(time.time()*1000)}-{threading.get_ident()}.ndjson"
    path = SPOOL_DIR / filename
    with spool_lock:
        with path.open("w", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, separators=(",", ":")) + "\n")


def _forward_event(payload: Dict[str, Any], request_id: str, timeout: float = 3.0) -> None:
    resp = requests.post(
        BRAIN_RECEIVER_URL,
        json=payload,
        headers={"X-Request-ID": request_id},
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"forward failed status={resp.status_code}")


def _forward_or_spool(payload: Dict[str, Any], request_id: str) -> None:
    event_id = _event_id(payload)
    try:
        _forward_event(payload, request_id)
        with metrics_lock:
            metrics["forward_success_count"] += 1
            metrics["last_forward_success_ts"] = _now_iso()
        log_json("forward_success", event_id=event_id, event_type=payload.get("event_type"), request_id=request_id)
    except Exception as exc:  # noqa: BLE001
        with metrics_lock:
            metrics["forward_failure_count"] += 1
            metrics["last_forward_failure_ts"] = _now_iso()
        _write_spool(payload)
        log_json(
            "forward_failed_spooled",
            event_id=event_id,
            event_type=payload.get("event_type"),
            request_id=request_id,
            error=str(exc),
        )


def _process_spool_loop() -> None:
    while True:
        files = sorted(SPOOL_DIR.glob("*.ndjson"))
        if not files:
            time.sleep(3)
            continue
        for path in files:
            try:
                with path.open("r", encoding="utf-8") as fp:
                    line = fp.readline()
                    payload = json.loads(line)
                rid = _request_id(payload, None)
                _forward_event(payload, rid)
                with metrics_lock:
                    metrics["forward_success_count"] += 1
                    metrics["last_forward_success_ts"] = _now_iso()
                log_json(
                    "retry_forward_success",
                    event_id=_event_id(payload),
                    event_type=payload.get("event_type"),
                    request_id=rid,
                )
                path.unlink(missing_ok=True)
            except Exception as exc:  # noqa: BLE001
                with metrics_lock:
                    metrics["forward_failure_count"] += 1
                    metrics["last_forward_failure_ts"] = _now_iso()
                log_json("retry_forward_failed", error=str(exc))
                time.sleep(2)
                break


def _uptime_seconds() -> Optional[int]:
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as fp:
            return int(float(fp.read().split()[0]))
    except Exception:
        return None


def _run_command(cmd: List[str]) -> Dict[str, Any]:
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            return {"ok": False, "stderr": proc.stderr.strip(), "stdout": proc.stdout.strip()}
        return {"ok": True, "stdout": proc.stdout.strip()}
    except FileNotFoundError:
        return {"ok": False, "error": "command_not_found"}


def _usb_list() -> Dict[str, Any]:
    result = _run_command(["lsusb"])
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error") or result.get("stderr") or "lsusb_failed"}
    lines = [line.strip() for line in result.get("stdout", "").splitlines() if line.strip()]
    return {"ok": True, "devices": lines}


def _ip_addresses() -> Dict[str, Any]:
    result = _run_command(["ip", "-br", "addr", "show"])
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error") or result.get("stderr") or "ip_failed"}
    interfaces: List[Dict[str, str]] = []
    for line in result.get("stdout", "").splitlines():
        parts = line.split()
        if len(parts) >= 3:
            iface = parts[0]
            state = parts[1]
            addrs = [p for p in parts[2:] if "/" in p]
            interfaces.append({"interface": iface, "state": state, "addresses": addrs})
    return {"ok": True, "interfaces": interfaces}


def _docker_ps() -> Dict[str, Any]:
    cmd = ["docker", "ps", "--format", "{{json .}}"]
    result = _run_command(cmd)
    if not result.get("ok"):
        return {"ok": False, "error": result.get("error") or result.get("stderr") or "docker_ps_failed"}
    entries: List[Dict[str, Any]] = []
    for line in result.get("stdout", "").splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            entries.append({"raw": line})
    return {"ok": True, "containers": entries}


@app.middleware("http")
async def api_key_guard(request: Request, call_next):
    if request.url.path in {"/health", "/openapi.json"}:
        return await call_next(request)
    if API_KEY:
        provided = request.headers.get("X-API-Key")
        if provided != API_KEY:
            return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    return await call_next(request)

@app.post("/ingest")
async def ingest(
    request: Request,
    background_tasks: BackgroundTasks,
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    with metrics_lock:
        metrics["last_ingest_ts"] = _now_iso()
    try:
        payload = await request.json()
    except JSONDecodeError:
        log_json("ingest_invalid_json")
        return JSONResponse({"ok": False, "error": "invalid_json"}, status_code=400)

    try:
        _validate_event(payload)
    except ValidationError as err:
        path = "/".join([str(p) for p in err.path])
        detail = err.message if not path else f"{err.message} at {path}"
        log_json("ingest_schema_failed", details=detail)
        return JSONResponse({"ok": False, "error": "schema_validation_failed", "details": detail}, status_code=400)

    rid = _request_id(payload, x_request_id)
    log_json("ingest_accepted", event_id=_event_id(payload), event_type=payload.get("event_type"), request_id=rid)
    background_tasks.add_task(_forward_or_spool, payload, rid)
    return JSONResponse({"ok": True, "accepted": True, "request_id": rid}, status_code=202)


@app.get("/health")
async def health():
    return {"ok": True, "status": "ready"}


@app.get("/status")
async def status():
    uptime_seconds = int(time.monotonic() - start_monotonic)
    with metrics_lock:
        snapshot = metrics.copy()
    retry_alive = retry_thread.is_alive() if retry_thread else False
    snapshot.update(
        {
            "service": "pla_node",
            "version": APP_VERSION,
            "ok": True,
            "uptime_seconds": uptime_seconds,
            "spool_queue_depth": _spool_queue_depth(),
            "retry_active": retry_alive,
        }
    )
    return snapshot


@app.get("/metrics")
async def metrics_endpoint():
    uptime_seconds = int(time.monotonic() - start_monotonic)
    with metrics_lock:
        success = metrics["forward_success_count"]
        failure = metrics["forward_failure_count"]
    lines = [
        f"pla_node_uptime_seconds {uptime_seconds}",
        f"pla_node_forward_success_total {success}",
        f"pla_node_forward_failure_total {failure}",
        f"pla_node_spool_queue_depth {_spool_queue_depth()}",
    ]
    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


@app.get("/os-info")
async def os_info():
    uname = platform.uname()
    uptime = _uptime_seconds()
    return {
        "ok": True,
        "hostname": uname.node,
        "system": uname.system,
        "release": uname.release,
        "version": uname.version,
        "machine": uname.machine,
        "processor": uname.processor,
        "uptime_seconds": uptime,
    }


@app.get("/disk")
async def disk():
    usage = shutil.disk_usage("/")
    return {
        "ok": True,
        "filesystem": "/",
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
    }


@app.get("/usb-list")
async def usb_list():
    return _usb_list()


@app.get("/ip")
async def ip_info():
    return _ip_addresses()


@app.get("/docker/ps")
async def docker_ps():
    return _docker_ps()


# retry thread started in lifespan