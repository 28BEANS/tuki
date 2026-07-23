#!/usr/bin/env bash
# Convenience runner pointing to scripts/dev.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/scripts/dev.sh" "$@"
