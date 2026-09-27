#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

echo "Running npm containers..."

npm run dev -- --host
