#!/usr/bin/env bash
# Pull the images for a dev/compose.yaml profile (with retry) then bring it up.
#
# Docker Hub pulls occasionally time out fetching an auth token or manifest
# (context deadline exceeded), and a brief rate-limit shows up the same way.
# Retrying the network-bound pull before starting containers keeps a transient
# registry hiccup from failing CI. `up --wait` then starts from images that are
# already local.
#
# Single source of truth for both callers: the compose-up composite action and
# the crash-test discovery loop (see .github/workflows/pr-tests.yml).
set -euo pipefail

profile="$1"

for attempt in 1 2 3; do
  docker compose -f dev/compose.yaml --profile "$profile" pull && break
  echo "pull attempt $attempt failed; retrying in $((attempt * 10))s"
  sleep $((attempt * 10))
done

docker compose -f dev/compose.yaml --profile "$profile" up -d --wait
