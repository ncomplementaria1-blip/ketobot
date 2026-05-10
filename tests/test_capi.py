"""Tests para CAPI Purchase event y endpoint admin."""
import importlib
from unittest.mock import MagicMock


def test_admin_sale_requires_token(client, monkeypatch):
    c, main = client
    monkeypatch.setenv("ADMIN_TOKEN", "secret-token")
    importlib.reload(main)
    monkeypatch.setattr(main, "ADMIN_TOKEN", "secret-token")

    resp = c.post("/admin/sale", json={"user_id": "56911112222", "value_clp": 30000})
    assert resp.status_code == 401


def test_admin_sale_fires_capi_and_dedupes(client, monkeypatch):
    c, main = client
    monkeypatch.setattr(main, "ADMIN_TOKEN", "secret-token")
    monkeypatch.setattr(main, "META_DATASET_ID", "999")
    monkeypatch.setattr(main, "META_CAPI_TOKEN", "EAA-test")

    fake_post = MagicMock()
    fake_post.return_value.json.return_value = {"events_received": 1}
    fake_post.return_value.status_code = 200
    fake_post.return_value.text = "ok"
    monkeypatch.setattr(main.requests, "post", fake_post)

    headers = {"Authorization": "Bearer secret-token"}
    body = {"user_id": "56911112222", "value_clp": 30000, "event_id": "abc-1"}

    resp1 = c.post("/admin/sale", json=body, headers=headers)
    assert resp1.status_code == 200
    assert resp1.get_json()["status"] == "ok"
    assert fake_post.call_count == 1

    sent_payload = fake_post.call_args.kwargs["json"]
    event = sent_payload["data"][0]
    assert event["event_name"] == "Purchase"
    assert event["action_source"] == "business_messaging"
    assert event["custom_data"] == {"currency": "CLP", "value": 30000}
    # Phone is sha256-hashed
    assert len(event["user_data"]["ph"][0]) == 64

    # Reposting same event_id deduplicates (no second CAPI call)
    resp2 = c.post("/admin/sale", json=body, headers=headers)
    assert resp2.status_code == 200
    assert resp2.get_json()["status"] == "duplicate"
    assert fake_post.call_count == 1


def test_webhook_captures_ctwa_clid(client):
    c, main = client
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "56933334444",
                                    "type": "text",
                                    "text": {"body": "hola"},
                                    "referral": {"ctwa_clid": "clid-xyz-123"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    resp = c.post("/webhook", json=payload)
    assert resp.status_code == 200

    import db
    assert db.get_user_referral("56933334444") == "clid-xyz-123"
