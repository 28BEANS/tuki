#!/usr/bin/env bash
# =============================================================================
# Tuki — Local Dev Runner
# Starts the FastAPI backend and Flutter app in parallel.
# Usage: ./scripts/dev.sh [options]
#
# Options:
#   --backend-only   Start only the FastAPI backend
#   --mobile-only    Start only the Flutter mobile app
#   --device <id>    Flutter device/emulator ID (default: chrome)
#   --port <port>    Backend port (default: 8000)
#   -h, --help       Show this help message
# =============================================================================

# ── Resolve project root (script can be called from anywhere) ─────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKEND_DIR="$ROOT_DIR/apps/backend"
MOBILE_DIR="$ROOT_DIR/apps/mobile"

VENV_DIR="$BACKEND_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
VENV_UVICORN="$VENV_DIR/bin/uvicorn"

# ── Defaults ──────────────────────────────────────────────────────────────────
RUN_BACKEND=true
RUN_MOBILE=true
FLUTTER_DEVICE="chrome"
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
  --device <id>        Flutter target device/emulator ID (default: chrome)
  --port <port>        Backend uvicorn port (default: 8000)
  -h, --help           Show this help

${BOLD}Examples:${RESET}
  ./scripts/dev.sh                    # Start everything (Flutter on Chrome)
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
  if ! command -v "$1" >/dev/null 2>&1; then
    log_error "'$1' is not installed or not in PATH."
    exit 1
  fi
}

if $RUN_BACKEND; then
  check_command python3
fi
if $RUN_MOBILE; then
  check_command flutter
fi

# ── Track PIDs so we can clean up on exit ────────────────────────────────────
BACKEND_PID=""
MOBILE_PID=""

cleanup() {
  echo ""
  log_warn "Shutting down all services..."
  for pid in $BACKEND_PID $MOBILE_PID; do
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  log_success "All services stopped. Goodbye! 👋"
}
trap cleanup EXIT INT TERM

# ── Backend ───────────────────────────────────────────────────────────────────
start_backend() {
  log_section "Starting FastAPI Backend"

  # 1. Create venv if missing
  if [ ! -f "$VENV_PYTHON" ]; then
    log_info "Virtual environment not found — creating one..."
    python3 -m venv "$VENV_DIR"
    log_success "Virtual environment created at $VENV_DIR"
  else
    log_info "Virtual environment found at $VENV_DIR"
  fi

  # 2. Install deps if fastapi is not present in the venv
  if ! "$VENV_PYTHON" -c "import fastapi" 2>/dev/null; then
    log_info "Installing backend dependencies into venv (this may take a minute)..."
    "$VENV_PIP" install --quiet -e "$BACKEND_DIR/.[dev]"
    log_success "Dependencies installed."
  else
    log_info "Backend dependencies already installed."
  fi

  # 3. Always ensure the local routing_engine package is installed (editable)
  #    This is a workspace-local package not available on PyPI.
  if ! "$VENV_PYTHON" -c "import routing_engine" 2>/dev/null; then
    log_info "Installing local routing_engine package..."
    "$VENV_PIP" install --quiet -e "$ROOT_DIR/packages/routing_engine/"
    log_success "routing_engine installed."
  fi

  log_info "Backend starting on http://localhost:${BACKEND_PORT}"
  log_info "API docs:     http://localhost:${BACKEND_PORT}/docs"

  # 3. Run uvicorn from within the venv — always uses the venv's Python
  (
    cd "$BACKEND_DIR"
    "$VENV_UVICORN" app.main:app \
      --host 0.0.0.0 \
      --port "$BACKEND_PORT" \
      --reload \
      --reload-dir app \
      --log-level info
  ) &
  BACKEND_PID=$!
  log_success "Backend running (PID: $BACKEND_PID)"
}

# ── Mobile ────────────────────────────────────────────────────────────────────
start_mobile() {
  log_section "Starting Flutter Mobile App"

  # Install flutter packages if needed
  if [ ! -d "$MOBILE_DIR/.dart_tool" ]; then
    log_info "Running 'flutter pub get'..."
    (cd "$MOBILE_DIR" && flutter pub get --suppress-analytics)
    log_success "Flutter packages ready."
  fi

  log_info "Targeting device: $FLUTTER_DEVICE"
  log_info "Launching Flutter app..."

  (
    cd "$MOBILE_DIR"
    # Give backend a moment to start if running together
    if $RUN_BACKEND; then sleep 3; fi
    flutter run --suppress-analytics -d "$FLUTTER_DEVICE"
  ) &
  MOBILE_PID=$!
  log_success "Mobile running (PID: $MOBILE_PID)"
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

log_info "Root:         $ROOT_DIR"
log_info "Backend port: $BACKEND_PORT"
log_info "Flutter:      $FLUTTER_DEVICE"

if $RUN_BACKEND; then start_backend; fi
if $RUN_MOBILE;  then start_mobile;  fi

# ── Keep alive — compatible with bash 3.2 (macOS default) ────────────────────
log_success "All services running. Press Ctrl+C to stop."
wait
