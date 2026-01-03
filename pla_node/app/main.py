"""
PLA Node: minimal authenticated tool-runner API for HexForge PLA.
- FastAPI server with API key auth via X-API-Key header.
- Read-only system introspection endpoints; no arbitrary shell execution.
- Structured logging without leaking secrets.
"""
from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Dict, List

import psutil
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

API_KEY = os.getenv("PLA_API_KEY")
if not API_KEY:
    raise RuntimeError("PLA_API_KEY must be set; refusing to start without auth")

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

app = FastAPI(title="HexForge PLA Node", version="0.1.0")


def log_event(request: Request, success: bool, status_code: int) -> None:
    client_ip = request.client.host if request.client else "unknown"
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "method": request.method,
        "client_ip": client_ip,
        "status": status_code,
        "success": success,
    }
    logging.info(entry)


async def verify_api_key(request: Request) -> None:
    provided = request.headers.get("X-API-Key")
    if not provided or provided != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        log_event(request, success=response.status_code < 400, status_code=response.status_code)
        return response
    except HTTPException as exc:
        log_event(request, success=False, status_code=exc.status_code)
        raise
    except Exception:
        log_event(request, success=False, status_code=500)
        raise


@app.get("/health")
async def health() -> Dict[str, bool | str]:
    return {"ok": True, "status": "ready"}


@app.get("/os-info")
async def os_info(_: None = Depends(verify_api_key)) -> Dict[str, str]:
    return {
        "hostname": platform.node(),
        "platform": platform.system(),
        "kernel": platform.release(),
        "arch": platform.machine(),
    }


@app.get("/disk")
async def disk(_: None = Depends(verify_api_key)) -> Dict[str, float | int]:
    usage = psutil.disk_usage("/")
    return {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "percent": usage.percent,
    }


def _run_command(args: List[str]) -> Dict[str, str]:
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        return {"output": result.stdout.strip()}
    except FileNotFoundError:
        return {"error": f"command not found: {args[0]}"}
    except subprocess.CalledProcessError as exc:
        return {"error": exc.stderr.strip() or exc.stdout.strip() or "command failed"}


@app.get("/usb-list")
async def usb_list(_: None = Depends(verify_api_key)) -> Dict[str, Dict[str, str]]:
    return {
        "lsusb": _run_command(["lsusb"]),
        "lsblk": _run_command(["lsblk", "-o", "NAME,MODEL,SERIAL,SIZE,TYPE,MOUNTPOINT"]),
    }


@app.get("/ip")
async def ip_info(_: None = Depends(verify_api_key)) -> Dict[str, List[Dict[str, str]]]:
    addrs = []
    for iface, iface_addrs in psutil.net_if_addrs().items():
        for addr in iface_addrs:
            if addr.family.name == "AF_INET":
                addrs.append({"interface": iface, "address": addr.address})
    return {"addresses": addrs}


@app.get("/docker/ps")
async def docker_ps(_: None = Depends(verify_api_key)) -> JSONResponse:
    if not shutil.which("docker"):
        return JSONResponse(status_code=501, content={"error": "docker not installed"})
    result = _run_command(["docker", "ps", "--format", "{{.ID}} {{.Image}} {{.Status}}"])
    status_code = 200 if "output" in result else 500
    return JSONResponse(status_code=status_code, content=result)


# Entrypoint helper for `uvicorn app.main:app`
__all__ = ["app"]
