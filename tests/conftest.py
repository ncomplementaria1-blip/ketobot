import os
import sys
import tempfile
from unittest.mock import MagicMock

import pytest

# Make project root importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Point the DB at a temporary file for each test."""
    path = str(tmp_path / "test.db")
    monkeypatch.setenv("SQLITE_PATH", path)
    # Reload db module so DB_PATH picks up the env var.
    import importlib
    import db as db_module
    importlib.reload(db_module)
    db_module.init_db()
    return path


@pytest.fixture
def client(db_path, monkeypatch):
    """Flask test client with Anthropic + WhatsApp calls mocked."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("VERIFY_TOKEN", "test-verify")

    import importlib
    import main
    importlib.reload(main)

    fake_response = MagicMock()
    fake_response.content = [MagicMock(text="respuesta de prueba")]
    main.client.messages.create = MagicMock(return_value=fake_response)
    main.send_whatsapp_message = MagicMock(return_value={"status": "sent"})

    main.app.config["TESTING"] = True
    with main.app.test_client() as c:
        yield c, main
