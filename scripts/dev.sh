#!/usr/bin/env bash
# =============================================================================
# Tuki — Local Dev Runner
# Starts the FastAPI backend and Flutter app in parallel.
# Usage: ./scripts/dev.sh [options]
#
# Options:
#   --backend-only   Start only the FastAPI backend
#   --mobile-only    Start only the Flutter mobile app
#   --device <id>    Flutter device/emulator ID (default: auto-detect)
#   --port <port>    Backend port (default: 8000)
#   -h, --help       Show this help message
# =============================================================================

set -euo pipefail

# ── Resolve project root (script can be called from anywhere) ─────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKEND_DIR="$ROOT_DIR/apps/backend"
MOBILE_DIR="$ROOT_DIR/apps/mobile"

# ── Defaults ──────────────────────────────────────────────────────────────────
RUN_BACKEND=true
RUN_MOBILE=true
FLUTTER_DEVICE=""
BACKEND_PORT=8000

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

log_info()    { echo -e "${CYAN}[tuki]${RESET} $*"; }
log_success() { echo -e "${GREEN}[tuki]${RESET} $*"; }
log_warn()    { echo -e "${YELLOW}[tuki]${RESET} $*"; }
log_error()   { echo -e "${RED}[tuki]${RESET} $*" >&2; }
log_section() { echo -e "\n${BOLD}${CYAN}══ $* ══${RESET}\n"; }

# ── Help ──────────────────────────────────────────────────────────────────────
usage() {
  cat <<EOF
${BOLD}Usage:${RESET} ./scripts/dev.sh [options]

${BOLD}Options:${RESET}
  --backend-only       Start only the FastAPI backend
  --mobile-only        Start only the Flutter mobile app
  --device <id>        Flutter target device/emulator ID
  --port <port>        Backend uvicorn port (default: 8000)
  -h, --help           Show this help

${BOLD}Examples:${RESET}
  ./scripts/dev.sh                    # Start everything
  ./scripts/dev.sh --backend-only     # Backend only
  ./scripts/dev.sh --device iPhone    # Run on a specific device
  ./scripts/dev.sh --port 9000        # Use a different backend port
EOF
  exit 0
}

# ── Arg parsing ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend-only) RUN_MOBILE=false; shift ;;
    --mobile-only)  RUN_BACKEND=false; shift ;;
    --device)       FLUTTER_DEVICE="$2"; shift 2 ;;
    --port)         BACKEND_PORT="$2"; shift 2 ;;
    -h|--help)      usage ;;
    *) log_error "Unknown option: $1"; usage ;;
  esac
done

# ── Dependency checks ─────────────────────────────────────────────────────────
check_command() {
  if ! command -v "$1" &>/dev/null; then
    log_error "'$1' is not installed or not in PATH."
    exit 1
  fi
}

log_section "Tuki Local Dev"

if $RUN_BACKEND; then
  check_command python3
  check_command uvicorn || true  # will be invoked via venv
fi
if $RUN_MOBILE; then
  check_command flutter
fi

# ── Track PIDs so we can clean up on exit ────────────────────────────────────
PIDS=()

cleanup() {
  echo ""
  log_warn "Shutting down all services..."
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  log_success "All services stopped. Goodbye! 👋"
}
trap cleanup EXIT INT TERM

# ── Backend ───────────────────────────────────────────────────────────────────
start_backend() {
  log_section "Starting FastAPI Backend"

  local venv_python="$BACKEND_DIR/.venv/bin/python"
  local venv_uvicorn="$BACKEND_DIR/.venv/bin/uvicorn"

  # Create venv if it doesn't exist
  if [[ ! -f "$venv_python" ]]; then
    log_info "Virtual environment not found. Creating one..."
    python3 -m venv "$BACKEND_DIR/.venv"
    log_success "Virtual environment created."
  fi

  # Install dependencies if needed
  if [[ ! -f "$BACKEND_DIR/.venv/lib/python"*"/site-packages/fastapi/__init__.py" ]] 2>/dev/null; then
    log_info "Installing backend dependencies (this may take a minute)..."
    "$venv_python" -m pip install --quiet -e "$BACKEND_DIR/.[dev]"
    log_success "Dependencies installed."
  fi

  log_info "Backend starting on http://localhost:${BACKEND_PORT}"
  log_info "API docs: http://localhost:${BACKEND_PORT}/docs"

  (
    cd "$BACKEND_DIR"
    "$venv_uvicorn" app.main:app \
      --host 0.0.0.0 \
      --port "$BACKEND_PORT" \
      --reload \
      --reload-dir app \
      --log-level info \
      2>&1 | sed "s/^/${CYAN}[backend]${RESET} /"
  ) &
  PIDS+=($!)
  log_success "Backend process started (PID: ${PIDS[-1]})"
}

# ── Mobile ────────────────────────────────────────────────────────────────────
start_mobile() {
  log_section "Starting Flutter Mobile App"

  # Install flutter packages if needed
  if [[ ! -d "$MOBILE_DIR/.dart_tool" ]]; then
    log_info "Running 'flutter pub get'..."
    (cd "$MOBILE_DIR" && flutter pub get --suppress-analytics)
    log_success "Flutter packages ready."
  fi

  # Build the flutter run command
  local flutter_cmd="flutter run --suppress-analytics"
  if [[ -n "$FLUTTER_DEVICE" ]]; then
    flutter_cmd+=" -d $FLUTTER_DEVICE"
    log_info "Targeting device: $FLUTTER_DEVICE"
  else
    log_info "No device specified — Flutter will auto-detect."
    log_info "Tip: Use --device <id> to pick a specific target."
  fi

  log_info "Launching Flutter app..."

  (
    cd "$MOBILE_DIR"
    # Give backend a moment to start if running together
    if $RUN_BACKEND; then sleep 3; fi
    $flutter_cmd 2>&1 | sed "s/^/${GREEN}[mobile]${RESET} /"
  ) &
  PIDS+=($!)
  log_success "Mobile process started (PID: ${PIDS[-1]})"
}

# ── Main ──────────────────────────────────────────────────────────────────────
echo -e "${BOLD}"
cat <<'BANNER'
  ████████╗██╗   ██╗██╗  ██╗██╗
  ╚══██╔══╝██║   ██║██║ ██╔╝██║
     ██║   ██║   ██║█████╔╝ ██║
     ██║   ██║   ██║██╔═██╗ ██║
     ██║   ╚██████╔╝██║  ██╗██║
     ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝
BANNER
echo -e "${RESET}"
log_info "Root: $ROOT_DIR"
log_info "Backend port: $BACKEND_PORT"

$RUN_BACKEND && start_backend
$RUN_MOBILE  && start_mobile

# ── Keep alive ────────────────────────────────────────────────────────────────
if [[ ${#PIDS[@]} -gt 0 ]]; then
  log_success "All services running. Press Ctrl+C to stop."
  # Wait for any child process to exit
  wait -n "${PIDS[@]}" 2>/dev/null || true
  log_warn "A service exited. Stopping all remaining services..."
fi
