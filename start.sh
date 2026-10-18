#!/usr/bin/env bash
# Quick starter script for Lanacord Grammys Fake Betting Platform

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

PORT=${1:-8080}

echo "=========================================================="
echo "✨ 🏆  LANACORD GRAMMYS 2026 - BETTING GALA  🏆 ✨"
echo "=========================================================="
echo "👑 Voter Platform : http://localhost:${PORT}/"
echo "🛡️  Admin Suite    : http://localhost:${PORT}/admin"
echo "=========================================================="
echo "Press Ctrl+C to stop the server."
echo ""

/usr/bin/python3 server.py "$PORT"
