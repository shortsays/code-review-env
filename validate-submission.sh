#!/usr/bin/env bash
set -uo pipefail
PING_URL="${1:-}"
REPO_DIR="${2:-.}"
[ -z "$PING_URL" ] && echo "Usage: $0 <hf_space_url> [repo_dir]" && exit 1
REPO_DIR="$(cd "$REPO_DIR" && pwd)"
PASS=0

log()  { printf "[%s] %s\n" "$(date -u +%H:%M:%S)" "$*"; }
pass() { log "PASSED -- $1"; PASS=$((PASS+1)); }
fail() { log "FAILED -- $1"; }

echo "==============================="
echo "  OpenEnv Submission Validator"
echo "==============================="

# Step 1
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" -d '{}' \
  "${PING_URL%/}/reset" --max-time 30 2>/dev/null || echo "000")
[ "$HTTP_CODE" = "200" ] && pass "HF Space live" || { fail "HF Space returned $HTTP_CODE"; exit 1; }

# Step 2
command -v docker &>/dev/null || { fail "docker not found"; exit 1; }
docker build "$REPO_DIR" 2>&1 && pass "Docker build" || { fail "Docker build failed"; exit 1; }

# Step 3
command -v openenv &>/dev/null || { fail "openenv not found — pip install openenv-core"; exit 1; }
(cd "$REPO_DIR" && openenv validate 2>&1) && pass "openenv validate" || { fail "openenv validate failed"; exit 1; }

echo "==============================="
echo "  All $PASS/3 checks passed!"
echo "  Ready to submit."
echo "==============================="