# RelationshipOS Release Checklist

This checklist is the minimum gate before publishing a new build or demo branch.

## Required Verification

- Run the full unit/integration suite: `uv run pytest --tb=short -q`
- Run linting: `uv run ruff check .`
- Run router holdout evaluation: `uv run python router_v2/training/router_eval.py --data router_v2/training/holdout_zh.jsonl`
- Confirm router model dependencies are installed and the model loads without production fallback.
- Confirm `.env` or deployment config sets `RELATIONSHIP_OS_API_KEY`.
- Confirm admin-only routes use `RELATIONSHIP_OS_ADMIN_API_KEY`.
- Confirm production `RELATIONSHIP_OS_TRUSTED_HOSTS` is explicit and not `*`.
- Confirm WebSocket origins are restricted with `RELATIONSHIP_OS_WEBSOCKET_ALLOWED_ORIGINS`.
- Confirm request guards are configured: `RELATIONSHIP_OS_MAX_REQUEST_BYTES`, `RELATIONSHIP_OS_MAX_JSON_DEPTH`, `RELATIONSHIP_OS_RATE_LIMIT_REQUESTS`, and `RELATIONSHIP_OS_RATE_LIMIT_WINDOW_SECONDS`.

## Security Smoke Tests

- Unauthenticated session, stream, user memory, and runtime trace reads return `401` when `RELATIONSHIP_OS_API_KEY` is configured.
- Cross-user session, runtime trace, user profile, and WebSocket subscriptions return `403` or a forbidden WebSocket error.
- Stream append, projector rebuild, proactive dispatch, and global archive/followup reads require admin access.
- Oversized JSON bodies return `413`.
- Deeply nested JSON metadata returns `413`.
- Write bursts above the configured fixed-window rate limit return `429`.

## Data And Projection Checks

- `GET /sessions?offset=0&limit=20` returns `total`, `offset`, `limit`, and a bounded `sessions` array.
- Session listing does not depend on global `EventStore.read_all`.
- Projection snapshots are persisted in internal snapshot streams and restored after service restart.
- Projection snapshot streams are hidden from public `list_stream_ids` and rebuild targets.
- Runtime projection before and after snapshot restore produces the same state.

## Operational Notes

- The built-in rate limiter is per process. Multi-instance production deployments still need gateway or shared-store rate limiting.
- Projection snapshots are persisted as internal event streams. They are durable with the selected EventStore backend, but not yet compacted.
- WebSocket connection caps are per process. Multi-instance deployments should enforce global caps at the gateway layer.
- Router benchmark numbers in public docs must include evaluation date, model, judge type, and holdout file.

## Rollback

- Keep the previous container image or deployment artifact available before rollout.
- Keep the previous router model artifact available before retraining promotion.
- If snapshot restore behaves unexpectedly, disable snapshot consumption by rebuilding from full event streams and inspect internal `__projection_snapshot__:*` streams offline.
- If rate limiting blocks legitimate traffic, lower blast radius by setting `RELATIONSHIP_OS_RATE_LIMIT_REQUESTS=0` while gateway limits remain active.
