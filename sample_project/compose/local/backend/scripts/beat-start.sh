#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

echo "Running Beat now..."

exec celery -A config.celery beat --loglevel=info
