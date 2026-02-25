Agnostic Hybrid Retrieval

### Gothi — Record

```text
event_id: E20260209-0001
summary: User requests an evaluation of attached docs to produce a stack-agnostic system description of a hybrid retrieval system for AI IDE agents.
observations:
- User wants an evaluation and analysis of the attached documents.
- User wants a project- and stack-agnostic system description.
- The target audience is AI IDE agents that must adapt the system to any system.
entities:
- name: pxctx hybrid retrieval system; type: project
- name: AI IDE agents; type: concept
- name: hybrid retrieval; type: concept
constraints:
- project agnostic
- stack agnostic
- usable by AI IDE agents to adapt to any system
tasks_requested:
- evaluate and analyze the attached documents
- build a system description of the hybrid retrieval system suitable for adaptation
tags:
- topic:retrieval
- topic:agents
confidence: high
```

### Gothi — Recall

```text
recall_query: key contracts and invariants for a 3-tier hybrid retrieval+ingestion system usable by IDE agents
filters: time_range=all; tags=topic:retrieval,topic:agents
k: 6
results:
- id: F000001; kind: fact; snippet: 3-tier model (Treasure/Working/Long-lived) with hard tier dominance + deterministic ranking.; provenance: PXCTX_HYBRID_RETRIEVAL_SYSTEM.md; score: 0.93
- id: F000002; kind: fact; snippet: Hybrid retrieval per tier uses FTS (BM25) + vector similarity, then deterministic scoring/rerank.; provenance: PXCTX_HYBRID_RETRIEVAL_SYSTEM.md; score: 0.91
- id: F000003; kind: fact; snippet: Deterministic score = tier_boost + 2*vec + 1*fts + recency_boost*R + importance + verified + path + pin.; provenance: PXCTX_HYBRID_RETRIEVAL_SYSTEM.md; score: 0.89
- id: F000004; kind: fact; snippet: Context packing is Treasure-first with reserved token budget (e.g., 25%); dedupe by chunk_id.; provenance: PXCTX_HYBRID_RETRIEVAL_SYSTEM.md; score: 0.87
- id: F000005; kind: fact; snippet: Data model includes docs, chunks, FTS index, vectors; metadata: tier/scope/tags/sources/verified/ttl/pin/supersedes/content_hash/redacted.; provenance: PXCTX_HYBRID_RETRIEVAL_SYSTEM.md; score: 0.86
- id: F000006; kind: fact; snippet: Agent-facing query contract returns packs by tier + final packed list + stats; includes repo/session/task/active_paths filters.; provenance: Documents_as_Context_With_Vectors.md; score: 0.84
```

### Gethli — Analyze

* **Supported claims**

  * The system is a 3-tier memory model with hard dominance: Treasure > Working > Long-lived. [IDs: F000001]
  * Retrieval is hybrid (lexical FTS/BM25 + vector similarity) and reranked deterministically within tiers. [IDs: F000002]
  * Scoring is a transparent additive formula including tier boosts, vector, FTS, recency, importance, verified, active_paths, and pin. [IDs: F000003]
  * Packing is Treasure-first with a reserved token budget and deduplication by chunk_id. [IDs: F000004]
  * The storage model separates docs, chunks, FTS index, and vectors; docs carry governance/lifecycle fields (ttl, supersedes, content_hash, redacted). [IDs: F000005]
  * A query/response contract can expose tier “packs” plus a final packed context list and stats, filtered by repo/session/task/active_paths. [IDs: F000006]
* **Assumptions**

  * A1: Target IDE agents can call the retrieval system through either a CLI, local library call, or HTTP API (adapter layer). (Test: confirm integration surface desired.)
* **Plan**

  1. Define a stack-agnostic reference architecture (components + responsibilities).
  2. Specify portable data contracts: Document, Chunk, RetrievalRequest/Response, Governance actions.
  3. Specify deterministic retrieval + scoring + packing algorithms (tiered).
  4. Provide an “adapter recipe” for IDE agents to map onto any DB/vector/FTS stack.

