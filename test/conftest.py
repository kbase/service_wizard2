# conftest.py

import pytest
from dotenv import load_dotenv

@pytest.fixture(autouse=True)
def load_environment():
    load_dotenv()