from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from prometheus_client import generate_latest

router = APIRouter(tags=["metrics"])

security = HTTPBasic()


@router.get("/metrics", response_class=PlainTextResponse)
def get_metrics(credentials: HTTPBasicCredentials = Depends(security)):
    return generate_latest()
