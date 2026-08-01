#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_DIR="$(git rev-parse --git-dir)/hooks"

ln -sf "$SCRIPT_DIR/post-merge" "$HOOK_DIR/post-merge"
chmod +x "$SCRIPT_DIR/post-merge"

echo "Hook installed: post-merge → $HOOK_DIR/post-merge"
