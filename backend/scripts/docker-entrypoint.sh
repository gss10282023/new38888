#!/usr/bin/env sh
set -eu

wait_for_tcp() {
  host="$1"
  port="$2"
  name="$3"
  max_attempts="${4:-60}"

  echo "[entrypoint] Waiting for ${name} (${host}:${port})..."
  i=1
  while [ "$i" -le "$max_attempts" ]; do
    if python - <<PY >/dev/null 2>&1
import socket
import sys

host = "${host}"
port = int("${port}")
s = socket.socket()
s.settimeout(1)
try:
    s.connect((host, port))
except OSError:
    sys.exit(1)
finally:
    try:
        s.close()
    except Exception:
        pass
sys.exit(0)
PY
    then
      echo "[entrypoint] ${name} is reachable."
      return 0
    fi
    i=$((i + 1))
    sleep 1
  done

  echo "[entrypoint] Timed out waiting for ${name} (${host}:${port})." >&2
  return 1
}

DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
REDIS_URL="${REDIS_URL:-redis://redis:6379/1}"

wait_for_tcp "${DB_HOST}" "${DB_PORT}" "Postgres"

REDIS_HOST="$(python - <<'PY'
import os
from urllib.parse import urlparse

url = os.environ.get("REDIS_URL", "")
parsed = urlparse(url)
print(parsed.hostname or "redis")
PY
)"
REDIS_PORT="$(python - <<'PY'
import os
from urllib.parse import urlparse

url = os.environ.get("REDIS_URL", "")
parsed = urlparse(url)
print(parsed.port or 6379)
PY
)"
wait_for_tcp "${REDIS_HOST}" "${REDIS_PORT}" "Redis"

echo "[entrypoint] Applying migrations..."
python manage.py migrate --noinput

if [[ "${SEED_DEMO_DATA:-false}" == "true" ]]; then
  echo "[entrypoint] Seeding demo data..."
  python scripts/seed_demo_data.py
fi

echo "[entrypoint] Starting ASGI server..."
exec daphne -b 0.0.0.0 -p 8000 btf_backend.asgi:application
