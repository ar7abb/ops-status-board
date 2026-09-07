# Local portfolio demonstration

This demonstration proves the operational behavior of Ops Status Board without
requiring live AWS resources or exposing secrets. Run it from a disposable
clone or copy, not from a production host.

## 1. Start and verify the stack

Copy `.env.example` to `.env`, replace every placeholder with local test values,
then run:

```bash
docker compose build
docker compose up -d --wait
docker compose ps
curl --fail http://127.0.0.1:8000/health/live
curl --fail http://127.0.0.1:8000/health/ready
curl --fail http://127.0.0.1:8000/version
```

Expected evidence is two healthy containers, two `{"status":"ok"}` health
responses, and an explicit application version. FastAPI is published only on
the host loopback interface; PostgreSQL remains private to the Compose network.

## 2. Create and read an incident

Use the protected API with the local test admin token:

```bash
curl --fail \
  --request POST \
  --header "Authorization: Bearer ${ADMIN_API_TOKEN}" \
  --header 'Content-Type: application/json' \
  --data '{"title":"Portfolio demo incident","summary":"Controlled local demonstration","severity":"medium","status":"investigating"}' \
  http://127.0.0.1:8000/api/incidents

curl --fail http://127.0.0.1:8000/api/incidents
```

Open `http://127.0.0.1:8000/`. The incident proves the local browser, API, and
database path works end to end. The separate VM/AWS deployment adds Nginx in
front of FastAPI.

## 3. Demonstrate dependency failure

```bash
docker compose stop db
curl --silent --output /dev/null --write-out '%{http_code}\n' \
  http://127.0.0.1:8000/health/live
curl --silent --output /dev/null --write-out '%{http_code}\n' \
  http://127.0.0.1:8000/health/ready
```

Expected result:

- liveness returns `200`: the application process is running;
- readiness returns `503`: the service should not receive traffic because its
  database dependency is unavailable.

## 4. Recover and prove persistence

```bash
docker compose up -d --wait db
curl --fail http://127.0.0.1:8000/health/ready
curl --fail http://127.0.0.1:8000/api/incidents
```

Readiness must recover to `200`, and the incident must still exist because the
named PostgreSQL volume survives a container stop and restart.

## 5. Clean up

```bash
docker compose down --volumes --remove-orphans
```

This final command deliberately deletes the disposable local database volume.
Use plain `docker compose down` when data should be retained.

## What this demonstration proves

- the documented local workflow is reproducible;
- health checks distinguish process health from dependency health;
- persistence survives container replacement while the named volume exists;
- failure and recovery can be demonstrated without a public server;
- cleanup is intentional and its data-loss boundary is understood.
