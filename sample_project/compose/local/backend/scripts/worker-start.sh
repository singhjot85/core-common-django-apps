#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

ENABLE_DEBUGPY=${ENABLE_DEBUGPY:-0}

echo "Running Worker now..."

if [ "$ENABLE_DEBUGPY" = "1" ]; then
    echo "Starting Celery Worker with debugpy and watchmedo auto-reload..."
    exec watchmedo auto-restart \
        --directory=apps \
        --directory=config \
        --directory=utils \
        --pattern="*.py" \
        --recursive -- \
        python -m debugpy --listen 0.0.0.0:5678 -m \
        celery -A config.celery worker --loglevel=info --concurrency=1 \
        # -P solo  # Let's see if vscode can catch multiple threads, if it can't we can uncomment this
else
    echo "Starting Celery Worker with watchmedo auto-reload..."
    exec watchmedo auto-restart \
        --directory=apps \
        --directory=config \
        --directory=utils \
        --pattern="*.py" \
        --recursive -- \
        celery -A config.celery worker --loglevel=info --concurrency=4
fi
