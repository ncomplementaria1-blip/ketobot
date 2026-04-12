import importlib


def test_save_and_retrieve(db_path):
    import db
    importlib.reload(db)
    db.init_db()

    db.save_message("user1", "user", "hola")
    db.save_message("user1", "assistant", "qué gusto")
    db.save_message("user2", "user", "otra conversación")

    convo = db.get_conversation("user1")
    assert convo == [
        {"role": "user", "content": "hola"},
        {"role": "assistant", "content": "qué gusto"},
    ]

    other = db.get_conversation("user2")
    assert len(other) == 1
    assert other[0]["content"] == "otra conversación"


def test_history_limit_returns_last_n_ordered(db_path):
    import db
    importlib.reload(db)
    db.init_db()

    for i in range(15):
        db.save_message("user1", "user", f"msg {i}")

    convo = db.get_conversation("user1", limit=10)
    assert len(convo) == 10
    # Oldest-first, should be msgs 5..14
    assert convo[0]["content"] == "msg 5"
    assert convo[-1]["content"] == "msg 14"


def test_empty_conversation(db_path):
    import db
    importlib.reload(db)
    db.init_db()

    assert db.get_conversation("nobody") == []
