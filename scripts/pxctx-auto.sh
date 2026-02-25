#!/usr/bin/env bash
# pxctx-auto.sh — Professor X session bootstrap helpers
#
# Source this file at the start of a Professor X session:
#   source scripts/pxctx-auto.sh
#
# Then call:
#   pxctx-boot "Task description"
#
# Functions provided:
#   pxctx-boot   <description>  — start a new session
#   pxctx-resume <session_id>   — resume an existing session
#   pxctx-context <query>       — query context and print summary
#   pxctx-record <type> <text>  — record a finding/decision/etc.
#   pxctx-checkpoint <message>  — record a milestone
#   pxctx-verify                — verify findings were stored
#   pxctx-wrap-up               — end-of-session cleanup

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve paths
# ---------------------------------------------------------------------------
_PXCTX_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PXCTX_ROOT="${PXCTX_ROOT:-$(dirname "$_PXCTX_SCRIPT_DIR")}"
_PXCTX_CLI="${_PXCTX_SCRIPT_DIR}/pxctx"

_pxctx() {
    python3 "$_PXCTX_CLI" "$@"
}

# ---------------------------------------------------------------------------
# pxctx-boot — start a new session
# ---------------------------------------------------------------------------
pxctx-boot() {
    local description="${1:-Unnamed session}"

    echo "[pxctx-boot] Bootstrapping session: $description"

    # Check health (DB initialises on first use)
    if ! python3 "$_PXCTX_CLI" status > /dev/null 2>&1; then
        echo "[pxctx-boot] WARNING: pxctx CLI unavailable — continuing without context system."
        return 1
    fi

    # Create session
    local session_json
    session_json=$(_pxctx session-new "$description")

    export PXCTX_SESSION_ID
    PXCTX_SESSION_ID=$(echo "$session_json" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")

    export PXCTX_TASK_ID
    PXCTX_TASK_ID=$(echo "$session_json" | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")

    export PXCTX_REPO_ID
    PXCTX_REPO_ID=$(echo "$session_json" | python3 -c "import sys,json; print(json.load(sys.stdin)['repo_id'])")

    echo "[pxctx-boot] session_id=$PXCTX_SESSION_ID  task_id=$PXCTX_TASK_ID  repo_id=$PXCTX_REPO_ID"

    # Index KB files if not yet done
    _pxctx-index-kb 2>/dev/null || true

    # Prime context query
    echo "[pxctx-boot] Priming context for: $description"
    _pxctx query "$description" --budget 2000 2>/dev/null | \
        python3 -c "
import sys, json
data = json.load(sys.stdin)
final = data.get('final', [])
print(f'[pxctx-boot] Context primed: {len(final)} items ({data[\"stats\"][\"budget_used_chars\"]} chars)')
for item in final[:5]:
    print(f'  [{item[\"tier\"]}] {item[\"id\"]}: {item[\"snippet\"][:80]}')
" 2>/dev/null || true

    echo "[pxctx-boot] Ready."
}

# ---------------------------------------------------------------------------
# pxctx-resume — resume an existing session
# ---------------------------------------------------------------------------
pxctx-resume() {
    local session_id="${1:-}"
    if [[ -z "$session_id" ]]; then
        echo "[pxctx-resume] ERROR: provide session_id" >&2
        return 1
    fi

    export PXCTX_SESSION_ID="$session_id"
    echo "[pxctx-resume] Resumed session: $PXCTX_SESSION_ID"

    _pxctx query "" --budget 1500 2>/dev/null | \
        python3 -c "
import sys, json
data = json.load(sys.stdin)
final = data.get('final', [])
print(f'[pxctx-resume] {len(final)} context items loaded.')
" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# pxctx-context — query context and print a human-readable summary
# ---------------------------------------------------------------------------
pxctx-context() {
    local query="${1:-}"
    local budget="${2:-4000}"

    echo "[pxctx] Querying context: \"$query\""
    _pxctx query "$query" --budget "$budget" | \
        python3 -c "
import sys, json
data = json.load(sys.stdin)
packs = data.get('packs', {})
for tier in ('treasure', 'working', 'long_lived'):
    items = packs.get(tier, [])
    if items:
        label = tier.replace('_', '-')
        print(f'  [{label}] {len(items)} item(s):')
        for it in items:
            print(f'    • {it[\"id\"]} [{it[\"type\"]}]: {it[\"snippet\"][:100]}')
stats = data.get('stats', {})
print(f'  stats: {stats}')
" 2>&1
}

# ---------------------------------------------------------------------------
# pxctx-record — quick record of a finding/decision/etc.
#
# Usage:  pxctx-record <type> <text>
# Types:  decision | finding | constraint | command_summary | architecture | note
# ---------------------------------------------------------------------------
pxctx-record() {
    local rec_type="${1:-note}"
    local text="${2:-}"
    local ttl="${3:-7}"   # default 7-day TTL for working items

    if [[ -z "$text" ]]; then
        echo "[pxctx-record] ERROR: provide text" >&2
        return 1
    fi

    local result
    result=$(_pxctx add \
        --tier working \
        --type "$rec_type" \
        --text "$text" \
        --scope session \
        --ttl-days "$ttl" 2>/dev/null)

    local doc_id
    doc_id=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id','?'))" 2>/dev/null || echo "?")
    echo "[pxctx] Recorded [$rec_type] → $doc_id"
}

# ---------------------------------------------------------------------------
# pxctx-checkpoint — record a milestone as a verified finding
# ---------------------------------------------------------------------------
pxctx-checkpoint() {
    local message="${1:-}"
    if [[ -z "$message" ]]; then
        echo "[pxctx-checkpoint] ERROR: provide message" >&2
        return 1
    fi

    local result
    result=$(_pxctx add \
        --tier working \
        --type checkpoint \
        --text "$message" \
        --tags checkpoint milestone \
        --scope session \
        --ttl-days 30 2>/dev/null)

    local doc_id
    doc_id=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id','?'))" 2>/dev/null || echo "?")
    echo "[pxctx] Checkpoint → $doc_id: $message"
}

# ---------------------------------------------------------------------------
# pxctx-verify — print a summary of what was stored this session
# ---------------------------------------------------------------------------
pxctx-verify() {
    echo "[pxctx-verify] Session: ${PXCTX_SESSION_ID:-<unset>}"
    if [[ -z "${PXCTX_SESSION_ID:-}" ]]; then
        echo "[pxctx-verify] No active session." >&2
        return 1
    fi

    _pxctx list --tier working --session "$PXCTX_SESSION_ID" | \
        python3 -c "
import sys, json
items = json.load(sys.stdin)
print(f'[pxctx-verify] {len(items)} working item(s) stored this session:')
for it in items:
    print(f'  {it[\"id\"]} [{it[\"type\"]}]: {(it.get(\"summary\") or \"\")[:80]}')
" 2>&1
}

# ---------------------------------------------------------------------------
# pxctx-wrap-up — end-of-session: verify, gc, stats
# ---------------------------------------------------------------------------
pxctx-wrap-up() {
    echo "[pxctx-wrap-up] Wrapping session ${PXCTX_SESSION_ID:-<unset>} ..."

    pxctx-verify || true

    echo "[pxctx-wrap-up] Running GC (dry-run) ..."
    _pxctx gc --dry-run 2>/dev/null | \
        python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'  Would delete {len(data.get(\"would_delete\", []))} expired item(s).')
" 2>/dev/null || true

    echo "[pxctx-wrap-up] Store stats:"
    _pxctx status 2>/dev/null | \
        python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'  docs_by_tier: {data.get(\"docs_by_tier\", {})}')
" 2>/dev/null || true

    if [[ -n "${PXCTX_SESSION_ID:-}" ]]; then
        _pxctx session-update --session-id "$PXCTX_SESSION_ID" --state wrapped 2>/dev/null || true
    fi

    echo "[pxctx-wrap-up] Done."
}

# ---------------------------------------------------------------------------
# _pxctx-index-kb — ingest KB markdown files as long-lived docs (idempotent)
# ---------------------------------------------------------------------------
_pxctx-index-kb() {
    local kb_dir="${PXCTX_ROOT}/docs/KB"
    if [[ ! -d "$kb_dir" ]]; then
        return 0
    fi

    local count=0
    while IFS= read -r -d '' f; do
        local basename
        basename="$(basename "$f")"
        # Skip README and treasure README
        [[ "$basename" == "README.md" ]] && continue

        _pxctx add \
            --tier long-lived \
            --type kb-note \
            --file "$f" \
            --never-expire \
            --tags kb \
            --sources "$f" \
            2>/dev/null || true
        (( count++ )) || true
    done < <(find "$kb_dir" -name "*.md" -print0 2>/dev/null)

    [[ $count -gt 0 ]] && echo "[pxctx] Indexed $count KB file(s) as long-lived context." || true
}

# ---------------------------------------------------------------------------
# Convenience: export _pxctx so subshells can use it
# ---------------------------------------------------------------------------
export -f _pxctx 2>/dev/null || true
