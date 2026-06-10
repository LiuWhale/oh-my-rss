#!/bin/sh
set -eu

APP_DIR="${APP_DIR:-$HOME/oh-my-rss}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$APP_DIR"
"$PYTHON_BIN" -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e .

if [ ! -f config.yaml ]; then
  oh-my-rss init-config --output config.yaml
  echo "Created config.yaml. Edit it before enabling a schedule."
fi

cat <<MSG
Install complete.

Example cron line:
*/10 * * * * cd "$APP_DIR" && . .venv/bin/activate && oh-my-rss run --config config.yaml --limit 1 >> state/cron.log 2>&1
MSG
