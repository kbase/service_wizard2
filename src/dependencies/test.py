import requests

from configs.settings import get_settings
from dotenv import load_dotenv
load_dotenv()

auth_url = get_settings().auth_service_url
response = requests.post(url=auth_url, headers={"Authorization": "TDDI6VCCHJGDKWIEUETS2YOX26RGCR5Y"})

if response.status_code == 401:
    raise HTTPException(status_code=401, detail=f"Invalid auth token or token has expired.")
if response.status_code != 200:
    raise HTTPException(
        status_code=401,
        detail=f"Something is wrong auth service or url is not valid",
    )

response = requests.get(auth_url, headers={"Authorization": token})

