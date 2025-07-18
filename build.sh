#!/usr/bin/env bash

# Update and install Chromium
apt-get update && apt-get install -y chromium

# Optional: Confirm install (for debug)
which chromium || which chromium-browser || which google-chrome