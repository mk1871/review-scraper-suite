#!/bin/bash
# start_chrome.sh
echo "🚀 Iniciando Chrome en modo debug..."
google-chrome-stable \
  --user-data-dir=/home/k0b4/.config/google-chrome \
  --profile-directory=Default \
  --remote-debugging-port=9222 \
  --remote-debugging-address=0.0.0.0 \
  --no-first-run \
  --no-default-browser-check \
  about:blank
