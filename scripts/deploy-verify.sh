#!/usr/bin/env bash
#
# Deployment Verification Script for Web3search
#
# Validates that both frontend (Cloudflare Pages) and backend (Render Workers) are properly deployed and accessible.
#
# Usage:
#   ./scripts/deploy-verify.sh
#   DEPLOY_FRONTEND_URL=https://staging.web3search.pages.dev ./scripts/deploy-verify.sh
#
# Environment Variables:
#   DEPLOY_FRONTEND_URL       Frontend URL to verify (default: https://web3search.pages.dev)
#   DEPLOY_BACKEND_HEALTH_URL Backend health endpoint (default: https://web3search-api.onrender.com/api/v1/health)
#   DEPLOY_VERIFY_TIMEOUT     HTTP request timeout in seconds (default: 15)
#

set -euo pipefail
IFS=$'\n\t'

# ============================================================================
# Prerequisites Check
# ============================================================================

check_prerequisites() {
  local missing=()

  command -v openssl >/dev/null 2>&1 || missing+=("openssl")
  command -v curl >/dev/null 2>&1 || missing+=("curl")
  command -v dig >/dev/null 2>&1 || missing+=("dig")
  command -v python3 >/dev/null 2>&1 || missing+=("python3")

  if [ ${#missing[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing required dependencies: ${missing[*]}${RESET}"
    echo "Please install these tools and try again."
    exit 1
  fi
}

# ============================================================================
# Configuration
# ============================================================================

GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
CYAN="\033[1;36m"
RESET="\033[0m"

DEFAULT_FRONTEND_URL="https://web3search.pages.dev"
DEFAULT_BACKEND_HEALTH_URL="https://web3search-api.onrender.com/api/v1/health"
DEFAULT_TIMEOUT="${DEPLOY_VERIFY_TIMEOUT:-15}"

FRONTEND_URL="${DEPLOY_FRONTEND_URL:-$DEFAULT_FRONTEND_URL}"
BACKEND_HEALTH_URL="${DEPLOY_BACKEND_HEALTH_URL:-$DEFAULT_BACKEND_HEALTH_URL}"

FAILURES=0

# ============================================================================
# Logging Functions
# ============================================================================

log() {
  echo -e "${CYAN}👉 $*${RESET}"
}

warn() {
  echo -e "${YELLOW}⚠️  $*${RESET}"
}

error() {
  echo -e "${RED}❌ $*${RESET}"
}

success() {
  echo -e "${GREEN}✅ $*${RESET}"
}

# ============================================================================
# URL Parsing Helpers
# ============================================================================

parse_host_port() {
  local url=$1
  python3 - <<'PY' "$url"
import sys
from urllib.parse import urlparse
input_url = sys.argv[1]
parsed = urlparse(input_url)
host = parsed.hostname or ''
port = parsed.port or (443 if parsed.scheme == 'https' else 80)
print(host)
print(port)
PY
}

get_host_port() {
  local url=$1
  local host port
  read -r host port < <(parse_host_port "$url")
  echo "$host:$port"
}

# ============================================================================
# Health Check Functions
# ============================================================================

check_ssl_certificate() {
  local label=$1
  local host=$2
  local port=$3

  log "Checking SSL certificate for ${label} (${host}:${port})"

  local cert_info
  if ! cert_info=$(openssl s_client -connect "${host}:${port}" -servername "${host}" </dev/null 2>/dev/null | openssl x509 -noout -dates 2>/dev/null); then
    error "${label}: Unable to retrieve TLS certificate."
    return 1
  fi

  local not_after
  not_after=$(printf '%s\n' "$cert_info" | awk -F= '/notAfter/{print $2}')
  if [ -z "$not_after" ]; then
    error "${label}: Failed to parse certificate expiration date."
    return 1
  fi

  local expiry_ts
  expiry_ts=$(python3 - <<PY "$not_after"
from datetime import datetime
import sys
date_str = sys.argv[1]
dt = datetime.strptime(date_str.strip(), "%b %d %H:%M:%S %Y %Z")
print(int(dt.timestamp()))
PY
  )

  local now_ts
  now_ts=$(date +%s)

  if [ "$expiry_ts" -le "$now_ts" ]; then
    error "${label}: TLS certificate expired on ${not_after}."
    return 1
  fi

  local remaining_days=$(( (expiry_ts - now_ts) / 86400 ))
  success "${label}: TLS certificate valid for ${remaining_days} days (expires ${not_after})."
  return 0
}

check_dns() {
  local label=$1
  local host=$2

  log "Resolving DNS for ${label} (${host})"

  local ips
  if ! ips=$(dig +short "$host" 2>/dev/null); then
    error "${label}: DNS lookup failed."
    return 1
  fi

  if [ -z "$ips" ]; then
    error "${label}: No DNS records found."
    return 1
  fi

  success "${label}: Resolved to ${ips}."
  return 0
}

check_url_health() {
  local label=$1
  local url=$2

  log "Probing ${label}: ${url}"

  local http_code
  if ! http_code=$(curl -sSfL --max-time "$DEFAULT_TIMEOUT" -o /dev/null -w "%{http_code}" "$url" 2>&1); then
    error "${label}: HTTP request failed."
    return 1
  fi

  if [ "$http_code" -lt 200 ] || [ "$http_code" -ge 400 ]; then
    error "${label}: Unexpected status ${http_code}."
    return 1
  fi

  success "${label}: Responded with ${http_code}."
  return 0
}

# ============================================================================
# Orchestration
# ============================================================================

run_check() {
  "$@" || FAILURES=$((FAILURES + 1))
}

main() {
  check_prerequisites

  log "Starting deployment verification (timeout=${DEFAULT_TIMEOUT}s)."
  echo ""

  # Parse frontend URL
  local frontend_host_port
  frontend_host_port=$(get_host_port "$FRONTEND_URL")
  local frontend_host="${frontend_host_port%%:*}"
  local frontend_port="${frontend_host_port##*:}"

  # Parse backend URL
  local backend_host_port
  backend_host_port=$(get_host_port "$BACKEND_HEALTH_URL")
  local backend_host="${backend_host_port%%:*}"
  local backend_port="${backend_host_port##*:}"

  # Run all checks
  log "Frontend Checks:"
  run_check check_ssl_certificate "Frontend (SSL)" "$frontend_host" "$frontend_port"
  run_check check_dns "Frontend (DNS)" "$frontend_host"
  run_check check_url_health "Frontend (page load)" "$FRONTEND_URL"

  echo ""
  log "Backend Checks:"
  run_check check_ssl_certificate "Backend (SSL)" "$backend_host" "$backend_port"
  run_check check_dns "Backend (DNS)" "$backend_host"
  run_check check_url_health "Backend health" "$BACKEND_HEALTH_URL"

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  if [ "$FAILURES" -ne 0 ]; then
    error "Deployment verification failed ($FAILURES check(s) failed)."
    exit 1
  fi

  success "Deployment verification passed. 🎉"
  echo ""
}

main "$@"