### Gethli — Answer

Below is a **project- and stack-agnostic specification** you can hand to AI IDE agents. It describes *what must be true* (contracts + invariants) while allowing any implementation choices (SQLite/Qdrant/Elastic/Postgres, local/remote embeddings, etc.). It is distilled from the attached pxctx technical documentation and the “Documents as Context” contract.  

---

## 1) System purpose and non-negotiable invariants

### Goal

Provide **deterministic, governance-aware context retrieval** for IDE agents by combining:

* **Lexical retrieval** (exact terms, symbols, errors) via full-text search (BM25-style).
* **Semantic retrieval** via vector similarity (cosine/dot). 

### Tier invariants (hard priority)

The memory corpus is partitioned into exactly three tiers:

1. **Treasure (Canonical / “always king”)**

   * Non-negotiable rules, invariants, architectural decisions.
   * Must dominate retrieval regardless of recency. 
2. **Working (Ephemeral / session-task memory)**

   * Short-lived findings, plans, command summaries; strongly recency-weighted. 
3. **Long-lived (Durable knowledge)**

   * KB docs + distilled learnings; mildly recency-weighted; boosted by verification/evidence. 

**Dominance rule:** the system MUST be able to guarantee Treasure outranks other tiers (either by staged packing or by tier boosts that overwhelm other signals). 

---

## 2) Reference architecture (stack-agnostic)

Implement as four replaceable modules:

1. **Ingestion**

   * Accepts documents/notes, assigns tier + metadata, chunks content, computes content_hash for idempotency, triggers vector indexing. 
2. **Indexing**

   * Maintains:

     * Full-text index over chunk text (BM25-like).
     * Vector index over chunk embeddings. 
3. **Retrieval**

   * Executes tier-staged hybrid retrieval and deterministic reranking. 
4. **Packing**

   * Produces a token-budgeted final context with Treasure-first reservation and dedupe. 

Any storage/search stack is acceptable if it can support:

* Store docs + chunks + metadata.
* Lexical search over chunks (or equivalent).
* Vector similarity over chunk embeddings.
* Deterministic sorting and filtering.

---

## 3) Canonical data contracts (portable)

### 3.1 Document (logical record)

Minimum required fields (names are suggestions; map as needed):

* `doc_id: string`
* `tier: "treasure" | "working" | "long_lived"`
* `title: string`
* `content: string`
* `type: "decision" | "constraint" | "finding" | "plan_step" | "command_summary" | "kb_doc" | "distilled_note" | "security_rule" | "architecture" | "invariant"` 
* `scope: { repo_id?: string, session_id?: string, task_id?: string }` 
* `tags: string[]`
* `sources: { kind: string, ref: string }[]`
* `importance: number (0..1)` (default 0.5) 
* `verified: "asserted" | "observed" | "tested" | "documented"` 
* lifecycle/governance:

  * `pin: boolean` (commonly true for Treasure) 
  * `never_expire: boolean`
  * `ttl_days?: number`
  * `supersedes?: string[]` (versioning chain) 
* integrity/safety:

  * `content_hash: string` (idempotent update detection) 
  * `redacted: boolean` 
* timestamps:

  * `created_at`, `updated_at`

### 3.2 Chunk (retrieval unit)

* `chunk_id: string`
* `doc_id: string`
* `chunk_index: number`
* `chunk_text: string`
* `token_count?: number`
* optional: `heading_path?: string` (useful for markdown chunk provenance)

### 3.3 Embedding record

* `chunk_id: string`
* `embedding: float[] | bytes`
* `embedding_model: string`
* `embedding_dim: number`

---

## 4) Agent-facing retrieval contract

### Request

An IDE agent should be able to call retrieval with:

* `q: string` (the current task/user request)
* `scope filters: repo_id?, session_id?, task_id?`
* `active_paths?: string[]` (boost chunks sourced from files under active work paths) 
* `limits: treasure_k, working_k, long_lived_k, final_n, max_tokens` 
* optional `filters: tags_any?, tiers?`

