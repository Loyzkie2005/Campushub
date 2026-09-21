# CampusHub Chat Service

Standalone FastAPI chat API backed by async SQLAlchemy. PostgreSQL is used in
production; SQLite is supported for tests. Database tables are managed only by
Alembic and are prefixed with `chat_`.

## Windows PowerShell setup

Run these commands from `backend\chat_service`:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with the PostgreSQL async URL, a long random `CHAT_JWT_SECRET`, and
the comma-separated browser origins allowed to call the service. The secret,
issuer, and audience must match Django's chat token settings. Do not commit
`.env`.

Apply the schema and start FastAPI:

```powershell
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

For a physical phone, bind FastAPI and Django to all interfaces:

```powershell
# Terminal 1: backend\chat_service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Terminal 2: backend\core
python manage.py runserver 0.0.0.0:8000
```

Set `ApiConfig.hostIp` in
`campushub/lib/module_app/config/api_config.dart` to the PC's Wi-Fi IPv4
address. The phone and PC must be on the same network, and Windows Firewall must
allow inbound TCP ports 8000 and 8001.

Create a migration after changing the SQLAlchemy models:

```powershell
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Run tests (they set an isolated SQLite URL):

```powershell
pytest
```

## Authentication

HTTP endpoints require `Authorization: Bearer <jwt>`, except `GET /health`.
Tokens use HS256 and the same `CHAT_JWT_SECRET` as the trusted token issuer.
Required claims are:

```json
{"sub":"admin:3","name":"Administrator","role":"admin"}
```

`sub` is a namespaced actor key. Prefixes such as `admin:` and `mobile:` keep
IDs from separate identity stores from colliding. The service validates tokens;
the existing CampusHub backend should issue them after authenticating a user.

## REST API

- `GET /health`
- `GET /conversations`
- `POST /conversations` with
  `{"participant":{"actor_key":"mobile:24","display_name":"Student"}}`
- `GET /conversations/{id}/messages?before_id=100&limit=50`
- `POST /conversations/{id}/messages` with `{"body":"Hello"}`
- `POST /conversations/{id}/read` with `{"message_id":100}`; omit or set
  `message_id` to `null` to read through the latest message

Direct conversations are reused for the same unordered actor pair. All
conversation operations enforce participant membership. Message pages are
returned in chronological order; use `next_before_id` for the next older page.

## WebSocket protocol

Connect to `/ws`. If an `Origin` header is present, it must match
`ALLOWED_ORIGINS`. The server accepts the socket, then the first JSON event must
arrive within `WEBSOCKET_AUTH_TIMEOUT_SECONDS`:

```json
{"type":"auth","token":"<jwt>"}
```

Success returns `auth.ok`. Supported client commands are:

```json
{"type":"message.send","conversation_id":1,"body":"Hello"}
{"type":"typing.start","conversation_id":1}
{"type":"typing.stop","conversation_id":1}
{"type":"conversation.read","conversation_id":1,"message_id":15}
```

Membership is checked for every command. Connected participants receive
`message.created` and `conversation.updated`; typing events are ephemeral and
sent to other connected participants. An actor may have multiple simultaneous
sockets, so multiple browser tabs or devices all receive events. Invalid
post-authentication commands receive an `error` event.

## Configuration

- `DATABASE_URL`: `postgresql+asyncpg://...` in production or
  `sqlite+aiosqlite:///...` in tests
- `CHAT_JWT_SECRET`: shared HS256 signing secret
- `CHAT_JWT_ISSUER`: token issuer; defaults to `campushub-django`
- `CHAT_JWT_AUDIENCE`: token audience; defaults to `campushub-chat`
- `ALLOWED_ORIGINS`: comma-separated HTTP/WebSocket browser origins
- `WEBSOCKET_AUTH_TIMEOUT_SECONDS`: first-event authentication timeout

## End-to-end flow

1. Django authenticates an admin or mobile user and issues a short-lived chat
   JWT.
2. The web or Flutter client uses that JWT for FastAPI REST requests.
3. The client opens `/ws` and sends the JWT in the first `auth` event.
4. FastAPI stores chat data in the `chat_*` PostgreSQL tables and broadcasts
   real-time events to every connected participant.

Useful checks:

```powershell
# FastAPI health
Invoke-RestMethod http://127.0.0.1:8001/health

# Service tests
.\.venv\Scripts\python.exe -m pytest -q

# Django token bridge tests (from backend\core)
python manage.py test modules.messages

# Flutter static analysis (from campushub)
flutter analyze
```
