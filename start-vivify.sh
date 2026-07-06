#!/bin/bash
# Start Vivify API server (port 3334)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export VIVIFY_DB_PATH="${VIVIFY_DB_PATH:-$SCRIPT_DIR/vivify_backend.db}"
export AUDIT_CHAIN_DB="${AUDIT_CHAIN_DB:-$SCRIPT_DIR/../memory/audit_chain.db}"
export MATERIALVIEW_URL="${MATERIALVIEW_URL:-http://localhost:3001}"
export SOC_GATEWAY_URL="${SOC_GATEWAY_URL:-http://localhost:3333}"

cd "$SCRIPT_DIR/backend"

echo "=== Vivify API ==="
echo "  DB:          $VIVIFY_DB_PATH"
echo "  Audit chain: $AUDIT_CHAIN_DB"
echo "  Port:        3334"
echo ""

exec python3 -m uvicorn server:app --host 0.0.0.0 --port 3334 --reload
