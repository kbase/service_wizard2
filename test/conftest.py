import os
from glob import glob

import pytest
from dotenv import load_dotenv


def _as_module(fixture_path: str) -> str:
    return fixture_path.replace("/", ".").replace("\\", ".").replace(".py", "")


def pytest_collectreport(report):
    print("CONFTEST loading all fixtures")


@pytest.fixture(autouse=True)
def load_environment():
    # Set DOTENV_FILE_LOCATION to override the default .env file location
    load_dotenv(os.environ.get("DOTENV_FILE_LOCATION", ".env"))
    if os.environ.get("PYCHARM_HOSTED"):
        load_dotenv(os.environ.get("src/.env"))


pytest_plugins = [_as_module(fixture) for fixture in glob("src/fixtures/[!_]*.py") + glob("test/src/fixtures/[!_]*.py")]
