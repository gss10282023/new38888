#!/usr/bin/env bash
set -euo pipefail

# Root directories
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# Commands can be overridden via environment variables if needed.
BACKEND_CMD=${BACKEND_CMD:-"daphne -b 0.0.0.0 -p 8000 btf_backend.asgi:application"}
FRONTEND_CMD=${FRONTEND_CMD:-"npm run dev -- --host"}

# Basic command availability checks before spawning background processes.
if ! command -v daphne >/dev/null && [[ "$BACKEND_CMD" == daphne* ]]; then
  echo "Error: daphne not found. Install it with 'pip install daphne' or set BACKEND_CMD." >&2
  exit 1
fi
if ! command -v npm >/dev/null; then
  echo "Error: npm not found. Install Node.js before starting the frontend." >&2
  exit 1
fi

# Gracefully stop child processes on exit.
cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}
trap cleanup INT TERM EXIT

# Launch backend (ASGI) service.
(cd "$BACKEND_DIR" && eval "$BACKEND_CMD") &
BACKEND_PID=$!

# Launch frontend dev server.
(cd "$FRONTEND_DIR" && eval "$FRONTEND_CMD") &
FRONTEND_PID=$!

wait
