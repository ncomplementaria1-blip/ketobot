def test_home(client):
    c, _ = client
    resp = c.get("/")
    assert resp.status_code == 200
    assert b"activo" in resp.data


def test_verify_webhook_ok(client):
    c, _ = client
    resp = c.get(
        "/webhook",
        query_string={
            "hub.mode": "subscribe",
            "hub.verify_token": "test-verify",
            "hub.challenge": "12345",
        },
    )
    assert resp.status_code == 200
    assert resp.data == b"12345"


def test_verify_webhook_rejects_bad_token(client):
    c, _ = client
    resp = c.get(
        "/webhook",
        query_string={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong",
            "hub.challenge": "12345",
        },
    )
    assert resp.status_code == 403


def test_webhook_processes_text_message_and_persists(client):
    c, main = client

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "56911112222",
                                    "type": "text",
                                    "text": {"body": "hola, cuánto vale?"},
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
    assert resp.get_json() == {"status": "ok"}

    # Anthropic was called with system as a list including cache_control
    main.client.messages.create.assert_called_once()
    kwargs = main.client.messages.create.call_args.kwargs
    assert isinstance(kwargs["system"], list)
    assert kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert kwargs["messages"][-1] == {"role": "user", "content": "hola, cuánto vale?"}

    # WhatsApp send was called with the mocked response text
    main.send_whatsapp_message.assert_called_once_with(
        "56911112222", "respuesta de prueba"
    )

    # Both messages persisted
    import db
    convo = db.get_conversation("56911112222")
    assert len(convo) == 2
    assert convo[0] == {"role": "user", "content": "hola, cuánto vale?"}
    assert convo[1] == {"role": "assistant", "content": "respuesta de prueba"}


def test_webhook_ignores_non_text(client):
    c, main = client
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {"from": "56911112222", "type": "image"}
                            ]
                        }
                    }
                ]
            }
        ]
    }
    resp = c.post("/webhook", json=payload)
    assert resp.status_code == 200
    main.client.messages.create.assert_not_called()


def test_webhook_handles_status_event(client):
    c, main = client
    # Meta sends status updates without "messages" key
    payload = {"entry": [{"changes": [{"value": {"statuses": [{"id": "x"}]}}]}]}
    resp = c.post("/webhook", json=payload)
    assert resp.status_code == 200
    main.client.messages.create.assert_not_called()
