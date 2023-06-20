from typing import Union

from fastapi import APIRouter, Depends

from src.dependencies.deps import authenticated_user
from src.models.models import ServiceLogWebSocket

router = APIRouter(
    tags=["authenticated", "logs"],
    dependencies=[Depends(authenticated_user)],
    responses={404: {"description": "Not found"}},
)


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


# @router.get(
#     "/selections/{selection_id}",
#     # response_model=models.SelectionVerbose,
#     # summary="Get a selection",
#     # description="Get the status and contents of a selection."
# )
# def hello(
#         r: Request,
#         selection_id: str = "123",
#         verbose: bool = False,
# ):  # -> models.SelectionVerbose:
#     # return await processing_selections.get_selection(
#     #     app_state.get_app_state(r), selection_id, verbose=verbose
#     # )
#     return 123
