import os
from glob import glob

import pytest
from dotenv import load_dotenv


def _as_module(fixture_path: str) -> str:
    return fixture_path.replace("/", ".").replace("\\", ".").replace(".py", "")

def pytest_collectreport(report):
    print("CONFTEST loaded")

@pytest.fixture(autouse=True)
def load_environment():
    # Ensure that the environment variables are loaded before running the tests
    load_dotenv(os.environ.get("DOTENV_FILE_LOCATION", ".env"))



pytest_plugins = [_as_module(fixture) for fixture in glob("test/src/fixtures/[!_]*.py")]
