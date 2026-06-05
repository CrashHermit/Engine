#!/bin/bash
# Install dev dependencies (ruff, pytest) so linting and tests work in
# Claude Code on the web sessions. Keeps agent-authored branches conforming
# to the formatter before they reach CI.
set -euo pipefail

# Only run in the remote (web) environment; local sessions manage their own venv.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"
uv sync --group dev
