import traceback
from typing import Union

from fastapi import APIRouter, Depends, Request, Query, HTTPException

from src.dependencies.middleware import is_authorized
from src.dependencies.start import start_deployment
from src.models.models import ServiceLogWebSocket

router = APIRouter(
    tags=["authenticated", "logs"],
    dependencies=[Depends(is_authorized)],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
        409: {"description": "AlreadyExistsError"},
    },
)


from src.models.models import DynamicServiceStatus



@router.get("/start/")
def start(request: Request, module_name: str = Query(...), version: str = Query(...)) -> DynamicServiceStatus:
    """
    :param request:  The request object used to start the service
    :param module_name: The name of the service module, case-insensitive
    :param version:      - specify the service version, which can be either:
                        (1) full git commit hash of the module version
                        (2) semantic version or semantic version specification
                            Note: semantic version lookup will only work for
                            released versions of the module.
                        (3) release tag, which is one of: dev | beta | release

    :return: DynamicServiceStatus
    """

    try:
        return start_deployment(request, module_name, version)
    except HTTPException as e:
        raise e
    except Exception as e:
        detail = traceback.format_exc()
        raise HTTPException(status_code=getattr(e, "status", 500), detail=detail) from e


@router.get("/get_service_log/{service}/{instance_id}")
def get_service_log(service: str, instance_id: Union[str | None] = None):
    """
    Get all service logs for all services, unless instance id is provided
    :param service: name of the service, e.g "condor-stats"
    :param instance_id: id of the specific service instance, e.g "1234"
    :return: a dictionary with a key "instance_id" and a key "logs" which is a list of logs
    """

    # TODO Call both and see what they look like
    return {"instance_id": instance_id, "logs": ["log1", "log2"]}


@router.get("/get_service_log/{instance_id}/{socket_url}")
def get_service_log_web_socket(instance_id, socket_url):
    """
    returns connection info for a websocket connection to get realtime service logs
    :param instance_id:
    :param socket_url:
    :return:
    """
    socket1 = ServiceLogWebSocket(instance_id=instance_id, socket_url=socket_url)
    socket2 = ServiceLogWebSocket(instance_id=instance_id, socket_url=socket_url)
    return [socket1, socket2]

    #
    # typedef structure{
    #     string instance_id;
    #     string socket_url;
    # } ServiceLogWebSocket;
    #
    # /* returns connection info for a websocket connection to get realtime service logs */
    # funcdef get_service_log_web_socket(GetServiceLogParams params) returns (list <ServiceLogWebSocket> sockets) authentication required;