### Response

Return:

* `packs: { treasure: Hit[], working: Hit[], long_lived: Hit[] }`
* `final: PackedContextItem[]` (already token-budgeted and tier-ordered)
* `stats: { vector_calls, fts_calls, deduped, returned }` (optional) 

Where a `Hit` minimally includes:

* `doc_id, chunk_id, tier, score, title, snippet, tags, sources, updated_at` 

This mirrors the documented query contract style used for pxctx. 

---

## 5) Deterministic retrieval algorithm (tier-staged hybrid)

### Tier-staged flow

1. Compute query embedding once.
2. Retrieve **Treasure hits** (hybrid lexical + vector) → score deterministically → sort desc.
3. Retrieve **Working hits** filtered by session/task first → apply stronger recency.
4. Retrieve **Long-lived hits** filtered by repo → apply verified boost + mild recency.
5. Pack context Treasure-first with reserved token budget; then fill with best remaining.  

### Per-tier candidate scoring (deterministic)

Use an additive, transparent function:

`score = tier_boost + 2*vec + 1*fts + recency_boost*R + importance + verified + path_boost + pin_boost`

With:

* `tier_boost`: treasure 10, working 5, long_lived 2 (example) 
* `vec`: normalized semantic similarity 0..1
* `fts`: normalized lexical score 0..1 (BM25 ranks normalized) 
* `R`: recency score with decay (example: ~30-day decay curve) 
* `verified`: mapping (documented>tested>observed>asserted) 
* `path_boost`: e.g., +0.2 if any source ref matches an active_path 
* `pin_boost`: e.g., +0.5 if pinned 

**Implementation note for agents:** your backend may use different ranges; normalize vec/fts onto comparable 0..1 scales before applying weights.

---

## 6) Deterministic packing algorithm (token-budgeted, Treasure-first)

Packing MUST:

* Reserve a minimum Treasure token budget (documented example: 25%). 
* Add Treasure items first until the Treasure budget is met (or treasure_k/final_n limits).
* Merge Working + Long-lived, sort by score desc, fill remaining tokens.
* Dedupe by `chunk_id`. 

This is the key mechanism that ensures Treasure remains present even when the query is off-topic or the budget is tight. 

---

## 7) Governance and lifecycle (portable rules)

Minimum governance actions:

1. **Add**

   * default agent writes go to Working (findings/plans/command summaries). 
2. **Promote**

   * working → long_lived (compaction/distillation)
   * long_lived → treasure only by explicit promote action (human/policy gate) 
3. **Supersede**

   * when Treasure changes, create a new doc that `supersedes` old doc(s) (audit chain). 
4. **Expire / GC**

   * apply TTL for working (example default: 7 days) and optionally long-lived (example: 180 days). 
5. **Idempotent ingestion**

   * use `content_hash` and (optionally) `source` keys to avoid duplicating unchanged docs. 

---

## 8) “Adapter recipe” for AI IDE agents (how to port to any stack)

An IDE agent implementing this spec should do the following mapping steps:

1. **Choose stores**

   * Any document store for `Document` + `Chunk`.
   * Any lexical search that can return ranked chunk matches.
   * Any vector index that can return top-k nearest chunks.
2. **Implement the contracts**

   * Ensure every chunk is addressable by `(doc_id, chunk_id)` and can return `snippet + metadata`.
   * Ensure you can filter by scope fields and tier.
3. **Implement retrieval stages**

   * Run retrieval separately per tier (or simulate by filtering + tier-aware scoring).
4. **Implement deterministic scoring**

   * Normalize scores to stable ranges; apply the additive formula; no stochastic rerankers.
5. **Implement packing**

   * Enforce Treasure reservation and dedupe; output `final[]` as the only thing the LLM must consume by default, while exposing `packs` for debugging/telemetry.