## MCP Telegram Server

Production-ready MCP-compliant HTTP/SSE server to manage Telegram channel posts via the Bot API.

### Features
- **MCP tools**: telegram.create_post, telegram.update_post, telegram.delete_post, telegram.get_post, telegram.list_posts
- **Persistence**: SQLite via SQLAlchemy 2.x
- **Transport**: HTTPS + SSE (works behind Cloudflare Tunnel)
- **Security**: API key auth, chat allowlist, basic rate limiting
- **Reliability**: Retries with backoff (tenacity), idempotency key for create
- **Observability**: JSON logs, request_id correlation
- **Tests**: Mocked Telegram API, SSE correlation, security

### Requirements
- Python 3.11+

### Setup
1. Copy `.env.example` to `.env` and fill values:
```bash
cp .env.example .env
```

2. Install and run:
```bash
make install
make run
```
Server at http://localhost:8000

Health check:
```bash
curl http://localhost:8000/healthz
```

### Cloudflare Tunnel
Expose locally over HTTPS preserving SSE:
```bash
cloudflared tunnel --url http://localhost:8000 --hostname YOUR_SUBDOMAIN.yourdomain.com
```

Test SSE:
```bash
curl -N -H "Accept: text/event-stream" -H "X-API-Key: $API_KEY" https://YOUR_SUBDOMAIN.yourdomain.com/mcp/sse
```

### JSON-RPC
- Endpoint: `POST /mcp/rpc` (async -> 202)
- Endpoint: `POST /mcp/rpc?sync=true` (sync -> 200)
- SSE: `GET /mcp/sse?client_id=<uuid>`; events `event: message`, `data: <JSON>`

Example tools/list (sync):
```bash
curl -s -X POST 'http://localhost:8000/mcp/rpc?sync=true' \
  -H 'Content-Type: application/json' -H "X-API-Key: $API_KEY" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}' | jq
```

Example create_post (sync):
```bash
curl -s -X POST 'http://localhost:8000/mcp/rpc?sync=true' \
  -H 'Content-Type: application/json' -H "X-API-Key: $API_KEY" \
  -d '{
    "jsonrpc":"2.0",
    "id":"c8b5a8f4-3c3f-4a78-8d1c-2f5a4f2c6d77",
    "method":"tools/call",
    "params":{
      "name":"telegram.create_post",
      "arguments":{ "chat_id":"@my_channel", "text":"Hello from MCP!", "parse_mode":"HTML", "disable_web_page_preview":true },
      "idempotency_key":"demo-001"
    }
  }'
```

### Docker
Build and run:
```bash
docker build -t mcp-telegram-server .
docker run --rm -p 8000:8000 --env-file .env mcp-telegram-server
```

Docker Compose:
```bash
docker-compose up --build
```

### Makefile
- **install**: install editable package
- **fmt**: ruff fix + black
- **lint**: ruff + black --check
- **test**: pytest
- **run**: uvicorn dev
- **run-docker**: build and run image

### Tool Schemas
The MCP `tools/list` returns JSON Schema for each tool as required.

### Notes
- For channels with `@username`, links are `https://t.me/<username>/<message_id>`; otherwise link may be null.
- Input validation enforces either `text` or `caption` present for create/update.
- Rate limit default `10/second` per API key and IP.
