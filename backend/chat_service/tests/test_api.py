import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


def token(actor_key: str, name: str = "Test User", role: str = "user") -> str:
    return jwt.encode(
        {
            "sub": actor_key,
            "name": name,
            "role": role,
            "iss": "campushub-django",
            "aud": "campushub-chat",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        "test-only-secret-that-is-over-32-bytes",
        algorithm="HS256",
    )


def auth(actor_key: str, name: str = "Test User") -> dict[str, str]:
    return {"Authorization": f"Bearer {token(actor_key, name)}"}


def test_health_and_bearer_auth(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/conversations")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_presence_tracks_authenticated_websocket(client: TestClient) -> None:
    headers = auth("mobile:24", "Student")
    offline = client.get("/presence/admin:3", headers=headers)
    assert offline.status_code == 200
    assert offline.json() == {"actor_key": "admin:3", "online": False}

    with client.websocket_connect("/ws") as websocket:
        websocket.send_json(
            {"type": "auth", "token": token("admin:3", "Administrator")}
        )
        assert websocket.receive_json()["type"] == "auth.ok"

        online = client.get("/presence/admin:3", headers=headers)
        assert online.status_code == 200
        assert online.json() == {"actor_key": "admin:3", "online": True}

    offline_again = client.get("/presence/admin:3", headers=headers)
    assert offline_again.json()["online"] is False


def test_direct_conversation_is_reused(client: TestClient) -> None:
    created = client.post(
        "/conversations",
        headers=auth("admin:3", "Administrator"),
        json={
            "participant": {
                "actor_key": "mobile:24",
                "display_name": "Student",
            }
        },
    )
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    reused = client.post(
        "/conversations",
        headers=auth("mobile:24", "Student"),
        json={
            "participant": {
                "actor_key": "admin:3",
                "display_name": "Administrator",
            }
        },
    )
    assert reused.status_code == 200
    assert reused.json()["id"] == conversation_id

    visible = client.get("/conversations", headers=auth("mobile:24"))
    assert visible.status_code == 200
    assert [item["id"] for item in visible.json()] == [conversation_id]


def test_product_context_creates_separate_direct_conversations(
    client: TestClient,
) -> None:
    first = client.post(
        "/conversations",
        headers=auth("mobile:24", "Student"),
        json={
            "participant": {
                "actor_key": "admin:3",
                "display_name": "Administrator",
            },
            "context_key": "product:101",
        },
    )
    second = client.post(
        "/conversations",
        headers=auth("mobile:24", "Student"),
        json={
            "participant": {
                "actor_key": "admin:3",
                "display_name": "Administrator",
            },
            "context_key": "product:102",
        },
    )
    first_again = client.post(
        "/conversations",
        headers=auth("mobile:24", "Student"),
        json={
            "participant": {
                "actor_key": "admin:3",
                "display_name": "Administrator",
            },
            "context_key": "product:101",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert first_again.status_code == 200
    assert first_again.json()["id"] == first.json()["id"]


def test_conversation_membership_is_enforced(client: TestClient) -> None:
    conversation = client.post(
        "/conversations",
        headers=auth("admin:3", "Administrator"),
        json={
            "participant": {
                "actor_key": "mobile:24",
                "display_name": "Student",
            }
        },
    ).json()

    denied = client.get(
        f"/conversations/{conversation['id']}/messages",
        headers=auth("mobile:99", "Outsider"),
    )
    assert denied.status_code == 404

    sent = client.post(
        f"/conversations/{conversation['id']}/messages",
        headers=auth("admin:3", "Administrator"),
        json={"body": "Hello"},
    )
    assert sent.status_code == 201

    messages = client.get(
        f"/conversations/{conversation['id']}/messages",
        headers=auth("mobile:24", "Student"),
    )
    assert messages.status_code == 200
    assert [item["body"] for item in messages.json()["items"]] == ["Hello"]
    assert messages.json()["items"][0]["sender_actor_key"] == "admin:3"

    summaries = client.get("/conversations", headers=auth("mobile:24", "Student"))
    assert summaries.json()[0]["last_message"]["body"] == "Hello"
    assert summaries.json()[0]["unread_count"] == 1

    read = client.post(
        f"/conversations/{conversation['id']}/read",
        headers=auth("mobile:24", "Student"),
        json={"message_id": sent.json()["id"]},
    )
    assert read.status_code == 200
    assert read.json()["last_read_message_id"] == sent.json()["id"]
    summaries = client.get("/conversations", headers=auth("mobile:24", "Student"))
    assert summaries.json()[0]["unread_count"] == 0


def test_websocket_authentication_and_message_delivery(client: TestClient) -> None:
    conversation = client.post(
        "/conversations",
        headers=auth("admin:3", "Administrator"),
        json={
            "participant": {
                "actor_key": "mobile:24",
                "display_name": "Student",
            }
        },
    ).json()

    with client.websocket_connect("/ws", headers={"origin": "http://testserver"}) as ws:
        ws.send_json({"type": "auth", "token": token("mobile:24", "Student")})
        assert ws.receive_json()["type"] == "auth.ok"

        ws.send_json(
            {
                "type": "message.send",
                "conversation_id": conversation["id"],
                "body": "Sent over WebSocket",
            }
        )
        created = ws.receive_json()
        assert created["type"] == "message.created"
        assert created["message"]["sender_actor_key"] == "mobile:24"
        assert created["message"]["body"] == "Sent over WebSocket"
        assert ws.receive_json()["type"] == "conversation.updated"


def test_conversation_delete_requires_membership(client: TestClient) -> None:
    conversation = client.post(
        "/conversations",
        headers=auth("admin:3", "Administrator"),
        json={
            "participant": {
                "actor_key": "mobile:24",
                "display_name": "Student",
            }
        },
    ).json()

    denied = client.delete(
        f"/conversations/{conversation['id']}",
        headers=auth("mobile:99", "Outsider"),
    )
    assert denied.status_code == 404

    deleted = client.delete(
        f"/conversations/{conversation['id']}",
        headers=auth("admin:3", "Administrator"),
    )
    assert deleted.status_code == 204
    assert client.get("/conversations", headers=auth("admin:3")).json() == []
    visible_to_peer = client.get(
        "/conversations", headers=auth("mobile:24", "Student")
    ).json()
    assert [item["id"] for item in visible_to_peer] == [conversation["id"]]

    reply = client.post(
        f"/conversations/{conversation['id']}/messages",
        headers=auth("mobile:24", "Student"),
        json={"body": "This should restore the chat"},
    )
    assert reply.status_code == 201
    restored = client.get(
        "/conversations", headers=auth("admin:3", "Administrator")
    ).json()
    assert [item["id"] for item in restored] == [conversation["id"]]
    assert restored[0]["last_message"]["body"] == "This should restore the chat"


def test_conversation_list_refreshes_participant_name(client: TestClient) -> None:
    client.post(
        "/conversations",
        headers=auth("mobile:24", "Development Guest"),
        json={
            "participant": {
                "actor_key": "admin:3",
                "display_name": "Administrator",
            }
        },
    )

    conversations = client.get(
        "/conversations",
        headers=auth("mobile:24", "Lester Bulay"),
    ).json()
    own_participant = next(
        item
        for item in conversations[0]["participants"]
        if item["actor_key"] == "mobile:24"
    )
    assert own_participant["display_name"] == "Lester Bulay"


def test_clear_chat_keeps_conversation_and_removes_messages(
    client: TestClient,
) -> None:
    conversation = client.post(
        "/conversations",
        headers=auth("admin:3", "Administrator"),
        json={
            "participant": {
                "actor_key": "mobile:24",
                "display_name": "Student",
            }
        },
    ).json()
    client.post(
        f"/conversations/{conversation['id']}/messages",
        headers=auth("admin:3", "Administrator"),
        json={"body": "Remove me"},
    )

    cleared = client.delete(
        f"/conversations/{conversation['id']}/messages",
        headers=auth("mobile:24", "Student"),
    )
    assert cleared.status_code == 204
    messages = client.get(
        f"/conversations/{conversation['id']}/messages",
        headers=auth("admin:3", "Administrator"),
    ).json()
    assert messages["items"] == []
    conversations = client.get(
        "/conversations", headers=auth("admin:3", "Administrator")
    ).json()
    assert conversations[0]["id"] == conversation["id"]
    assert conversations[0]["last_message"] is None
