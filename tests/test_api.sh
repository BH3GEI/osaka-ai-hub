#!/bin/bash
# Full API test suite for Osaka AI Hub
# Usage: bash tests/test_api.sh [BASE_URL]

BASE="${1:-http://154.17.17.154:18801}"
PASS=0
FAIL=0
TMPDIR=$(mktemp -d)

check() {
    local name="$1" expected_code="$2" actual_code="$3"
    if [ "$actual_code" = "$expected_code" ]; then
        echo "  ✓ $name (HTTP $actual_code)"
        PASS=$((PASS+1))
    else
        echo "  ✗ $name (expected $expected_code, got $actual_code)"
        FAIL=$((FAIL+1))
    fi
}

echo "=== Osaka AI Hub Test Suite ==="
echo "Target: $BASE"
echo ""

# 1. Health
echo "[1] GET /health"
CODE=$(curl -s -o "$TMPDIR/health.json" -w "%{http_code}" "$BASE/health")
check "health returns 200" "200" "$CODE"

# 2. Services
echo "[2] GET /api/services"
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/services")
check "services returns 200" "200" "$CODE"

# 3. Chat
echo "[3] POST /api/chat"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/chat" -F "message=Say hi in 3 words")
check "chat normal" "200" "$CODE"

echo "[4] POST /api/chat (missing field)"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/chat")
check "chat missing field" "422" "$CODE"

# 5. TTS
echo "[5] POST /api/tts"
CODE=$(curl -s -o "$TMPDIR/tts.wav" -w "%{http_code}" -X POST "$BASE/api/tts" -F "text=Hello")
check "tts normal" "200" "$CODE"
file "$TMPDIR/tts.wav" | grep -q "WAVE audio" && check "tts is valid WAV" "yes" "yes" || check "tts is valid WAV" "yes" "no"

# 6. Generate (sadtalker)
echo "[6] POST /api/generate (sadtalker)"
CODE=$(curl -s -o "$TMPDIR/sad.mp4" -w "%{http_code}" --max-time 60 -X POST "$BASE/api/generate" -F "text=Test" -F "engine=sadtalker")
check "generate sadtalker" "200" "$CODE"
file "$TMPDIR/sad.mp4" | grep -q "MP4\|ISO Media" && check "sadtalker is valid MP4" "yes" "yes" || check "sadtalker is valid MP4" "yes" "no"

# 7. Generate (musetalk)
echo "[7] POST /api/generate (musetalk)"
CODE=$(curl -s -o "$TMPDIR/muse.mp4" -w "%{http_code}" --max-time 300 -X POST "$BASE/api/generate" -F "text=Test" -F "engine=musetalk")
check "generate musetalk" "200" "$CODE"

# 8. Talk (full pipeline)
echo "[8] POST /api/talk"
CODE=$(curl -s -o "$TMPDIR/talk.mp4" -w "%{http_code}" --max-time 120 -X POST "$BASE/api/talk" -F "message=Say hello" -F "engine=sadtalker")
check "talk pipeline" "200" "$CODE"

# 9. Edge cases
echo "[9] Edge: no input"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/generate" -F "engine=sadtalker")
check "no input returns 400" "400" "$CODE"

echo "[10] Edge: invalid engine"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/generate" -F "text=hi" -F "engine=fake")
check "invalid engine returns 400" "400" "$CODE"

echo "[11] Edge: missing required"
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/api/tts")
check "tts missing text returns 422" "422" "$CODE"

# Summary
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
rm -rf "$TMPDIR"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
