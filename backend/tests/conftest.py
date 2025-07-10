"""
Pytest Configuration für Preisvergleich Split Backend Architecture
"""

import os
import sys
import pytest
import asyncio
from typing import Generator

# Add project paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'client-api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'admin-api'))

# Legacy app path support für veraltete Tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_database_url():
    """Provide a test database URL"""
    return "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"

@pytest.fixture
def test_environment():
    """Set up test environment variables"""
    os.environ["APP_ENV"] = "test"
    os.environ["DEBUG"] = "true"
    os.environ["DATABASE_ECHO"] = "false"
    yield
    # Cleanup
    for key in ["APP_ENV", "DEBUG", "DATABASE_ECHO"]:
        os.environ.pop(key, None)

# Custom markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "integration: Integration tests that require external services")
    config.addinivalue_line("markers", "crawler: Crawler-specific tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "database: Tests that require database connection") 