#!/usr/bin/env bash
set -euo pipefail

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

PG_VERSION="${PG_VERSION_OVERRIDE:-$(ls /etc/postgresql | head -n 1)}"
PG_CLUSTER="main"
PG_PORT="$(pg_lsclusters 2>/dev/null | awk 'NR==2 {print $3}')"
PG_PORT="${PG_PORT:-5432}"

SUBSTITUTION_PORT="${SUBSTITUTION_PORT:-8000}"
STOCK_PREDICTION_PORT="${STOCK_PREDICTION_PORT:-8100}"
ORDER_SERVICE_PORT="${PORT}"

SHORTAGE_SERVICE_URL="${SHORTAGE_SERVICE_URL:-http://localhost:${ORDER_SERVICE_PORT}/api/orders/shortage/proactive-call}"
export SHORTAGE_SERVICE_URL

PROC_PIDS=()
PROC_NAMES=()

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM
  log "Shutting down services (exit code: ${exit_code})"

  for idx in "${!PROC_PIDS[@]}"; do
    local pid="${PROC_PIDS[$idx]}"
    local name="${PROC_NAMES[$idx]}"
    if kill -0 "$pid" 2>/dev/null; then
      log "Stopping ${name} (pid ${pid})"
      kill "$pid" 2>/dev/null || true
    fi
  done

  if pg_ctlcluster "${PG_VERSION}" "${PG_CLUSTER}" status >/dev/null 2>&1; then
    log "Stopping PostgreSQL ${PG_VERSION}/${PG_CLUSTER}"
    pg_ctlcluster "${PG_VERSION}" "${PG_CLUSTER}" stop
  fi

  exit "${exit_code}"
}

trap cleanup EXIT INT TERM

start_postgres() {
  if pg_ctlcluster "${PG_VERSION}" "${PG_CLUSTER}" status >/dev/null 2>&1; then
    log "PostgreSQL ${PG_VERSION}/${PG_CLUSTER} already running"
  else
    log "Starting PostgreSQL ${PG_VERSION}/${PG_CLUSTER}"
    pg_ctlcluster "${PG_VERSION}" "${PG_CLUSTER}" start
  fi

  log "Waiting for PostgreSQL to accept connections on port ${PG_PORT}"
  for attempt in $(seq 1 30); do
    if pg_isready -h localhost -p "${PG_PORT}" >/dev/null 2>&1; then
      log "PostgreSQL is ready"
      return 0
    fi
    sleep 1
  done

  log "PostgreSQL failed to start in time"
  exit 1
}

escape_sql() {
  echo "$1" | sed "s/'/''/g"
}

ensure_database() {
  local db_user="${WAREHOUSE_DB_USER:-warehouse_user}"
  local db_pass="${WAREHOUSE_DB_PASSWORD:-warehouse_pass}"
  local db_name="${WAREHOUSE_DB_NAME:-warehouse}"

  log "Ensuring role ${db_user} exists"
  if ! runuser -u postgres -- psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${db_user}'" | grep -q 1; then
    runuser -u postgres -- psql -c "CREATE ROLE ${db_user} WITH LOGIN PASSWORD '$(escape_sql "${db_pass}")';"
  fi

  log "Ensuring database ${db_name} exists"
  if ! runuser -u postgres -- psql -tc "SELECT 1 FROM pg_database WHERE datname='${db_name}'" | grep -q 1; then
    runuser -u postgres -- createdb -O "${db_user}" "${db_name}"
  fi

  log "Applying warehouse schema"
  runuser -u postgres -- psql -d "${db_name}" -f /app/warehouse-db/db/init.sql

  log "Granting privileges on public schema tables/sequences to ${db_user}"
  runuser -u postgres -- psql -d "${db_name}" <<SQL
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${db_user};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${db_user};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO ${db_user};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO ${db_user};
SQL
}

start_process() {
  local name="$1"
  shift
  log "Starting ${name}"
  "$@" &
  local pid=$!
  PROC_PIDS+=("${pid}")
  PROC_NAMES+=("${name}")
}

start_services() {
  start_process "Order Fulfilment API (:${ORDER_SERVICE_PORT})" \
    bash -c "cd /opt/order && java -jar order_fulfilment_service.jar --server.port=${ORDER_SERVICE_PORT}"

  start_process "Substitution API (:${SUBSTITUTION_PORT})" \
    uvicorn services.substitution_service.main:app --host 127.0.0.1 --port "${SUBSTITUTION_PORT}"

  start_process "Stock Prediction API (:${STOCK_PREDICTION_PORT})" \
    uvicorn stock_prediction.main:app --host 127.0.0.1 --port "${STOCK_PREDICTION_PORT}"

}

main() {
  start_postgres
  ensure_database
  log "Seeding warehouse data (qty=500)"
  python3 /app/analysis/seed_selected_products.py --qty 500 || {
    log "Seeding failed"
    exit 1
  }
  start_services

  set +e
  wait -n
  exit_code=$?
  set -e
  log "A service exited (code=${exit_code}), shutting down stack"
  exit "${exit_code}"
}

main "$@"

