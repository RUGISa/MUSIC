#!/bin/bash
set -u
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3 is required. Install Python 3 and reopen this file.'
  read -r -p 'Press Return to close: ' _
  exit 1
fi
python3 manager.py
code=$?
if [ "$code" -ne 0 ]; then
  echo 'FREQUENCY failed. Logs: ~/Library/Application Support/FREQUENCY/'
  read -r -p 'Press Return to close: ' _
fi
exit "$code"
