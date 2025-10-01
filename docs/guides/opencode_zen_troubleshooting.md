# OpenCode Zen Integration & Troubleshooting

Observed symptom: API call returns an empty response and the adapter falls back to a placeholder event. Use this checklist to identify and fix common causes.

## ✅ Recent Bug Fix (2025-10-01)

**Major adapter bug eliminated**: The OpenCode Zen adapter was using a non-standard API structure that caused connection failures. This has been **fixed** in `src/core/opencode_zen_adapter.py` (lines 97-224).

**What was fixed**:
- ✅ Endpoint changed from `/extract` to `/chat/completions` (OpenAI-standard)
- ✅ Payload converted to OpenAI-compatible messages format
- ✅ Added `stream: false` flag
- ✅ Auth header retry logic (tries both Bearer and X-API-Key)
- ✅ Comprehensive error logging with HTTP status codes
- ✅ Debug mode toggle via `OPENCODEZEN_DEBUG` environment variable

**See full details**: `docs/reports/bug-elimination-opencode-zen-2025-10-01.md`

**Diagnostic tool**: Run `uv run python scripts/probe_opencode_zen.py` to test all endpoint/auth variants systematically.

## 1) Environment & Selection
- Ensure `EVENT_EXTRACTOR=opencode_zen` is set for the run.
- Verify credentials: `OPENCODEZEN_API_KEY` is non-empty in `.env`.
- Confirm endpoint and model:
  - `OPENCODEZEN_BASE_URL` (e.g., `https://api.opencode-zen.com/v1`).
  - `OPENCODEZEN_MODEL` matches an available model slug.
  - `OPENCODEZEN_TIMEOUT` set (e.g., `30`).

## 2) Authentication Header
Providers typically use one of these schemes:
- `Authorization: Bearer <OPENCODEZEN_API_KEY>`
- or `X-API-Key: <OPENCODEZEN_API_KEY>` (exact header name varies)

Action: Check provider docs and align the adapter accordingly. If empty JSON is returned, try switching header style and log the HTTP status and headers.

## 3) Endpoint & Payload Shape
- Endpoint path often follows OpenAI-style routes:
  - Chat: `POST {BASE_URL}/chat/completions`
  - Text: `POST {BASE_URL}/completions`
- Required JSON fields usually include:
  - `model`: string (e.g., `provider/model-name`)
  - `messages`: array for chat models
  - `temperature`, `max_tokens` (optional)
- Content-Type must be `application/json`.
- Streaming disabled: include `stream: false` if supported; some gateways stream by default.

## 4) Minimal Connectivity Probe (example)
This example mirrors a typical chat-completions request. Adjust the URL, header name, and payload fields to match the official docs.

```python
import os, json, requests
base = os.environ.get('OPENCODEZEN_BASE_URL', 'https://api.opencode-zen.com/v1')
key = os.environ['OPENCODEZEN_API_KEY']
model = os.environ['OPENCODEZEN_MODEL']
url = f"{base.rstrip('/')}/chat/completions"
headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
}
body = {
    "model": model,
    "messages": [
        {"role": "system", "content": "You extract legal events as structured JSON."},
        {"role": "user", "content": "Test connectivity only. Reply with: OK"}
    ],
    "temperature": 0.0,
    "stream": False
}
resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)
print(resp.status_code, resp.headers.get('x-request-id'))
print(resp.text[:500])  # Inspect raw text if JSON parse fails
```

If you get an empty body:
- Try `X-API-Key` header instead of `Authorization`.
- Switch endpoint path (`/completions` vs `/chat/completions`).
- Add `max_tokens` if the API requires it.
- Ensure the model slug is valid.

## 5) Adapter Hardening Tips
- Lazy-import HTTP client libs inside methods to avoid import-time failures.
- On non-2xx, log status, response text, and request id if available.
- If response parses but contains no choices, log a clear reason and return a fallback record with `attributes.fallback_reason`.
- Map common errors: `401/403` (auth), `404` (path/model), `429` (rate limit), `5xx` (provider outage).

## 6) Observability & Logs
- Add a debug toggle to print request metadata (masked) and the first 500 chars of the response.
- Capture connectivity attempts under `docs/reports/opencode_zen_connection.log` with timestamped results.

## 7) Common Root Causes
- Wrong header name (Bearer vs API-Key).
- Incorrect base URL or missing `/v1` prefix.
- Using `prompt` instead of `messages` for chat endpoints.
- Streaming default without handling chunks.
- Invalid or unavailable model slug.

## 8) Next Steps
Once corrected:
- Re-run the API connection test order (`docs/orders/api-connection-test.json`).
- If successful, update the work summary with the resolution details so future runs avoid the same pitfall.

