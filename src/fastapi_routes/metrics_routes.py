import os

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from prometheus_client import generate_latest

router = APIRouter(tags=["metrics"])

security = HTTPBasic()


@router.get("/metrics", response_class=PlainTextResponse)
def get_metrics(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != os.environ["METRICS_USERNAME"] or credentials.password != os.environ["METRICS_PASSWORD"]:
        return PlainTextResponse("Unauthorized", status_code=401)
    return generate_latest()
