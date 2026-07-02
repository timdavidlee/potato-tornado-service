# potato-tornado-service

A Dockerised **Postgres + FastAPI** wrapper over the
[`potato-tornado`](https://github.com/timdavidlee/potato-tornado) synthetic teaching
collections. `docker compose up` seeds every collection into its own Postgres schema and serves
it over HTTP.

## Architecture

```
docker compose
├── db     postgres:16                     one database, one schema per collection
├── seed   potato-tornado seed <dsn>       one-shot: generate + load all collections, then exit
└── api    uvicorn (FastAPI)               reads Postgres, serves JSON on :8000
```

The library is a private dependency installed over SSH (pinned to the `postgres-seed` branch
until that PR lands — see `[tool.uv.sources]` in [`pyproject.toml`](pyproject.toml)).

## Run it

Requires Docker with BuildKit and a running `ssh-agent` holding your GitHub key (the build
fetches the private `potato-tornado` repo over SSH):

```bash
ssh-add -l >/dev/null || ssh-add          # ensure your key is loaded
docker compose build --ssh default
docker compose up                         # db → seed → api
```

Then:

```bash
curl localhost:8000/health
curl localhost:8000/collections                              # ["clinic","hotel","insurance",...]
curl localhost:8000/collections/hotel/tables                 # ["demand_forecast","properties",...]
curl 'localhost:8000/collections/hotel/tables/reservations?limit=5'
```

Interactive docs: <http://localhost:8000/docs>.

## Endpoints

| Method & path | Returns |
|---|---|
| `GET /health` | `{"status":"ok"}`, or `503` if Postgres is unreachable |
| `GET /collections` | the seeded schema names (one per collection) |
| `GET /collections/{schema}/tables` | table names in that collection |
| `GET /collections/{schema}/tables/{table}?limit=&offset=` | a page of rows as JSON records |

Schema and table path params are validated against the live catalog before use, so they can't be
used for SQL injection.

## Local development (without Docker)

```bash
uv sync --extra dev          # resolves potato-tornado over SSH
uv run pytest                # health tests (no DB needed)

# point at any Postgres and seed + serve by hand:
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/teaching
uv run potato-tornado seed "$DATABASE_URL" --scale 0.2
uv run uvicorn potato_tornado_service.main:app --reload
```

To develop against a local `potato-tornado` checkout instead of the git dependency, override the
source in `pyproject.toml`:

```toml
[tool.uv.sources]
potato-tornado = { path = "../potato-tornado", editable = true }
```

## Once the library releases

When the `potato-tornado` `seed` work merges to `main`, tag a release there and switch this repo's
dependency from the branch to that tag:

```toml
potato-tornado = { git = "ssh://git@github.com/timdavidlee/potato-tornado.git", tag = "v0.1.1" }
```
