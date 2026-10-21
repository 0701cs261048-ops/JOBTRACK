# JobTrack

Full-stack job application tracker. Python (standard library only), SQLite, vanilla JS.

## Run
    python3 server.py        # then open http://localhost:8000
Optional env vars: PORT, DB_PATH.

## Features
- Register/login, PBKDF2-hashed passwords with per-user salt, expiring session tokens
- REST API: /api/register, /login, /logout, /me, /apps (CRUD), /stats
- SQLite with foreign keys, indexes, parameterized queries; every query is scoped to the logged-in user
- Kanban board with drag-and-drop (optimistic update, rolls back on error), search, status filter
- Dashboard: pipeline counts, "heard back" rate, applications over the last 7 days

## Known limits
No rate limiting, no HTTPS (put it behind a reverse proxy), no tests suite, plain HTTP server meant for demos/small use.
