import os
import pytest
from unittest.mock import AsyncMock, MagicMock

# Set dummy env vars before any app modules are imported
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    client.table = MagicMock(return_value=client)
    client.select = MagicMock(return_value=client)
    client.insert = MagicMock(return_value=client)
    client.eq = MagicMock(return_value=client)
    client.order = MagicMock(return_value=client)
    client.limit = MagicMock(return_value=client)
    client.execute = AsyncMock(return_value=MagicMock(data=[]))
    return client


@pytest.fixture
def mock_anthropic(mocker):
    return mocker.patch("anthropic.AsyncAnthropic")


@pytest.fixture
def mock_openai(mocker):
    return mocker.patch("openai.AsyncOpenAI")
