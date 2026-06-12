#!/bin/sh
set -eu

APP_DIR="${APP_DIR:-$HOME/oh-my-rss}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "$APP_DIR"
"$PYTHON_BIN" -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -e .
mkdir -p state site

if [ ! -f config.yaml ]; then
  oh-my-rss init-config --output config.yaml
  echo "Created config.yaml. Edit it before enabling a schedule."
fi

CRON_LINE="$(oh-my-rss print-cron \
  --cwd "$APP_DIR" \
  --config config.yaml \
  --limit 1 \
  --interval-minutes 10 \
  --log-path state/cron.log \
  --venv .venv)"

cat <<MSG
Install complete.

Example cron line:
$CRON_LINE
MSG
