import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app, manager
from services.data_manager import DataManager

@pytest.fixture(scope="session")
def test_db_url():
    # Use a temporary sqlite for tests
    return "sqlite:///test_database.db"

@pytest.fixture(scope="session", autouse=True)
def setup_test_manager(test_db_url):
    # Overwrite the global manager in main with a test one
    import main
    test_manager = DataManager(db_url=test_db_url)
    main.manager = test_manager
    yield test_manager
    
    # Properly shutdown/dispose to release file lock on Windows
    test_manager.db.engine.dispose()
    
    # Cleanup
    if os.path.exists("test_database.db"):
        try:
            os.remove("test_database.db")
        except:
            pass

@pytest.fixture
def client():
    return TestClient(app)
