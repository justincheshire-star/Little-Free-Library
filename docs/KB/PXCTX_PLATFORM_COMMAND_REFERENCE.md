# pxctx Platform Command Reference

**Purpose**: Cross-platform command guide for Professor X Context System (pxctx) operations  
**Audience**: Developers, AI agents, SOP executors  
**Platforms**: Windows (PowerShell), Linux/macOS (Bash), VS Code Codespaces  
**Last Updated**: February 10, 2026

---

## 📋 Quick Reference

| Operation    | Linux/Bash                                                | Windows PowerShell                                        |
| ------------ | --------------------------------------------------------- | --------------------------------------------------------- |
| Stats        | `./pxctx stats`                                           | `.\pxctx stats`                                           |
| Query        | `./pxctx query "text"`                                    | `.\pxctx query "text"`                                    |
| Add single   | `cd docs/KB && python -m Vector_RAG.pxctx add ...`        | `cd docs\KB; python -m Vector_RAG.pxctx add ...`          |
| Batch ingest | See [Session Review Ingestion](#session-review-ingestion) | See [Session Review Ingestion](#session-review-ingestion) |

---

## 🎯 Common Operations

### Check System Stats

**Linux/Bash/Codespaces**:

```bash
# From workspace root
./pxctx stats

# Or from docs/KB
cd docs/KB
python -m Vector_RAG.pxctx stats
```

**Windows PowerShell**:

```powershell
# From workspace root
.\pxctx stats

# Or from docs\KB
cd docs\KB
python -m Vector_RAG.pxctx stats
```

**Expected Output**:

```
Professor X Context System Stats

Schema version: 1.0
Created: 2026-02-06 05:20:48

Total documents: 150
Total chunks: 1062

Tier Breakdown:
  LONG_LIVED: 127 docs (15 pinned)
  TREASURE: 6 docs (6 pinned)
  WORKING: 17 docs (0 pinned)
```

---

### Query Context

**Linux/Bash/Codespaces**:

```bash
# Basic query
./pxctx query "your search terms" --final-n 5

# With JSON output (for parsing)
./pxctx query "search terms" --final-n 5 --json-output

# Avoid hyphenated terms (FTS5 parsing issue)
# ❌ BAD: ./pxctx query "B-011 blocker"
# ✅ GOOD: ./pxctx query "blocker resolution february"
```

**Windows PowerShell**:

```powershell
# Basic query
.\pxctx query "your search terms" --final-n 5

# With JSON output
.\pxctx query "search terms" --final-n 5 --json-output

# Use quotes for multi-word queries
.\pxctx query "model download blocker" --final-n 3
```

**Performance Note**: Query latency ~1-3 seconds (embedding model load + hybrid search)

---

### Add Single Document

**Linux/Bash/Codespaces**:

```bash
cd docs/KB

python -m Vector_RAG.pxctx add \
  --tier long_lived \
  --type kb_doc \
  --title "Document Title" \
  --file "../../path/to/file.md" \
  --repo "LocalAgents" \
  --tags "tag1,tag2" \
  --source-kind file \
  --source-ref "path/to/file.md" \
  --importance 0.7 \
  --ttl-days 180
```

**Windows PowerShell**:

```powershell
cd docs\KB

python -m Vector_RAG.pxctx add `
  --tier long_lived `
  --type kb_doc `
  --title "Document Title" `
  --file "..\..\path\to\file.md" `
  --repo "LocalAgents" `
  --tags "tag1,tag2" `
  --source-kind file `
  --source-ref "path/to/file.md" `
  --importance 0.7 `
  --ttl-days 180
```

**Note**: Use backtick `` ` `` for line continuation in PowerShell, backslash `\` in Bash.

**Performance Warning**:

- **Embedding time**: ~5-15 seconds per document (depends on chunk count)
- **CPU-bound**: ONNX embedding model is CPU-intensive
- **Codespaces**: Limited CPU, may take 2-3x longer than Windows
- See [Async Ingestion](#async-ingestion) for non-blocking approaches

---

## 📚 Session Review Ingestion

### Single Session (Manual)

**Linux/Bash/Codespaces**:

```bash
cd docs/KB

python -m Vector_RAG.pxctx add \
  --tier long_lived \
  --type kb_doc \
  --title "Session: SESSION_SUMMARY_FEB09_2026" \
  --file "../../docs/session-reviews/2026/02-february/SESSION_SUMMARY_FEB09_2026.md" \
  --repo "LocalAgents" \
  --tags "session,review,2026,february" \
  --source-kind file \
  --source-ref "docs/session-reviews/2026/02-february/SESSION_SUMMARY_FEB09_2026.md" \
  --importance 0.7 \
  --ttl-days 180
```

**Windows PowerShell**:

```powershell
cd docs\KB

python -m Vector_RAG.pxctx add `
  --tier long_lived `
  --type kb_doc `
  --title "Session: SESSION_SUMMARY_FEB09_2026" `
  --file "..\..\docs\session-reviews\2026\02-february\SESSION_SUMMARY_FEB09_2026.md" `
  --repo "LocalAgents" `
  --tags "session,review,2026,february" `
  --source-kind file `
  --source-ref "docs/session-reviews/2026/02-february/SESSION_SUMMARY_FEB09_2026.md" `
  --importance 0.7 `
  --ttl-days 180
```

---

### Batch Ingestion from INDEX.md

**Linux/Bash/Codespaces** (Last 3 sessions):

```bash
indexPath="docs/session-reviews/INDEX.md"
sessionReviews=$(grep -oP '\[SESSION (SUMMARY|REVIEW).+?\]\(\K[^)]+' "$indexPath" | head -n 3)

cd docs/KB
while IFS= read -r relPath; do
  fullPath="../../docs/session-reviews/$relPath"
  normalizedRef="docs/session-reviews/$relPath"
  basename=$(basename "$relPath" .md)
  title="Session: $basename"

  echo "Ingesting: $basename"
  python -m Vector_RAG.pxctx add \
    --tier long_lived \
    --type kb_doc \
    --title "$title" \
    --file "$fullPath" \
    --repo "LocalAgents" \
    --tags "session,review" \
    --source-kind file \
    --source-ref "$normalizedRef" \
    --importance 0.7 \
    --ttl-days 180
done <<< "$sessionReviews"
```

**Windows PowerShell** (Last 3 sessions):

```powershell
$indexPath = "docs\session-reviews\INDEX.md"
$sessionReviews = Get-Content $indexPath |
  Select-String -Pattern "\[SESSION (SUMMARY|REVIEW).+?\]\((.+?)\)" |
  ForEach-Object { $_.Matches.Groups[2].Value } |
  Select-Object -First 3

Write-Host "Found $($sessionReviews.Count) session reviews to ingest"

cd docs\KB
foreach ($relPath in $sessionReviews) {
  $fullPath = "..\..\docs\session-reviews\$relPath"
  $normalizedRef = "docs/session-reviews/$relPath" -replace "\\", "/"
  $basename = [System.IO.Path]::GetFileNameWithoutExtension($relPath)
  $title = "Session: $basename"

  Write-Host "Ingesting: $basename"
  python -m Vector_RAG.pxctx add `
    --tier long_lived `
    --type kb_doc `
    --title "$title" `
    --file "$fullPath" `
    --repo "LocalAgents" `
    --tags "session,review" `
    --source-kind file `
    --source-ref "$normalizedRef" `
    --importance 0.7 `
    --ttl-days 180
}
cd ..\..
```

---

### Async Ingestion (Recommended)

**Linux/Bash/Codespaces:**

```bash
# Start async ingestion (3 sessions, default)
./scripts/ingest-sessions-async.sh

# Check status
./scripts/check-ingestion-status.sh

# Ingest 5 sessions with wait
./scripts/ingest-sessions-async.sh -n 5 -w

# Sync mode (blocking, for compatibility)
./scripts/ingest-sessions-async.sh -n 3 -s
```

**Windows/PowerShell** (async with Start-Job):

```powershell
# Start async ingestion job
$job = Start-Job -ScriptBlock {
    cd $using:PWD/docs/KB
    python -m Vector_RAG.pxctx add --tier long_lived --type kb_doc `
        --title "Session: FEB09" `
        --file "..\..\docs\session-reviews\2026\02-february\SESSION_SUMMARY_FEB09_2026.md" `
        --repo "LocalAgents" --tags "session,review" `
        --source-kind file --source-ref "docs/session-reviews/2026/02-february/SESSION_SUMMARY_FEB09_2026.md" `
        --importance 0.7 --ttl-days 180 --on-duplicate update
}

# Check job status (non-blocking)
$job | Receive-Job -Keep

# Wait for completion and get output
$job | Wait-Job | Receive-Job
$job | Remove-Job
```

**Features:**

- ✅ **Idempotent**: Uses `--on-duplicate update` to skip unchanged content (hash-based)
- ✅ **Progress indicators**: Shows embedding progress with model info, chunk counts, and tqdm progress bar
- ✅ **Async execution**: Non-blocking with PID tracking and log output (`ingestion.log`)
- ✅ **Status checking**: Monitor progress with `./scripts/check-ingestion-status.sh` or `tail -f docs/KB/ingestion.log`

**Performance:**

- Embedding phase: 5-15 seconds per session in Codespaces (CPU-bound, ONNX)
- Idempotent check: <1 second for unchanged content (content_hash comparison)
- 3 sessions (all already current): ~1 second total with idempotent skipping

**Exit Codes:**

- `0`: All sessions ingested or skipped successfully
- `1`: One or more sessions failed to ingest

**Script Details:**

- Location: `scripts/ingest-sessions-async.sh`, `scripts/check-ingestion-status.sh`
- Log file: `docs/KB/ingestion.log`
- PID file: `docs/KB/ingestion.pid`

**Performance**:

- **3 sessions**: ~45-60 seconds (Codespaces), ~20-30 seconds (Windows)
- **Blocking**: These commands run synchronously
- **See**: [Async Ingestion](#async-ingestion) for background execution

---

## ⚡ Async Ingestion

### Background Execution (Linux/Codespaces)

```bash
# Run ingestion in background, redirect output to log
cd docs/KB
{
  python -m Vector_RAG.pxctx add \
    --tier long_lived \
    --type kb_doc \
    --title "Session: SESSION_SUMMARY_FEB09_2026" \
    --file "../../docs/session-reviews/2026/02-february/SESSION_SUMMARY_FEB09_2026.md" \
    --repo "LocalAgents" \
    --tags "session,review" \
    --source-kind file \
    --source-ref "docs/session-reviews/2026/02-february/SESSION_SUMMARY_FEB09_2026.md" \
    --importance 0.7 \
    --ttl-days 180
} > ingestion.log 2>&1 &

INGESTION_PID=$!
echo "Ingestion running in background (PID: $INGESTION_PID)"
echo "Monitor: tail -f docs/KB/ingestion.log"
echo "Check status: ps -p $INGESTION_PID"
```

### Background Execution (Windows PowerShell)

```powershell
# Start ingestion as background job
cd docs\KB
$job = Start-Job -ScriptBlock {
  Set-Location $using:PWD
  python -m Vector_RAG.pxctx add `
    --tier long_lived `
    --type kb_doc `
    --title "Session: SESSION_SUMMARY_FEB09_2026" `
    --file "..\..\docs\session-reviews\2026\02-february\SESSION_SUMMARY_FEB09_2026.md" `
    --repo "LocalAgents" `
    --tags "session,review" `
    --source-kind file `
    --source-ref "docs/session-reviews/2026/02-february/SESSION_SUMMARY_FEB09_2026.md" `
    --importance 0.7 `
    --ttl-days 180
}

Write-Host "Ingestion running in background (Job: $($job.Id))"
Write-Host "Check status: Get-Job -Id $($job.Id)"
Write-Host "Wait for completion: Wait-Job -Id $($job.Id)"
Write-Host "Get results: Receive-Job -Id $($job.Id)"
```

### Check Completion (Polling)

**Linux/Bash**:

```bash
# Check if background process completed
if ps -p $INGESTION_PID > /dev/null; then
  echo "Still running..."
else
  echo "✅ Ingestion complete"
  cat docs/KB/ingestion.log | tail -n 10
fi
```

**Windows PowerShell**:

```powershell
# Check job status
$job = Get-Job -Id $jobId
if ($job.State -eq "Completed") {
  Write-Host "✅ Ingestion complete"
  Receive-Job -Id $jobId
} elseif ($job.State -eq "Running") {
  Write-Host "Still running..."
} else {
  Write-Host "⚠️ Job state: $($job.State)"
}
```

---

## 🔧 Maintenance Operations

### Telemetry Cleanup

**Linux/Bash**:

```bash
cd docs/KB

# Dry run (see what would be deleted)
python -m Vector_RAG.pxctx telemetry-gc --days 30 --dry-run

# Actually delete old telemetry
python -m Vector_RAG.pxctx telemetry-gc --days 30 --force
```

**Windows PowerShell**:

```powershell
cd docs\KB

# Dry run
python -m Vector_RAG.pxctx telemetry-gc --days 30 --dry-run

# Execute
python -m Vector_RAG.pxctx telemetry-gc --days 30 --force
```

---

### Manual Deduplication

**Linux/Bash**:

```bash
cd docs/KB

python3 << 'EOF'
import sqlite3

conn = sqlite3.connect('Vector_RAG/pxctx.db')

# Find duplicates by title
cursor = conn.execute('''
    SELECT title, COUNT(*) as count
    FROM docs
    GROUP BY title
    HAVING count > 1
''')

for row in cursor:
    print(f'{row[0]}: {row[1]} duplicates')

conn.close()
EOF
```

**Windows PowerShell**:

```powershell
cd docs\KB

python -c @"
import sqlite3
conn = sqlite3.connect('Vector_RAG/pxctx.db')
cursor = conn.execute('''
    SELECT title, COUNT(*) as count
    FROM docs
    GROUP BY title
    HAVING count > 1
''')
for row in cursor:
    print(f'{row[0]}: {row[1]} duplicates')
conn.close()
"@
```

---

## 🐛 Troubleshooting

### Common Issues

#### FTS5 Query Parsing Error: "no such column: 011"

**Problem**: Hyphenated terms (e.g., "B-011") cause FTS5 to interpret as column reference.

**Solution**: Avoid hyphens in queries

```bash
# ❌ BAD
./pxctx query "B-011 blocker"

# ✅ GOOD
./pxctx query "blocker resolution february"
./pxctx query "download scheduler issue"
```

#### Embedding Takes Too Long (Codespaces)

**Problem**: CPU-bound ONNX embedding is slow in resource-constrained environments.

**Solutions**:

1. Use background execution (see [Async Ingestion](#async-ingestion))
2. Reduce ingestion frequency (2-3 sessions instead of 5-7)
3. Run expensive ingestions on Windows host if available
4. Monitor with `top` or Task Manager to avoid overloading

```bash
# Monitor CPU during ingestion
top -p $(pgrep -f "Vector_RAG.pxctx")
```

#### ImportError: No module named 'onnxruntime'

**Problem**: ONNX Runtime not installed.

**Solution**:

```bash
pip install onnxruntime
```

---

## 📖 Related Documentation

- [PXCTX_HYBRID_RETRIEVAL_SYSTEM.md](PXCTX_HYBRID_RETRIEVAL_SYSTEM.md) - System architecture
- [SESSION_REVIEW_SOP.md](../sop/SESSION_REVIEW_SOP.md) - Phase 6 ingestion procedure
- [RAG_PIPELINE_SOP.md](../sop/RAG_PIPELINE_SOP.md) - RAG operations
- [PXCTX_AUTOMATION.md](../planning/PXCTX_AUTOMATION.md) - Automation scripts (Phases 1-4)

---

## 📊 Performance Benchmarks

| Operation             | Codespaces | Windows (8-core) | Notes               |
| --------------------- | ---------- | ---------------- | ------------------- |
| Query (5 results)     | 1-2s       | 0.5-1s           | Includes model load |
| Add 1 doc (10 chunks) | 15-20s     | 5-8s             | ONNX embedding      |
| Add 1 doc (50 chunks) | 60-90s     | 20-30s           | CPU-bound           |
| Batch 3 sessions      | 45-75s     | 20-35s           | Sequential          |
| Stats check           | <0.1s      | <0.1s            | SQLite query only   |

**CPU Utilization**: 100% single-core during embedding (ONNX is single-threaded)

---

## 🔑 Key Principles

1. **Path Normalization**: Always use forward slashes in `source-ref` (repo-relative, cross-platform)
2. **Idempotency**: Not yet implemented - re-ingestion creates duplicates (manual dedupe required)
3. **Async-First**: Use background execution for ingestions during session reviews
4. **Bounded Ingestion**: 2-3 sessions default, max 5-7 for multi-day work
5. **Query Hygiene**: Avoid hyphens, use descriptive natural language
6. **Platform Awareness**: Codespaces has limited CPU; Windows has overhead

---

**Last Updated**: February 10, 2026  
**Maintained By**: Professor X Mode  
**Feedback**: Update this doc when new patterns emerge or issues are resolved
